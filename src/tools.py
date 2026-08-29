"""
Agent Tools

This file contains tools exposed to the AI Agent.

Architecture:

ReasoningEngine
        |
        v
ToolManager
        |
        v
Tools Wrapper
        |
        v
Business Services
"""

from src.memory_manager import MemoryManager

from src.data_loader import load_financial_data
from src.company_service import get_company_data
from src.financial_analyzer import analyze_company
from src.credit_rules import evaluate_credit_rules
from src.credit_agent import create_credit_report


# ==================================================
# Memory Tool
# ==================================================

def get_company_memory_tool(
    company_name=None,
    **kwargs
):
    """
    Retrieve previous company memory.
    """

    if not company_name:
        return "شرکتی مشخص نشده است."

    memory_manager = MemoryManager()

    return memory_manager.get_latest_memory_summary(
        company_name
    )


# ==================================================
# Load Company Context Tool
# ==================================================

def load_company_context_tool(
    company_name=None,
    **kwargs
):
    """
    Load raw company financial data.
    """

    if not company_name:
        raise ValueError(
            "company_name is required"
        )

    df = load_financial_data()

    company_data = get_company_data(
        df,
        company_name
    )

    return company_data


# ==================================================
# Financial Analysis Tool
# ==================================================

def financial_analysis_tool(
    load_company_context=None,
    **kwargs
):
    """
    Analyze financial information.

    Input: load_company_context (output of load_company_context step)
    """

    if load_company_context is None:
        raise ValueError(
            "load_company_context is required"
        )

    return analyze_company(
        load_company_context
    )


# ==================================================
# Credit Rules Tool
# ==================================================

def credit_rule_check_tool(
    review_financial_analysis=None,
    **kwargs
):
    """
    Evaluate credit rules.

    Input: review_financial_analysis (output of review_financial_analysis step)
    """

    if review_financial_analysis is None:
        raise ValueError(
            "review_financial_analysis is required"
        )

    return evaluate_credit_rules(
        review_financial_analysis
    )


# ==================================================
# Risk Evaluation Tool
# ==================================================

def evaluate_risk_tool(
    check_credit_rules=None,
    **kwargs
):
    """
    Convert credit rules result into risk level.

    Input: check_credit_rules (output of check_credit_rules step)
    """

    if check_credit_rules is None:
        return {
            "risk_level": "Unknown"
        }

    risk = "Medium"

    if isinstance(check_credit_rules, dict):

        values = check_credit_rules.values()

        if all(
            value == "acceptable"
            for value in values
        ):
            risk = "Low"

        elif any(
            value in ["weak", "high"]
            for value in values
        ):
            risk = "High"

    return {
        "risk_level": risk
    }


# ==================================================
# Generate Credit Answer Tool
# ==================================================

def generate_credit_report_tool(
    company_name=None,
    review_financial_analysis=None,
    check_credit_rules=None,
    get_company_memory=None,
    evaluate_risk=None,
    **kwargs
):
    """
    Generate final credit report using LLM.
    Consumes all relevant context outputs.
    """

    if not company_name:
        raise ValueError(
            "company_name is required"
        )

    if evaluate_risk is None:
        evaluate_risk = evaluate_risk_tool(
            check_credit_rules
        )

    return create_credit_report(
        company_name,
        review_financial_analysis,
        check_credit_rules,
        get_company_memory,
        evaluate_risk
    )
