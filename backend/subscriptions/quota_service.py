from .models import Subscription, QuotaUsage, db
from .plan_config import get_plan_config
from datetime import datetime

class QuotaService:
    @staticmethod
    def _ensure_subscription(user_id: int) -> Subscription:
        sub = Subscription.query.filter_by(user_id=user_id).first()
        if not sub:
            free_plan = get_plan_config('free')
            sub = Subscription(
                user_id=user_id,
                tier='free',
                monthly_minutes_limit=free_plan['monthly_minutes'],
                minutes_used=0.0,
                status='active'
            )
            db.session.add(sub)
            db.session.commit()
        return sub

    @staticmethod
    def check_quota(user_id: int, estimated_minutes: float = 0,
                    file_size_mb: float = 0) -> dict:
        """
        完整的配额检查:
        - 月度分钟数
        - 单文件时长限制
        - 单文件大小限制
        返回 {"allowed": bool, "remaining": float, "plan": str, "error": str|None}
        """
        sub = QuotaService._ensure_subscription(user_id)
        config = get_plan_config(sub.tier)
        
        if not config:
            return {"allowed": False, "remaining": 0, "plan": sub.tier, "error": "Plan configuration not found"}

        # 1. Check single file duration limit
        max_single = config.get("max_single_minutes", -1)
        if max_single != -1 and estimated_minutes > max_single:
            return {
                "allowed": False, 
                "remaining": sub.monthly_minutes_limit - sub.minutes_used if sub.monthly_minutes_limit != -1 else float('inf'), 
                "plan": sub.tier,
                "error": f"Single request limit exceeded: {max_single} minutes"
            }

        # 2. Check single file size limit
        max_size = config.get("max_file_size_mb", -1)
        if max_size != -1 and file_size_mb > max_size:
             return {
                "allowed": False, 
                "remaining": sub.monthly_minutes_limit - sub.minutes_used if sub.monthly_minutes_limit != -1 else float('inf'), 
                "plan": sub.tier,
                "error": f"File size limit exceeded: {max_size} MB"
            }

        # 3. Check monthly limit
        if sub.monthly_minutes_limit == -1: # Unlimited
            return {"allowed": True, "remaining": float('inf'), "plan": sub.tier}
        
        remaining = sub.monthly_minutes_limit - sub.minutes_used
        if remaining >= estimated_minutes:
            return {"allowed": True, "remaining": remaining, "plan": sub.tier}
        else:
            return {"allowed": False, "remaining": remaining, "plan": sub.tier, "error": "Insufficient monthly quota"}

    @staticmethod
    def check_feature(user_id: int, feature: str) -> bool:
        """检查功能是否可用（如 diarization, api_access）"""
        sub = QuotaService._ensure_subscription(user_id)
        config = get_plan_config(sub.tier)
        if not config:
            return False
        
        features = config.get("features", {})
        
        # Specific check for export_formats which is a list
        if feature.startswith("export:"):
            fmt = feature.split(":")[1]
            return fmt in features.get("export_formats", [])
            
        return features.get(feature, False)

    @staticmethod
    def deduct_quota(user_id: int, task_id: str, minutes_used: float) -> bool:
        """扣减配额"""
        sub = QuotaService._ensure_subscription(user_id)
        sub.minutes_used += minutes_used
        
        usage = QuotaUsage(
            user_id=user_id,
            task_id=task_id,
            minutes_used=minutes_used
        )
        db.session.add(usage)
        db.session.commit()
        return True

    @staticmethod
    def get_usage_summary(user_id: int) -> dict:
        """返回用量摘要"""
        sub = QuotaService._ensure_subscription(user_id)
        history = QuotaUsage.query.filter_by(user_id=user_id).order_by(QuotaUsage.created_at.desc()).limit(10).all()
        
        total_used = sub.minutes_used
        quota = sub.monthly_minutes_limit
        remaining = quota - total_used if quota != -1 else float('inf')
        
        return {
            "total_used": total_used,
            "quota": quota,
            "remaining": remaining,
            "tier": sub.tier,
            "history": [
                {
                    "task_id": h.task_id,
                    "minutes_used": h.minutes_used,
                    "created_at": h.created_at.isoformat()
                } for h in history
            ]
        }

    @staticmethod
    def reset_monthly_quota(user_id: int) -> bool:
        """重置月度配额（Webhook 触发）"""
        sub = QuotaService._ensure_subscription(user_id)
        sub.minutes_used = 0.0
        db.session.commit()
        return True
