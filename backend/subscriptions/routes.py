from flask import Blueprint, request, jsonify, g, current_app
from .models import db, Subscription, QuotaUsage, Invoice
from .plan_config import get_all_plans, get_plan_config
from .stripe_service import StripeService
from .quota_service import QuotaService
from datetime import datetime
from backend.auth.decorators import jwt_required

subscription_bp = Blueprint('subscriptions', __name__)

@subscription_bp.route('/plans', methods=['GET'])
def list_plans():
    """Available plans (public)"""
    return jsonify({"data": get_all_plans()})

@subscription_bp.route('/me', methods=['GET'])
@jwt_required
def get_my_subscription():
    """Current subscription status"""
    sub = QuotaService._ensure_subscription(g.current_user.id)
    return jsonify({
        "data": {
            "tier": sub.tier,
            "billing_cycle": sub.billing_cycle,
            "status": sub.status,
            "current_period_end": sub.current_period_end.isoformat() if sub.current_period_end else None,
            "minutes_used": sub.minutes_used,
            "monthly_minutes_limit": sub.monthly_minutes_limit
        }
    })

@subscription_bp.route('/checkout', methods=['POST'])
@jwt_required
def create_checkout():
    """Create Stripe Checkout Session"""
    data = request.json
    tier = data.get('tier')
    cycle = data.get('cycle', 'monthly')
    success_url = data.get('success_url')
    cancel_url = data.get('cancel_url')

    if not tier or not success_url or not cancel_url:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Missing required fields"}}), 400

    try:
        # Ensure customer exists
        sub = QuotaService._ensure_subscription(g.current_user.id)
        if not sub.stripe_customer_id:
            sub.stripe_customer_id = StripeService.create_customer(g.current_user)
            db.session.commit()

        url = StripeService.create_checkout_session(
            g.current_user.id, tier, cycle, success_url, cancel_url
        )
        return jsonify({"data": {"checkout_url": url}})
    except Exception as e:
        return jsonify({"error": {"code": "STRIPE_ERROR", "message": str(e)}}), 500

@subscription_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Stripe Webhook"""
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = StripeService.handle_webhook(payload, sig_header)
    except Exception as e:
        return jsonify({"error": {"code": "WEBHOOK_ERROR", "message": str(e)}}), 400

    event_type = event.get('type')
    data_object = event.get('data', {}).get('object', {})

    if event_type == 'checkout.session.completed':
        # Upgrade tier
        metadata = data_object.get('metadata', {})
        user_id = metadata.get('user_id')
        tier = metadata.get('tier')
        cycle = metadata.get('cycle')
        stripe_sub_id = data_object.get('subscription')
        
        if user_id:
            sub = QuotaService._ensure_subscription(int(user_id))
            sub.tier = tier
            sub.billing_cycle = cycle
            sub.stripe_subscription_id = stripe_sub_id
            sub.status = 'active'
            
            # Optional: handle trial/period if available in session
            # For simplicity, we can fetch sub details if needed, 
            # or wait for invoice.paid to set period
            
            # Update limits based on config
            plan_config = get_plan_config(tier)
            sub.monthly_minutes_limit = plan_config.get('monthly_minutes', 60)
            db.session.commit()

    elif event_type == 'invoice.paid':
        # Record invoice, reset minutes, update period
        stripe_sub_id = data_object.get('subscription')
        if stripe_sub_id:
            sub = Subscription.query.filter_by(stripe_subscription_id=stripe_sub_id).first()
            if sub:
                sub.minutes_used = 0.0
                
                # Update period from line items if available
                lines = data_object.get('lines', {}).get('data', [])
                if lines:
                    period = lines[0].get('period', {})
                    if period.get('start'):
                        sub.current_period_start = datetime.fromtimestamp(period['start'])
                    if period.get('end'):
                        sub.current_period_end = datetime.fromtimestamp(period['end'])

                new_invoice = Invoice(
                    user_id=sub.user_id,
                    stripe_invoice_id=data_object.get('id'),
                    amount=data_object.get('amount_paid'),
                    currency=data_object.get('currency'),
                    status='paid',
                    description=f"Subscription payment for {sub.tier}",
                    created_at=datetime.utcnow()
                )
                db.session.add(new_invoice)
                db.session.commit()

    elif event_type == 'customer.subscription.deleted':
        # Downgrade to free
        stripe_sub_id = data_object.get('id')
        sub = Subscription.query.filter_by(stripe_subscription_id=stripe_sub_id).first()
        if sub:
            sub.tier = 'free'
            sub.billing_cycle = None
            sub.stripe_subscription_id = None
            sub.status = 'active'
            sub.current_period_start = None
            sub.current_period_end = None
            sub.monthly_minutes_limit = get_plan_config('free')['monthly_minutes']
            db.session.commit()

    elif event_type == 'customer.subscription.updated':
        stripe_sub_id = data_object.get('id')
        sub = Subscription.query.filter_by(stripe_subscription_id=stripe_sub_id).first()
        if sub:
            sub.status = data_object.get('status')
            sub.current_period_start = datetime.fromtimestamp(data_object.get('current_period_start'))
            sub.current_period_end = datetime.fromtimestamp(data_object.get('current_period_end'))
            db.session.commit()

    elif event_type == 'invoice.payment_failed':
        stripe_sub_id = data_object.get('subscription')
        if stripe_sub_id:
            sub = Subscription.query.filter_by(stripe_subscription_id=stripe_sub_id).first()
            if sub:
                sub.status = 'past_due'
                db.session.commit()

    return jsonify({"status": "success"})

@subscription_bp.route('/cancel', methods=['POST'])
@jwt_required
def cancel_subscription():
    sub = Subscription.query.filter_by(user_id=g.current_user.id).first()
    if not sub or not sub.stripe_subscription_id:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "No active subscription to cancel"}}), 404
    
    try:
        StripeService.cancel_subscription(sub.stripe_subscription_id)
        sub.status = 'cancelled' # Should be confirmed by webhook later, but can set here too
        db.session.commit()
        return jsonify({"data": {"message": "Subscription will be cancelled at the end of the period"}})
    except Exception as e:
        return jsonify({"error": {"code": "STRIPE_ERROR", "message": str(e)}}), 500

@subscription_bp.route('/reactivate', methods=['POST'])
@jwt_required
def reactivate_subscription():
    sub = Subscription.query.filter_by(user_id=g.current_user.id).first()
    if not sub or not sub.stripe_subscription_id:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "No cancelled subscription to reactivate"}}), 404
    
    try:
        StripeService.reactivate_subscription(sub.stripe_subscription_id)
        sub.status = 'active'
        db.session.commit()
        return jsonify({"data": {"message": "Subscription reactivated"}})
    except Exception as e:
        return jsonify({"error": {"code": "STRIPE_ERROR", "message": str(e)}}), 500

@subscription_bp.route('/usage', methods=['GET'])
@jwt_required
def get_usage():
    summary = QuotaService.get_usage_summary(g.current_user.id)
    return jsonify({"data": summary})

@subscription_bp.route('/invoices', methods=['GET'])
@jwt_required
def list_invoices():
    invoices = Invoice.query.filter_by(user_id=g.current_user.id).order_by(Invoice.created_at.desc()).all()
    return jsonify({
        "data": [
            {
                "id": inv.id,
                "amount": inv.amount,
                "currency": inv.currency,
                "status": inv.status,
                "created_at": inv.created_at.isoformat()
            } for inv in invoices
        ]
    })

@subscription_bp.route('/portal', methods=['POST'])
@jwt_required
def create_portal():
    sub = Subscription.query.filter_by(user_id=g.current_user.id).first()
    if not sub or not sub.stripe_customer_id:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "No stripe customer found"}}), 404
    
    return_url = request.json.get('return_url')
    if not return_url:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Missing return_url"}}), 400

    try:
        url = StripeService.create_portal_session(sub.stripe_customer_id, return_url)
        return jsonify({"data": {"portal_url": url}})
    except Exception as e:
        return jsonify({"error": {"code": "STRIPE_ERROR", "message": str(e)}}), 500
