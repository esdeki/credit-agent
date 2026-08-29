from src.data_loader import load_financial_data
from src.company_service import get_company_data
from src.financial_analyzer import analyze_company
from src.credit_rules import evaluate_credit_rules
from src.credit_agent import create_credit_report
from src.conversation_manager import ConversationManager
from src.memory_manager import MemoryManager


# ==================================================
# Reusable Business Logic Steps
# (Used by both credit_pipeline and reasoning tools)
# ==================================================

def load_company_context(company_name):
    """بارگذاری داده‌های خام شرکت از فایل."""
    df = load_financial_data()
    return get_company_data(df, company_name)


def review_financial_analysis(load_company_context):
    """تحلیل صورت‌های مالی شرکت."""
    return analyze_company(load_company_context)


def check_credit_rules(review_financial_analysis):
    """ارزیابی قوانین اعتباری روی تحلیل."""
    return evaluate_credit_rules(review_financial_analysis)


def evaluate_risk(check_credit_rules):
    """
    ارزیابی ریسک بر اساس نتایج موتور قواعد اعتباری.
    خروجی استاندارد با میدان risk_level فراهم می‌کند.
    """

    risk_level = "Unknown"

    if isinstance(check_credit_rules, dict) and check_credit_rules:
        results = list(check_credit_rules.values())

        if all(value == "acceptable" for value in results):
            risk_level = "Low"
        elif any(value in ("weak", "high") for value in results):
            risk_level = "High"
        else:
            risk_level = "Medium"
    else:
        risk_level = "Medium"

    return {
        "risk_level": risk_level,
        "source": "credit_rules"
    }


def get_company_memory(company_name):
    """بازیابی حافظه‌ی قبلی مربوط به شرکت."""
    return MemoryManager().get_company_memory(company_name)


def generate_credit_answer(
    company_name,
    review_financial_analysis,
    check_credit_rules,
    get_company_memory,
    evaluate_risk=None
):
    """تولید گزارش نهایی اعتباری."""
    return create_credit_report(
        company_name,
        review_financial_analysis,
        check_credit_rules,
        get_company_memory,
        evaluate_risk
    )


# ==================================================
# Full Pipeline Orchestrator
# ==================================================

def run_credit_analysis(
    company_name,
    conversation_manager,
    run_id=None,
    allow_persistence=False
):
    """
    اجرای کامل پایپ‌لاین اعتبارسنجی بدون ذخیره‌سازی مستقیم در حافظه.
    نتیجه شامل داده‌های تحلیلی، خروجی موتور قواعد و پیشنهاد ذخیره‌سازی است.
    """

    memory_manager = MemoryManager()

    company_data = load_company_context(company_name)

    analysis = review_financial_analysis(company_data)

    rule_result = check_credit_rules(analysis)

    risk_evaluation = evaluate_risk(rule_result)

    previous_memory = memory_manager.get_latest_memory_summary(company_name)

    report = generate_credit_answer(
        company_name=company_name,
        review_financial_analysis=analysis,
        check_credit_rules=rule_result,
        get_company_memory=previous_memory,
        evaluate_risk=risk_evaluation
    )

    conversation_manager.save_context(
        company_name,
        analysis,
        rule_result,
        report,
        risk_evaluation=risk_evaluation
    )

    return {
        "analysis": analysis,
        "report": report,
        "rule_result": rule_result,
        "risk_evaluation": risk_evaluation,
        "previous_memory": previous_memory,
        "run_id": run_id
    }
