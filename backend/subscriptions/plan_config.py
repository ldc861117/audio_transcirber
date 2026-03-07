# Plan definitions following SHARED_CONTRACTS_V2.md Section 6
PLAN_DEFINITIONS = {
    "free": {
        "display_name": "免费版",
        "price_monthly_cents": 0,
        "price_yearly_cents": 0,
        "stripe_price_id_monthly": None,
        "stripe_price_id_yearly": None,
        "monthly_minutes": 60,
        "max_single_minutes": 30,
        "max_file_size_mb": 50,
        "features": {
            "diarization": False,
            "export_formats": ["txt", "md"],
            "priority_queue": False,
            "api_access": False,
        }
    },
    "basic": {
        "display_name": "基础版",
        "price_monthly_cents": 2900,
        "price_yearly_cents": 29000,
        "stripe_price_id_monthly": "price_basic_monthly",  # Example IDs
        "stripe_price_id_yearly": "price_basic_yearly",
        "monthly_minutes": 300,
        "max_single_minutes": 120,
        "max_file_size_mb": 200,
        "features": {
            "diarization": True,
            "export_formats": ["txt", "md", "srt"],
            "priority_queue": False,
            "api_access": False,
        }
    },
    "pro": {
        "display_name": "专业版",
        "price_monthly_cents": 9900,
        "price_yearly_cents": 99000,
        "stripe_price_id_monthly": "price_pro_monthly",
        "stripe_price_id_yearly": "price_pro_yearly",
        "monthly_minutes": -1, # -1 means unlimited
        "max_single_minutes": -1,
        "max_file_size_mb": 500,
        "features": {
            "diarization": True,
            "export_formats": ["txt", "md", "srt", "docx", "pdf"],
            "priority_queue": True,
            "api_access": True,
        }
    }
}

PLAN_ORDER = ["free", "basic", "pro"]

def get_plan_config(tier: str) -> dict | None:
    """Returns the configuration for a given plan tier."""
    return PLAN_DEFINITIONS.get(tier)

def get_all_plans() -> dict:
    """Returns all plan definitions."""
    return PLAN_DEFINITIONS

def get_plan_order() -> list:
    """Returns the ordered list of plan tiers."""
    return PLAN_ORDER

def is_tier_gte(tier_a: str, tier_b: str) -> bool:
    """Checks if tier_a is greater than or equal to tier_b."""
    try:
        index_a = PLAN_ORDER.index(tier_a)
        index_b = PLAN_ORDER.index(tier_b)
        return index_a >= index_b
    except ValueError:
        return False
