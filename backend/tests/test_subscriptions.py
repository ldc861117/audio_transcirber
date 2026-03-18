"""
Track B — Subscription & Payment Tests
Uses shared conftest fixtures. Tests plan config, quota service, and subscription routes.
Note: subscription routes use a local mock jwt_required that defaults to user_id=1,
so we create a User with id=1 for route tests.
"""
import pytest
import json
from backend.db.base import db
from backend.auth.models import User
from backend.auth.jwt_manager import create_access_token
from backend.subscriptions.models import Subscription, QuotaUsage, Invoice
from backend.subscriptions.plan_config import get_plan_config, is_tier_gte, get_all_plans
from backend.subscriptions.quota_service import QuotaService


# --- Pure unit tests (no HTTP) ---

class TestPlanConfig:
    def test_free_plan_limits(self):
        cfg = get_plan_config('free')
        assert cfg['monthly_minutes'] == 60
        assert cfg['max_single_minutes'] == 30
        assert cfg['max_file_size_mb'] == 50

    def test_pro_plan_unlimited(self):
        cfg = get_plan_config('pro')
        assert cfg['monthly_minutes'] == -1  # unlimited
        assert cfg['max_single_minutes'] == -1

    def test_tier_comparison(self):
        assert is_tier_gte('pro', 'basic') is True
        assert is_tier_gte('pro', 'free') is True
        assert is_tier_gte('basic', 'pro') is False
        assert is_tier_gte('free', 'free') is True
        assert is_tier_gte('invalid', 'free') is False

    def test_all_plans_returns_three(self):
        plans = get_all_plans()
        assert 'free' in plans
        assert 'basic' in plans
        assert 'pro' in plans


class TestQuotaService:
    """Tests need app context + a user in DB."""

    @pytest.fixture(autouse=True)
    def create_user(self, app):
        with app.app_context():
            u = User(id=1, username='quotauser', email='q@e.com',
                     password_hash='x')
            db.session.add(u)
            db.session.commit()

    def test_check_within_limit(self, app):
        with app.app_context():
            res = QuotaService.check_quota(1, estimated_minutes=10, file_size_mb=10)
            assert res['allowed'] is True
            assert res['plan'] == 'free'

    def test_single_file_too_long(self, app):
        with app.app_context():
            res = QuotaService.check_quota(1, estimated_minutes=31)
            assert res['allowed'] is False
            assert 'Single request limit' in res['error']

    def test_file_too_large(self, app):
        with app.app_context():
            res = QuotaService.check_quota(1, file_size_mb=51)
            assert res['allowed'] is False
            assert 'File size limit' in res['error']

    def test_monthly_exceeded(self, app):
        with app.app_context():
            # Use up nearly all quota
            QuotaService.deduct_quota(1, 'task-fill', 55)
            res = QuotaService.check_quota(1, estimated_minutes=10)
            assert res['allowed'] is False
            assert 'Insufficient monthly quota' in res['error']

    def test_deduct_records_usage(self, app):
        with app.app_context():
            QuotaService.deduct_quota(1, 'task-1', 5.5)
            sub = Subscription.query.filter_by(user_id=1).first()
            assert sub.minutes_used == 5.5
            usage = QuotaUsage.query.filter_by(user_id=1).first()
            assert usage.minutes_used == 5.5
            assert usage.task_id == 'task-1'

    def test_feature_free_plan(self, app):
        with app.app_context():
            assert QuotaService.check_feature(1, 'diarization') is False
            assert QuotaService.check_feature(1, 'export:txt') is True
            assert QuotaService.check_feature(1, 'export:pdf') is False

    def test_feature_pro_plan(self, app):
        with app.app_context():
            sub = QuotaService._ensure_subscription(1)
            sub.tier = 'pro'
            db.session.commit()
            assert QuotaService.check_feature(1, 'diarization') is True
            assert QuotaService.check_feature(1, 'export:pdf') is True
            assert QuotaService.check_feature(1, 'api_access') is True

    def test_usage_summary(self, app):
        with app.app_context():
            QuotaService.deduct_quota(1, 'task-a', 3.0)
            QuotaService.deduct_quota(1, 'task-b', 2.0)
            summary = QuotaService.get_usage_summary(1)
            assert summary['total_used'] == 5.0
            assert summary['tier'] == 'free'
            assert len(summary['history']) == 2


# --- Route Integration Tests ---

class TestSubscriptionRoutes:
    """
    Subscription routes now use real jwt_required.
    Tests must provide valid JWT auth headers.
    """

    @pytest.fixture(autouse=True)
    def create_user(self, app):
        with app.app_context():
            u = User(id=1, username='subrouter', email='s@e.com',
                     password_hash='x')
            db.session.add(u)
            db.session.commit()

    def _auth_headers(self, app):
        with app.app_context():
            user = User.query.get(1)
            token = create_access_token(user)
        return {'Authorization': f'Bearer {token}'}

    def test_plans_public(self, client):
        resp = client.get('/api/v2/subscriptions/plans')
        assert resp.status_code == 200
        data = resp.get_json()['data']
        assert 'pro' in data
        assert data['pro']['monthly_minutes'] == -1

    def test_my_subscription_default_free(self, client, app):
        headers = self._auth_headers(app)
        resp = client.get('/api/v2/subscriptions/me', headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()['data']
        assert data['tier'] == 'free'
        assert data['monthly_minutes_limit'] == 60

    def test_usage_route(self, client, app):
        with app.app_context():
            QuotaService.deduct_quota(1, 'task-r', 7.0)
        headers = self._auth_headers(app)
        resp = client.get('/api/v2/subscriptions/usage', headers=headers)
        assert resp.status_code == 200
        data = resp.get_json()['data']
        assert data['total_used'] == 7.0

    def test_invoices_empty(self, client, app):
        headers = self._auth_headers(app)
        resp = client.get('/api/v2/subscriptions/invoices', headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()['data'] == []


class TestWebhooks:
    @pytest.fixture(autouse=True)
    def create_user(self, app):
        with app.app_context():
            u = User(id=1, username='whuser', email='wh@e.com',
                     password_hash='x')
            db.session.add(u)
            db.session.commit()

    def test_checkout_completed_upgrades_tier(self, client, app):
        payload = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "metadata": {"user_id": "1", "tier": "basic", "cycle": "monthly"},
                    "subscription": "sub_mock_123"
                }
            }
        }
        resp = client.post('/api/v2/subscriptions/webhook',
                           data=json.dumps(payload),
                           content_type='application/json')
        assert resp.status_code == 200

        with app.app_context():
            sub = Subscription.query.filter_by(user_id=1).first()
            assert sub.tier == 'basic'
            assert sub.stripe_subscription_id == 'sub_mock_123'
            assert sub.monthly_minutes_limit == 300

    def test_invoice_paid_resets_quota(self, client, app):
        with app.app_context():
            sub = QuotaService._ensure_subscription(1)
            sub.stripe_subscription_id = 'sub_reset'
            sub.minutes_used = 150.0
            db.session.commit()

        payload = {
            "type": "invoice.paid",
            "data": {
                "object": {
                    "subscription": "sub_reset",
                    "id": "inv_001",
                    "amount_paid": 2900,
                    "currency": "cny"
                }
            }
        }
        resp = client.post('/api/v2/subscriptions/webhook',
                           data=json.dumps(payload),
                           content_type='application/json')
        assert resp.status_code == 200

        with app.app_context():
            sub = Subscription.query.filter_by(user_id=1).first()
            assert sub.minutes_used == 0.0
            inv = Invoice.query.filter_by(user_id=1).first()
            assert inv.stripe_invoice_id == 'inv_001'
            assert inv.amount == 2900

    def test_subscription_deleted_downgrades(self, client, app):
        # First create a subscription
        with app.app_context():
            sub = QuotaService._ensure_subscription(1)
            sub.tier = 'pro'
            sub.stripe_subscription_id = 'sub_del_123'
            db.session.commit()

        payload = {
            "type": "customer.subscription.deleted",
            "data": {"object": {"id": "sub_del_123"}}
        }
        resp = client.post('/api/v2/subscriptions/webhook',
                           data=json.dumps(payload),
                           content_type='application/json')
        assert resp.status_code == 200

        with app.app_context():
            sub = Subscription.query.filter_by(user_id=1).first()
            assert sub.tier == 'free'
