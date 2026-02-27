from plans import plan_db, plan_config

class PlanService:
    @staticmethod
    def get_user_plan(user_id: int) -> dict:
        """返回当前 Plan + 用量"""
        row = plan_db.get_user_plan(user_id)
        if not row:
            # 自动分配 free plan
            config = plan_config.get_plan_config("free")
            plan_db.upsert_user_plan(
                user_id, 
                "free", 
                config.get("monthly_minutes", 60)
            )
            row = plan_db.get_user_plan(user_id)
        
        return dict(row)

    @staticmethod
    def subscribe(user_id: int, tier: str) -> bool:
        """订阅/升级"""
        config = plan_config.get_plan_config(tier)
        if not config:
            return False
        
        plan_db.upsert_user_plan(
            user_id,
            tier,
            config.get("monthly_minutes", 0)
        )
        return True

    @staticmethod
    def get_available_plans() -> list[dict]:
        """所有可用 Plan"""
        all_plans = plan_config.get_all_plans()
        result = []
        for tier, config in all_plans.items():
            plan_info = {"tier": tier}
            plan_info.update(config)
            result.append(plan_info)
        return result
