from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from services.plan_service import PlanService
from services.quota_service import QuotaService

plan_bp = Blueprint("plans", __name__, url_prefix="/api/v1/plans")

@plan_bp.route("/", methods=["GET"])
@login_required
def list_plans():
    """可用 Plan 列表"""
    plans = PlanService.get_available_plans()
    return jsonify(plans)

@plan_bp.route("/me", methods=["GET"])
@login_required
def get_my_plan():
    """当前用户 Plan & 用量余额"""
    plan = PlanService.get_user_plan(current_user.id)
    return jsonify(plan)

@plan_bp.route("/subscribe", methods=["POST"])
@login_required
def subscribe():
    """订阅/升级 {"tier": "basic"}"""
    data = request.json or {}
    tier = data.get("tier")
    if not tier:
        return jsonify({"error": "Missing tier"}), 400
    
    success = PlanService.subscribe(current_user.id, tier)
    if success:
        return jsonify({"ok": True})
    else:
        return jsonify({"error": "Invalid tier or subscription failed"}), 400

@plan_bp.route("/usage", methods=["GET"])
@login_required
def get_usage():
    """用量历史"""
    summary = QuotaService.get_usage_summary(current_user.id)
    return jsonify(summary)
