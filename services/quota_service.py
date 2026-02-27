from plans import plan_db, plan_config
from services.plan_service import PlanService

class QuotaService:
    @staticmethod
    def check_quota(user_id: int, estimated_minutes: float) -> dict:
        """
        返回 {"allowed": bool, "remaining": float, "plan": str}
        """
        user_plan = PlanService.get_user_plan(user_id)
        tier = user_plan["tier"]
        monthly_limit = user_plan["monthly_minutes"]
        used = user_plan["used_minutes"]
        
        config = plan_config.get_plan_config(tier)
        max_single = config.get("max_single_minutes", -1)
        
        # Check single request limit
        if max_single != -1 and estimated_minutes > max_single:
            return {
                "allowed": False, 
                "remaining": monthly_limit - used if monthly_limit != -1 else float('inf'), 
                "plan": tier,
                "error": f"Single request limit exceeded: {max_single} minutes"
            }
            
        # Check monthly limit
        if monthly_limit == -1: # Unlimited
            return {"allowed": True, "remaining": float('inf'), "plan": tier}
        
        remaining = monthly_limit - used
        if remaining >= estimated_minutes:
            return {"allowed": True, "remaining": remaining, "plan": tier}
        else:
            return {"allowed": False, "remaining": remaining, "plan": tier, "error": "Insufficient monthly quota"}

    @staticmethod
    def deduct_quota(user_id: int, task_id: str, minutes_used: float) -> bool:
        """扣减配额"""
        plan_db.update_used_minutes(user_id, minutes_used)
        plan_db.add_quota_usage(user_id, task_id, minutes_used)
        return True

    @staticmethod
    def get_usage_summary(user_id: int) -> dict:
        """
        返回 {"total_used": float, "quota": int, "remaining": float, "history": [...]}
        """
        user_plan = PlanService.get_user_plan(user_id)
        history = plan_db.get_quota_usage_history(user_id)
        
        total_used = user_plan["used_minutes"]
        quota = user_plan["monthly_minutes"]
        remaining = quota - total_used if quota != -1 else float('inf')
        
        return {
            "total_used": total_used,
            "quota": quota,
            "remaining": remaining,
            "history": [dict(h) for h in history]
        }
