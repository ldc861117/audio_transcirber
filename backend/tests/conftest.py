"""
Shared test fixtures for all V2 backend tests.
Uses create_app() with SQLALCHEMY_DATABASE_URI overridden to in-memory SQLite.
"""
import os
import pytest
from backend.db.base import db as _db


@pytest.fixture(scope='session')
def app():
    """Create application for testing with in-memory SQLite."""
    # Set env vars BEFORE create_app reads them
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    os.environ['JWT_SECRET_KEY'] = 'test-secret-key-for-jwt-at-least-32-chars'
    os.environ['JWT_REFRESH_SECRET_KEY'] = 'test-refresh-secret-for-jwt-32-chars'
    os.environ['STRIPE_SECRET_KEY'] = 'mock-stripe-key'
    os.environ['STRIPE_WEBHOOK_SECRET'] = 'mock-webhook-secret'

    from backend.app import create_app
    app = create_app('development')
    app.config['TESTING'] = True

    yield app

    with app.app_context():
        _db.drop_all()


@pytest.fixture(autouse=True)
def clean_db(app):
    """Reset DB before each test."""
    with app.app_context():
        from sqlalchemy import text
        for table in ['quota_usage', 'invoices', 'refresh_tokens', 'subscriptions', 'users']:
            try:
                _db.session.execute(text(f'DELETE FROM {table}'))
            except Exception:
                _db.session.rollback()
        _db.session.commit()
        yield
        _db.session.rollback()


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    """Register a user and return auth headers + user data."""
    resp = client.post('/api/v2/auth/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'Test1234!'
    })
    data = resp.get_json()['data']
    return {
        'headers': {'Authorization': f'Bearer {data["access_token"]}'},
        'access_token': data['access_token'],
        'refresh_token': data['refresh_token'],
        'user': data['user'],
    }
