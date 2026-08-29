import json
from pathlib import Path


def load_credit_policy():
    """
    Load credit policy configuration.
    """
    policy_path = Path(__file__).parent.parent / \
        "config" / "credit_policy.json"

    with open(policy_path, "r", encoding="utf-8") as file:
        policy = json.load(file)

    return policy


def evaluate_credit_rules(analysis):
    """
    Evaluate financial metrics based on credit policy.
    """

    policy = load_credit_policy()

    results = {}

    if analysis["Current_Ratio_Average"] >= policy["current_ratio_min"]:
        results["Current_Ratio"] = "acceptable"
    else:
        results["Current_Ratio"] = "weak"

    if analysis["Debt_Ratio_Average"] <= policy["debt_ratio_max"]:
        results["Debt_Ratio"] = "acceptable"
    else:
        results["Debt_Ratio"] = "high"

    if analysis["Quick_Ratio_Average"] >= policy["quick_ratio_min"]:
        results["Quick_Ratio"] = "acceptable"
    else:
        results["Quick_Ratio"] = "weak"

    return results
