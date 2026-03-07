from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, g
from .models import User, RefreshToken
from .jwt_manager import (
    create_access_token, 
    create_refresh_token, 
    refresh_access_token, 
    revoke_refresh_token
)
from .decorators import jwt_required
from .utils import validate_email, validate_username, validate_password
from backend.db.base import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Missing data"}}), 400
        
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not all([username, email, password]):
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Missing required fields"}}), 400
        
    if not validate_username(username):
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid username (2-32 chars)"}}), 400
        
    if not validate_email(email):
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid email format"}}), 400
        
    if not validate_password(password):
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid password (min 6 chars)"}}), 400
        
    if User.get_by_username(username):
        return jsonify({"error": {"code": "CONFLICT", "message": "Username already exists"}}), 409
        
    if User.get_by_email(email):
        return jsonify({"error": {"code": "CONFLICT", "message": "Email already exists"}}), 409
        
    try:
        user = User.create(username, email, password)
        # Note: Track B should handle automatic free subscription creation via signal or in User.create
        # For now, we assume user creation is enough or Track B will handle it.
        
        access_token = create_access_token(user)
        refresh_token = create_refresh_token(user)
        
        return jsonify({
            "data": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                    "tier": "free" # Default
                }
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": {"code": "INTERNAL_ERROR", "message": str(e)}}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Missing credentials"}}), 400
        
    identifier = data.get('username') or data.get('email')
    password = data.get('password')
    
    if not identifier or not password:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Missing username/email or password"}}), 400
        
    user = User.authenticate(identifier, password)
    if not user:
        return jsonify({"error": {"code": "UNAUTHORIZED", "message": "Invalid credentials"}}), 401
        
    if user.status != 'active':
        return jsonify({"error": {"code": "USER_SUSPENDED", "message": f"Account is {user.status}"}}), 403
        
    user.last_login_at = datetime.now(timezone.utc)
    db.session.commit()
    
    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)
    
    tier = user.subscription.tier if user.subscription else 'free'
    
    return jsonify({
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "tier": tier
            }
        }
    }), 200

@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    data = request.get_json()
    refresh_token = data.get('refresh_token')
    if not refresh_token:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Missing refresh token"}}), 400
        
    new_access_token = refresh_access_token(refresh_token)
    if not new_access_token:
        return jsonify({"error": {"code": "TOKEN_INVALID", "message": "Invalid or expired refresh token"}}), 401
        
    return jsonify({
        "data": {
            "access_token": new_access_token
        }
    }), 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    data = request.get_json()
    refresh_token = data.get('refresh_token')
    if refresh_token:
        revoke_refresh_token(refresh_token)
    return jsonify({"data": {"message": "Logged out successfully"}}), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required
def me():
    user = g.current_user
    tier = user.subscription.tier if user.subscription else 'free'
    return jsonify({
        "data": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "status": user.status,
            "email_verified": user.email_verified,
            "tier": tier,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None
        }
    }), 200

@auth_bp.route('/me', methods=['PUT'])
@jwt_required
def update_me():
    user = g.current_user
    data = request.get_json()
    
    username = data.get('username')
    email = data.get('email')
    
    if username:
        if not validate_username(username):
            return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid username"}}), 400
        existing = User.get_by_username(username)
        if existing and existing.id != user.id:
            return jsonify({"error": {"code": "CONFLICT", "message": "Username already taken"}}), 409
        user.username = username
        
    if email:
        if not validate_email(email):
            return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid email"}}), 400
        existing = User.get_by_email(email)
        if existing and existing.id != user.id:
            return jsonify({"error": {"code": "CONFLICT", "message": "Email already taken"}}), 409
        user.email = email
        user.email_verified = False # Reset verification on email change
        
    db.session.commit()
    
    tier = user.subscription.tier if user.subscription else 'free'
    return jsonify({
        "data": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "tier": tier
        }
    }), 200

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required
def change_password():
    user = g.current_user
    data = request.get_json()
    
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not old_password or not new_password:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Missing passwords"}}), 400
        
    if not user.check_password(old_password):
        return jsonify({"error": {"code": "UNAUTHORIZED", "message": "Incorrect old password"}}), 401
        
    if not validate_password(new_password):
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid new password"}}), 400
        
    user.set_password(new_password)
    RefreshToken.revoke_all_for_user(user.id) # Logout other sessions for security
    db.session.commit()
    
    return jsonify({"data": {"message": "Password updated successfully"}}), 200
