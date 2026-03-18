from functools import wraps
from flask import request, jsonify, g, current_app
import os
import jwt
from .jwt_manager import verify_access_token
from .models import User

def jwt_required(f):
    """
    从 Authorization: Bearer <token> 提取并验证 access_token。
    验证通过后将 user 对象注入 g.current_user。
    失败返回 401 + {"error": {"code": "AUTH_REQUIRED" | "TOKEN_EXPIRED" | "TOKEN_INVALID"}}
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Desktop mode bypass
        if os.environ.get('DESKTOP_MODE') == 'true' and not request.headers.get('Authorization'):
            from .desktop_adapter import DesktopAdapter
            g.current_user = DesktopAdapter.get_default_user()
            return f(*args, **kwargs)

        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": {"code": "AUTH_REQUIRED", "message": "Authentication required"}}), 401
        
        token = auth_header.split(' ')[1]
        try:
            payload = verify_access_token(token)
            user = User.get_by_id(int(payload['sub']))
            if not user:
                return jsonify({"error": {"code": "AUTH_REQUIRED", "message": "User not found"}}), 401
            
            if user.status == 'suspended':
                return jsonify({"error": {"code": "USER_SUSPENDED", "message": "Account suspended"}}), 403
            
            g.current_user = user
        except jwt.ExpiredSignatureError:
            return jsonify({"error": {"code": "TOKEN_EXPIRED", "message": "Token has expired"}}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": {"code": "TOKEN_INVALID", "message": "Invalid token"}}), 401
        except Exception as e:
            current_app.logger.error(f"JWT Decorator Auth Error: {str(e)}")
            return jsonify({"error": {"code": "TOKEN_INVALID", "message": "Authentication failed"}}), 401
            
        return f(*args, **kwargs)
            
    return decorated

def admin_required(f):
    """
    先执行 jwt_required，然后检查 g.current_user.role == 'admin'。
    非 admin 返回 403。
    """
    @wraps(f)
    @jwt_required
    def decorated(*args, **kwargs):
        if g.current_user.role != 'admin':
            return jsonify({"error": {"code": "FORBIDDEN", "message": "Admin access required"}}), 403
        return f(*args, **kwargs)
    return decorated

def subscription_required(min_tier='basic'):
    """
    检查用户订阅等级 >= min_tier。
    等级顺序: free < basic < pro
    不满足返回 403 + {"error": {"code": "INSUFFICIENT_PLAN"}}
    """
    tier_order = {'free': 0, 'basic': 1, 'pro': 2}
    
    def decorator(f):
        @wraps(f)
        @jwt_required
        def decorated(*args, **kwargs):
            user_tier = g.current_user.subscription.tier if g.current_user.subscription else 'free'
            if tier_order.get(user_tier, 0) < tier_order.get(min_tier, 0):
                return jsonify({"error": {"code": "INSUFFICIENT_PLAN", "message": f"Requires {min_tier} plan"}}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator
