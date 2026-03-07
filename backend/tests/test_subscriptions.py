import pytest
from flask import Flask
from backend.db.base import db, init_db
from backend.subscriptions.models import Subscription, QuotaUsage, Invoice
from backend.subscriptions.plan_config import get_plan_config, is_tier_gte
from backend.subscriptions.quota_service import QuotaService
from backend.subscriptions.stripe_service import StripeService
from backend.subscriptions.routes import subscription_bp
import json
from sqlalchemy import text

@pytest.fixture(scope='session')
def base_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['STRIPE_SECRET_KEY'] = 'mock-key'
    
    # Mock User table (simplified)
    class User(db.Model):
        __tablename__ = 'users'
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(32))
        email = db.Column(db.String(255))
    
    init_db(app)
    app.register_blueprint(subscription_bp, url_prefix='/api/v2/subscriptions')
    
    with app.app_context():
        db.create_all()
    
    return app

@pytest.fixture
def app(base_app):
    with base_app.app_context():
        # Clean up tables before each test
        db.session.execute(text("DELETE FROM quota_usage"))
        db.session.execute(text("DELETE FROM invoices"))
        db.session.execute(text("DELETE FROM subscriptions"))
        db.session.execute(text("DELETE FROM users"))
        
        # Add a test user
        # We need to get the User class again because it's local to base_app fixture
        # But we can just use the table directly if needed, or better, 
        # define User globally in the test module.
        from sqlalchemy import MetaData
        User = [m for m in db.Model.registry.mappers if m.class_.__tablename__ == 'users'][0].class_
        
        user = User(id=1, username='testuser', email='test@example.com')
        db.session.add(user)
        db.session.commit()
        
    yield base_app

@pytest.fixture
def client(app):
    return app.test_client()

def test_plan_config():
    assert get_plan_config('free')['monthly_minutes'] == 60
    assert is_tier_gte('pro', 'basic') is True
    assert is_tier_gte('basic', 'pro') is False
    assert is_tier_gte('free', 'free') is True

def test_quota_check(app):
    with app.app_context():
        # Test free plan limits
        res = QuotaService.check_quota(1, estimated_minutes=10, file_size_mb=10)
        assert res['allowed'] is True
        
        # Test too long for free
        res = QuotaService.check_quota(1, estimated_minutes=31)
        assert res['allowed'] is False
        assert "Single request limit" in res['error']
        
        # Test too large for free
        res = QuotaService.check_quota(1, file_size_mb=51)
        assert res['allowed'] is False
        assert "File size limit" in res['error']

def test_quota_deduction(app):
    with app.app_context():
        QuotaService.deduct_quota(1, "task-1", 5.5)
        sub = Subscription.query.filter_by(user_id=1).first()
        assert sub.minutes_used == 5.5
        
        usage = QuotaUsage.query.filter_by(user_id=1).first()
        assert usage.minutes_used == 5.5
        assert usage.task_id == "task-1"

def test_feature_check(app):
    with app.app_context():
        # Free plan feature check
        assert QuotaService.check_feature(1, 'diarization') is False
        assert QuotaService.check_feature(1, 'export:txt') is True
        assert QuotaService.check_feature(1, 'export:pdf') is False
        
        # Upgrade to pro and check again
        sub = Subscription.query.filter_by(user_id=1).first()
        sub.tier = 'pro'
        db.session.commit()
        
        assert QuotaService.check_feature(1, 'diarization') is True
        assert QuotaService.check_feature(1, 'export:pdf') is True

def test_webhook_upgrade(app, client):
    with app.app_context():
        # Mock webhook payload
        payload = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "metadata": {
                        "user_id": "1",
                        "tier": "basic",
                        "cycle": "monthly"
                    },
                    "subscription": "sub_123"
                }
            }
        }
        
        response = client.post('/api/v2/subscriptions/webhook', 
                                data=json.dumps(payload),
                                content_type='application/json')
        
        assert response.status_code == 200
        
        sub = Subscription.query.filter_by(user_id=1).first()
        assert sub.tier == 'basic'
        assert sub.stripe_subscription_id == 'sub_123'
        assert sub.monthly_minutes_limit == 300

def test_webhook_invoice_paid(app, client):
     with app.app_context():
        sub = QuotaService._ensure_subscription(1)
        sub.stripe_subscription_id = 'sub_123'
        sub.minutes_used = 150.0
        db.session.commit()
        
        payload = {
            "type": "invoice.paid",
            "data": {
                "object": {
                    "subscription": "sub_123",
                    "id": "inv_123",
                    "amount_paid": 2900,
                    "currency": "cny"
                }
            }
        }
        
        client.post('/api/v2/subscriptions/webhook', 
                    data=json.dumps(payload),
                    content_type='application/json')
        
        sub = Subscription.query.filter_by(user_id=1).first()
        assert sub.minutes_used == 0.0
        
        inv = Invoice.query.filter_by(user_id=1).first()
        assert inv.stripe_invoice_id == 'inv_123'
        assert inv.amount == 2900

def test_routes_me(client):
    # Mocking JWT with id 1 (see jwt_required in routes.py)
    response = client.get('/api/v2/subscriptions/me')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['data']['tier'] == 'free'

def test_routes_plans(client):
    response = client.get('/api/v2/subscriptions/plans')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'pro' in data['data']
    assert data['data']['pro']['monthly_minutes'] == -1
