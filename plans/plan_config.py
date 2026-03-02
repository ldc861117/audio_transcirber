import yaml
from app_paths import get_bundle_dir

CONTRACTS_PATH = get_bundle_dir() / "contracts.yaml"

def _load_plan_definitions():
    with open(CONTRACTS_PATH, "r", encoding="utf-8") as f:
        contracts = yaml.safe_load(f)
    return contracts.get("plan_definitions", {})

PLAN_DEFINITIONS = _load_plan_definitions()

def get_plan_config(tier: str) -> dict:
    """
    Returns the configuration for a given plan tier.
    """
    return PLAN_DEFINITIONS.get(tier, {})

def get_all_plans() -> dict:
    """
    Returns all plan definitions.
    """
    return PLAN_DEFINITIONS
