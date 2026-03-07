import stripe
from flask import current_app
from .plan_config import get_plan_config

class StripeService:
    @staticmethod
    def _is_mock():
        key = current_app.config.get('STRIPE_SECRET_KEY', '')
        return not key or key.startswith('mock')

    @staticmethod
    def create_customer(user) -> str:
        """创建 Stripe Customer，返回 customer_id"""
        if StripeService._is_mock():
            return f"cus_mock_{user.id}"
        
        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
        customer = stripe.Customer.create(
            email=user.email,
            name=user.username,
            metadata={'user_id': user.id}
        )
        return customer.id

    @staticmethod
    def create_checkout_session(user_id: int, tier: str, cycle: str,
                                 success_url: str, cancel_url: str) -> str:
        """创建 Checkout Session，返回 session URL"""
        plan_config = get_plan_config(tier)
        if not plan_config:
            raise ValueError(f"Invalid tier: {tier}")
        
        price_id = plan_config.get(f"stripe_price_id_{cycle}")
        if not price_id and not StripeService._is_mock():
            raise ValueError(f"No price ID for {tier} {cycle}")

        if StripeService._is_mock():
            return f"https://checkout.stripe.com/pay/mock_session_{user_id}_{tier}"

        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
        # We need to find or create customer here or pass customer_id from caller
        # For simplicity in this track, we might expect caller to provide customer_id 
        # but the contract says (user_id, tier, cycle...)
        
        # In a real implementation, we'd look up the user's subscription record for the customer_id
        from .models import Subscription
        sub = Subscription.query.filter_by(user_id=user_id).first()
        customer_id = sub.stripe_customer_id if sub else None

        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'user_id': user_id,
                'tier': tier,
                'cycle': cycle
            }
        )
        return session.url

    @staticmethod
    def create_portal_session(customer_id: str, return_url: str) -> str:
        """创建 Billing Portal Session，返回 URL"""
        if StripeService._is_mock():
            return f"https://billing.stripe.com/p/mock_portal_{customer_id}"

        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        return session.url

    @staticmethod
    def handle_webhook(payload: bytes, sig_header: str) -> dict:
        """验证并处理 Webhook 事件"""
        if StripeService._is_mock():
            # In mock mode, we assume the payload is already the event dict
            import json
            return json.loads(payload)

        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
        endpoint_secret = current_app.config['STRIPE_WEBHOOK_SECRET']

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
            return event
        except Exception as e:
            raise e

    @staticmethod
    def cancel_subscription(subscription_id: str) -> bool:
        """取消订阅（周期结束）"""
        if StripeService._is_mock():
            return True

        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
        stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True
        )
        return True

    @staticmethod
    def reactivate_subscription(subscription_id: str) -> bool:
        """重新激活已取消的订阅"""
        if StripeService._is_mock():
            return True

        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
        stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=False
        )
        return True
