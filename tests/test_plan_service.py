import unittest
import os
import sqlite3
from pathlib import Path

# Setup environment before imports
os.environ["SECRET_KEY"] = "test-secret"

# Force test database path
import plans.plan_db
plans.plan_db.DB_PATH = Path("data/test_plans.db")

from services.plan_service import PlanService
from services.quota_service import QuotaService

class TestPlanQuotaService(unittest.TestCase):
    def setUp(self):
        # Use a separate test database
        if plans.plan_db.DB_PATH.exists():
            plans.plan_db.DB_PATH.unlink()
        plans.plan_db.init_db()
        self.user_id = 1

    def tearDown(self):
        if plans.plan_db.DB_PATH.exists():
            plans.plan_db.DB_PATH.unlink()

    def test_default_plan_allocation(self):
        # Should automatically assign free plan when getting user plan for the first time
        plan = PlanService.get_user_plan(self.user_id)
        self.assertEqual(plan["tier"], "free")
        self.assertEqual(plan["monthly_minutes"], 60)
        self.assertEqual(plan["used_minutes"], 0.0)

    def test_subscribe_upgrade(self):
        # Initial plan is free
        PlanService.get_user_plan(self.user_id)
        
        # Upgrade to basic
        success = PlanService.subscribe(self.user_id, "basic")
        self.assertTrue(success)
        
        plan = PlanService.get_user_plan(self.user_id)
        self.assertEqual(plan["tier"], "basic")
        self.assertEqual(plan["monthly_minutes"], 300)

    def test_quota_check_allowed(self):
        # Free plan has 60 minutes
        res = QuotaService.check_quota(self.user_id, 10.0)
        self.assertTrue(res["allowed"])
        self.assertEqual(res["remaining"], 60.0)

    def test_quota_check_insufficient(self):
        # Free plan has 60 minutes, requesting 70 should fail (not exceeding single limit but exceeding monthly)
        # Note: free single limit is 30. So 70 will fail on single limit first if we check it first.
        # Let's use a case where single limit is NOT exceeded but monthly IS.
        # But for free plan single is 30, monthly is 60. Hard to exceed monthly without exceeding single in ONE request.
        # We can deduct some quota first.
        PlanService.get_user_plan(self.user_id)
        QuotaService.deduct_quota(self.user_id, "task-1", 50.0)
        
        # Now used=50, remaining=10. Requesting 20 (less than 30 single limit) should fail on monthly.
        res = QuotaService.check_quota(self.user_id, 20.0)
        self.assertFalse(res["allowed"])
        self.assertEqual(res["error"], "Insufficient monthly quota")

    def test_quota_check_single_limit(self):
        # Free plan max_single_minutes is 30
        res = QuotaService.check_quota(self.user_id, 40.0)
        self.assertFalse(res["allowed"])
        self.assertIn("Single request limit exceeded", res["error"])

    def test_quota_deduction(self):
        # Ensure user exists
        PlanService.get_user_plan(self.user_id)
        QuotaService.deduct_quota(self.user_id, "task-123", 5.5)
        
        summary = QuotaService.get_usage_summary(self.user_id)
        self.assertEqual(summary["total_used"], 5.5)
        self.assertEqual(summary["remaining"], 54.5)
        self.assertEqual(len(summary["history"]), 1)
        self.assertEqual(summary["history"][0]["task_id"], "task-123")
        self.assertEqual(summary["history"][0]["minutes_used"], 5.5)

    def test_pro_plan_unlimited(self):
        PlanService.subscribe(self.user_id, "pro")
        
        # Pro has monthly_minutes = -1 (unlimited)
        res = QuotaService.check_quota(self.user_id, 1000.0)
        self.assertTrue(res["allowed"])
        self.assertEqual(res["remaining"], float('inf'))

if __name__ == "__main__":
    unittest.main()
