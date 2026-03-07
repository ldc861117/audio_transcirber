import pytest
from flask import Flask
from backend.db.base import db, init_db
from backend.config import configs
from backend.auth.models import User, RefreshToken
from backend.auth.routes import auth_bp
from backend.auth.jwt_manager import create_access_token
import json

# Define the mock model globally to avoid re-definition errors in SQLAlchemy MetaData
class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    tier = db.Column(db.String(20), default='free')
    __table_args__ = {'extend_existing': True}

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.from_object(configs['development'])
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True
    app.config['JWT_SECRET_KEY'] = 'test-secret-key-at-least-32-chars-long'
    app.config['JWT_REFRESH_SECRET_KEY'] = 'test-refresh-secret-key-at-least-32-chars-long'
    
    init_db(app)
    # Ensure blueprint is only registered once if app fixture is used multiple times
    if 'auth' not in app.blueprints:
        app.register_blueprint(auth_bp, url_prefix='/api/v2/auth')
    
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture(autouse=True)
def setup_database(app):
    with app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()

def test_register_success(client):
    response = client.post('/api/v2/auth/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123'
    })
    assert response.status_code == 201
    data = response.get_json()
    assert 'access_token' in data['data']
    assert 'refresh_token' in data['data']
    assert data['data']['user']['username'] == 'testuser'

def test_register_duplicate_username(client):
    client.post('/api/v2/auth/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123'
    })
    response = client.post('/api/v2/auth/register', json={
        'username': 'testuser',
        'email': 'test2@example.com',
        'password': 'password123'
    })
    assert response.status_code == 409
    assert response.get_json()['error']['code'] == 'CONFLICT'

def test_login_success(client):
    client.post('/api/v2/auth/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123'
    })
    response = client.post('/api/v2/auth/login', json={
        'username': 'testuser',
        'password': 'password123'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert 'access_token' in data['data']

def test_login_invalid_credentials(client):
    client.post('/api/v2/auth/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123'
    })
    response = client.post('/api/v2/auth/login', json={
        'username': 'testuser',
        'password': 'wrongpassword'
    })
    assert response.status_code == 401

def test_me_protected(client):
    # Register and login to get token
    client.post('/api/v2/auth/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123'
    })
    login_resp = client.post('/api/v2/auth/login', json={
        'username': 'testuser',
        'password': 'password123'
    })
    token = login_resp.get_json()['data']['access_token']
    
    # Test protected /me
    response = client.get('/api/v2/auth/me', headers={
        'Authorization': f'Bearer {token}'
    })
    assert response.status_code == 200
    assert response.get_json()['data']['username'] == 'testuser'

def test_me_unauthorized(client):
    response = client.get('/api/v2/auth/me')
    assert response.status_code == 401

def test_refresh_token(client):
    reg_resp = client.post('/api/v2/auth/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123'
    })
    refresh_token = reg_resp.get_json()['data']['refresh_token']
    
    response = client.post('/api/v2/auth/refresh', json={
        'refresh_token': refresh_token
    })
    assert response.status_code == 200
    assert 'access_token' in response.get_json()['data']

def test_logout(client):
    reg_resp = client.post('/api/v2/auth/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123'
    })
    refresh_token = reg_resp.get_json()['data']['refresh_token']
    
    # Logout
    client.post('/api/v2/auth/logout', json={'refresh_token': refresh_token})
    
    # Try refresh again
    response = client.post('/api/v2/auth/refresh', json={
        'refresh_token': refresh_token
    })
    assert response.status_code == 401

def test_change_password(client):
    client.post('/api/v2/auth/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123'
    })
    login_resp = client.post('/api/v2/auth/login', json={
        'username': 'testuser',
        'password': 'password123'
    })
    token = login_resp.get_json()['data']['access_token']
    
    response = client.post('/api/v2/auth/change-password', json={
        'old_password': 'password123',
        'new_password': 'newpassword456'
    }, headers={'Authorization': f'Bearer {token}'})
    
    assert response.status_code == 200
    
    # Verify new password
    login_resp = client.post('/api/v2/auth/login', json={
        'username': 'testuser',
        'password': 'newpassword456'
    })
    assert login_resp.status_code == 200
