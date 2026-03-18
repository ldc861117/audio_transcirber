"""
Track A — JWT Authentication Tests
Uses shared conftest fixtures (app, client, clean_db, auth_headers).
"""
import pytest


class TestRegister:
    def test_register_success(self, client):
        resp = client.post('/api/v2/auth/register', json={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'Pass1234!'
        })
        assert resp.status_code == 201
        data = resp.get_json()['data']
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert data['user']['username'] == 'newuser'
        assert data['user']['email'] == 'new@example.com'

    def test_register_duplicate_username(self, client):
        client.post('/api/v2/auth/register', json={
            'username': 'dup', 'email': 'a@a.com', 'password': 'Pass1234!'
        })
        resp = client.post('/api/v2/auth/register', json={
            'username': 'dup', 'email': 'b@b.com', 'password': 'Pass1234!'
        })
        assert resp.status_code == 409
        assert resp.get_json()['error']['code'] == 'CONFLICT'

    def test_register_duplicate_email(self, client):
        client.post('/api/v2/auth/register', json={
            'username': 'user1', 'email': 'same@a.com', 'password': 'Pass1234!'
        })
        resp = client.post('/api/v2/auth/register', json={
            'username': 'user2', 'email': 'same@a.com', 'password': 'Pass1234!'
        })
        assert resp.status_code == 409

    def test_register_missing_fields(self, client):
        resp = client.post('/api/v2/auth/register', json={'username': 'x'})
        assert resp.status_code == 400


class TestLogin:
    def test_login_success(self, client):
        client.post('/api/v2/auth/register', json={
            'username': 'loginuser', 'email': 'l@e.com', 'password': 'Pass1234!'
        })
        resp = client.post('/api/v2/auth/login', json={
            'username': 'loginuser', 'password': 'Pass1234!'
        })
        assert resp.status_code == 200
        data = resp.get_json()['data']
        assert 'access_token' in data
        assert 'refresh_token' in data

    def test_login_by_email(self, client):
        client.post('/api/v2/auth/register', json={
            'username': 'emaillogin', 'email': 'e@e.com', 'password': 'Pass1234!'
        })
        resp = client.post('/api/v2/auth/login', json={
            'username': 'e@e.com', 'password': 'Pass1234!'
        })
        assert resp.status_code == 200

    def test_login_wrong_password(self, client):
        client.post('/api/v2/auth/register', json={
            'username': 'wrongpw', 'email': 'w@e.com', 'password': 'Pass1234!'
        })
        resp = client.post('/api/v2/auth/login', json={
            'username': 'wrongpw', 'password': 'WrongPassword!'
        })
        assert resp.status_code == 401

    def test_login_nonexistent(self, client):
        resp = client.post('/api/v2/auth/login', json={
            'username': 'ghost', 'password': 'nope'
        })
        assert resp.status_code == 401


class TestProtectedRoutes:
    def test_me_success(self, client, auth_headers):
        resp = client.get('/api/v2/auth/me', headers=auth_headers['headers'])
        assert resp.status_code == 200
        assert resp.get_json()['data']['username'] == 'testuser'

    def test_me_no_token(self, client):
        resp = client.get('/api/v2/auth/me')
        assert resp.status_code == 401
        assert resp.get_json()['error']['code'] == 'AUTH_REQUIRED'

    def test_me_invalid_token(self, client):
        resp = client.get('/api/v2/auth/me', headers={
            'Authorization': 'Bearer invalid.token.here'
        })
        assert resp.status_code == 401
        assert resp.get_json()['error']['code'] == 'TOKEN_INVALID'


class TestTokenRefresh:
    def test_refresh_success(self, client, auth_headers):
        resp = client.post('/api/v2/auth/refresh', json={
            'refresh_token': auth_headers['refresh_token']
        })
        assert resp.status_code == 200
        data = resp.get_json()['data']
        assert 'access_token' in data
        assert len(data['access_token']) > 10  # valid JWT

    def test_refresh_invalid_token(self, client):
        resp = client.post('/api/v2/auth/refresh', json={
            'refresh_token': 'fake-refresh-token'
        })
        assert resp.status_code == 401


class TestLogout:
    def test_logout_invalidates_refresh(self, client, auth_headers):
        # Logout
        client.post('/api/v2/auth/logout', json={
            'refresh_token': auth_headers['refresh_token']
        })
        # Refresh should now fail
        resp = client.post('/api/v2/auth/refresh', json={
            'refresh_token': auth_headers['refresh_token']
        })
        assert resp.status_code == 401


class TestChangePassword:
    def test_change_password_success(self, client, auth_headers):
        resp = client.post('/api/v2/auth/change-password', json={
            'old_password': 'Test1234!',
            'new_password': 'NewPass5678!'
        }, headers=auth_headers['headers'])
        assert resp.status_code == 200

        # Verify new password works
        resp = client.post('/api/v2/auth/login', json={
            'username': 'testuser', 'password': 'NewPass5678!'
        })
        assert resp.status_code == 200

    def test_change_password_wrong_old(self, client, auth_headers):
        resp = client.post('/api/v2/auth/change-password', json={
            'old_password': 'WrongOld!',
            'new_password': 'NewPass5678!'
        }, headers=auth_headers['headers'])
        assert resp.status_code == 400 or resp.status_code == 401
