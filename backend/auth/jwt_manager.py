import jwt
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from flask import current_app
from .models import RefreshToken, User

def validate_jwt_secrets():
    """
    启动校验：确保 JWT_SECRET_KEY 和 JWT_REFRESH_SECRET_KEY 已配置且非默认值。
    """
    secret = current_app.config.get('JWT_SECRET_KEY')
    refresh_secret = current_app.config.get('JWT_REFRESH_SECRET_KEY')

    if not secret or secret == 'dev-secret-change-me':
        current_app.logger.warning("JWT_SECRET_KEY is not set or using default value. Please update for production.")

    if not refresh_secret or refresh_secret == 'dev-refresh-secret':
        current_app.logger.warning("JWT_REFRESH_SECRET_KEY is not set or using default value. Please update for production.")

def create_access_token(user) -> str:
    """创建 15 分钟 access token，payload 含 sub, username, role, tier"""
    now = datetime.now(timezone.utc)
    # tier defaults to 'free' if no subscription
    try:
        tier = user.subscription.tier if user.subscription else 'free'
    except Exception:
        tier = 'free'
    
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "tier": tier,
        "iat": int(now.timestamp()),
        "exp": int((now + current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', timedelta(minutes=15))).timestamp()),
        "type": "access"
    }
    secret = current_app.config['JWT_SECRET_KEY']
    return jwt.encode(payload, secret, algorithm='HS256')

def create_refresh_token(user) -> str:
    """创建 7 天 refresh token，存储 hash 到 DB"""
    now = datetime.now(timezone.utc)
    expires_delta = current_app.config.get('JWT_REFRESH_TOKEN_EXPIRES', timedelta(days=7))
    expires_at = now + expires_delta
    
    jti = str(uuid.uuid4())
    
    payload = {
        "sub": str(user.id),
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "type": "refresh"
    }
    
    secret = current_app.config['JWT_REFRESH_SECRET_KEY']
    token = jwt.encode(payload, secret, algorithm='HS256')
    
    # Store hash
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    RefreshToken.create(user.id, token_hash, expires_at)
    
    return token

def verify_access_token(token: str) -> dict:
    """
    验证 access token，返回 payload。
    可能抛出 jwt.ExpiredSignatureError 或 jwt.InvalidTokenError
    """
    secret = current_app.config['JWT_SECRET_KEY']
    payload = jwt.decode(token, secret, algorithms=['HS256'])
    if payload.get('type') != 'access':
        raise jwt.InvalidTokenError("Not an access token")
    return payload

def refresh_access_token(refresh_token: str) -> str | None:
    """用 refresh token 换新 access token"""
    try:
        secret = current_app.config['JWT_REFRESH_SECRET_KEY']
        payload = jwt.decode(refresh_token, secret, algorithms=['HS256'])
        if payload.get('type') != 'refresh':
            return None
            
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        rt = RefreshToken.find_valid(token_hash)
        
        if not rt:
            return None
            
        user = User.get_by_id(int(payload['sub']))
        if not user or user.status != 'active':
            return None
            
        return create_access_token(user)
    except Exception as e:
        current_app.logger.error(f"JWT Refresh Decode Error: {str(e)}")
        return None

def revoke_refresh_token(refresh_token: str) -> bool:
    """撤销 refresh token"""
    try:
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        rt = RefreshToken.query.filter_by(token_hash=token_hash).first()
        if rt:
            rt.revoke()
            return True
        return False
    except Exception:
        return False
