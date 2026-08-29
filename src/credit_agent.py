import json

from src.llm_service import get_llm_response
from src.prompts import SYSTEM_CREDIT_PROMPT
from src.output_validator import validate_credit_report
from src.exceptions import ReportGenerationError


MAX_ATTEMPTS = 2  # یک تلاش اول + یک تلاش اصلاحی


def _extract_json_text(raw_text):
    """
    گاهی مدل با وجود دستور صریح، خروجی را داخل ```json ``` می‌گذارد
    یا قبل/بعدش توضیح اضافه می‌کند. این تابع تلاش می‌کند
    فقط بخش JSON را از داخل متن خام استخراج کند.
    """

    text = raw_text.strip()

    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()

    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]

    return text


def create_credit_report(company_name, analysis, rule_result, previous_memory, risk_evaluation=None):
    """
    Create structured credit report using LLM.

    اگر خروجی مدل معتبر نباشد (نه JSON درست، یا فیلدی کم داشته باشد)،
    یک‌بار به مدل فرصت اصلاح داده می‌شود. اگر باز هم ناموفق بود،
    یک ReportGenerationError مشخص بالا می‌رود تا لایه‌ی بالاتر (app.py / chat_agent.py)
    آن را با یک پیام تمیز به کاربر نشان دهد، نه با traceback خام.
    """

    risk_hint = ""
    if risk_evaluation:
        risk_hint = f"""
    Pre-calculated deterministic risk level (from credit policy rules):
    {risk_evaluation.get("risk_level")}

    You must use this value as the authoritative risk_level in your JSON output,
    unless the financial analysis strongly contradicts it.
    """

    base_prompt = f"""
Company name:
{company_name}

Company financial analysis:

{analysis}

Credit rules evaluation:

{rule_result}
{risk_hint}

Previous credit memory:

{previous_memory}

Return the credit assessment as JSON only.
"""

    user_prompt = base_prompt
    last_error = None

    for attempt in range(1, MAX_ATTEMPTS + 1):

        response = get_llm_response(
            SYSTEM_CREDIT_PROMPT,
            user_prompt
        )

        cleaned_response = _extract_json_text(response)

        try:
            report = json.loads(cleaned_response)
            validate_credit_report(report)
            return report

        except json.JSONDecodeError as error:
            last_error = f"خروجی مدل JSON معتبر نبود: {error}"

        except ReportGenerationError as error:
            # این همان خطایی است که validate_credit_report می‌زند
            # (فیلد ضروری جا افتاده یا نوع/مقدار نامعتبر)
            last_error = f"خروجی مدل ناقص بود: {error}"

        print(
            f"[credit_agent] تلاش {attempt} ناموفق بود -> {last_error}"
        )

        # برای تلاش بعدی، از خود مدل می‌خواهیم دقیقاً همان خروجی قبلی
        # را با فرمت درست دوباره بنویسد
        user_prompt = f"""
{base_prompt}

توجه: پاسخ قبلی شما نامعتبر بود ({last_error}).
لطفاً این‌بار فقط و فقط یک JSON کاملاً معتبر با تمام فیلدهای زیر برگردانید،
بدون هیچ توضیح، بدون ```json، بدون متن اضافه قبل یا بعد از آن:

{{
    "company": "",
    "decision": "",
    "risk_level": "",
    "confidence_score": 0,
    "executive_summary": "",
    "financial_analysis_detailed": "",
    "trend_analysis": "",
    "article_141_assessment": "",
    "external_risk_assessment": "",
    "credit_policy_compliance": "",
    "strengths": [],
    "weaknesses": [],
    "reasons": [],
    "supporting_factors": [],
    "objection_factors": [],
    "suggested_loan_amount": "",
    "suggested_repayment_months": "",
    "loan_justification": "",
    "recommendations": [],
    "final_notes": ""
}}
"""

    # اگر بعد از همه‌ی تلاش‌ها هنوز موفق نشدیم
    raise ReportGenerationError(
        "تولید گزارش اعتباری با خطا مواجه شد و حتی بعد از یک بار "
        f"تلاش اصلاحی هم موفق نبود. آخرین خطا: {last_error}"
    )
