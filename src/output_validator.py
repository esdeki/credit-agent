from src.exceptions import ReportGenerationError

REQUIRED_FIELDS = [
    "company",
    "decision",
    "risk_level",
    "confidence_score",
    "executive_summary",
    "financial_analysis_detailed",
    "trend_analysis",
    "article_141_assessment",
    "external_risk_assessment",
    "credit_policy_compliance",
    "strengths",
    "weaknesses",
    "reasons",
    "supporting_factors",
    "objection_factors",
    "suggested_loan_amount",
    "suggested_repayment_months",
    "loan_justification",
    "recommendations",
    "final_notes"
]

VALID_RISK_LEVELS = {"low", "medium", "high"}

# نکته: "تایید مشروط" و "ارجاع به کمیته" باید قبل از "تایید" و "رد"
# در normalize_decision چک شوند، چون این دو مقدارِ کوتاه‌تر
# زیرمجموعه‌ی متن مقادیر دیگر هم می‌توانند باشند.
VALID_DECISIONS = ["تایید مشروط", "ارجاع به کمیته", "تایید", "رد"]


def normalize_decision(value):
    """
    اگر مقدار دقیقاً یکی از گزینه‌های مجاز نبود،
    تلاش می‌کند از داخل متن، نزدیک‌ترین گزینه‌ی معتبر را استخراج کند.
    مثال: "رد درخواست اعتبار" -> "رد"
    """
    value = value.strip()

    if value in VALID_DECISIONS:
        return value

    for option in VALID_DECISIONS:
        if option in value:
            return option

    return value  # اگر هیچ تطابقی نبود، همان مقدار خام برمی‌گردد تا زیر رد شود


def normalize_confidence_score(value):
    """
    مدل گاهی این عدد را به‌صورت رشته ("85")، اعشاری صحیح (85.0)،
    یا در مقیاس کسری بین 0 و 1 (0.65 به‌جای 65) برمی‌گرداند.
    این تابع تلاش می‌کند همه‌ی این حالت‌ها را به یک int بین 0 تا 100 تبدیل کند.
    """
    if isinstance(value, bool):
        # bool زیرمجموعه‌ی int است ولی معنای منطقی متفاوتی دارد
        raise ReportGenerationError(
            f"Field 'confidence_score' must be an integer, got boolean: {value}"
        )

    if isinstance(value, str):
        stripped = value.strip()
        if stripped.replace(".", "", 1).isdigit():
            value = float(stripped) if "." in stripped else int(stripped)
        else:
            raise ReportGenerationError(
                f"Field 'confidence_score' must be an integer, got: '{value}'"
            )

    if isinstance(value, float):
        # مقیاس کسری 0 تا 1 -> تبدیل به مقیاس 0 تا 100
        if 0 <= value <= 1:
            return round(value * 100)
        if value.is_integer():
            return int(value)
        raise ReportGenerationError(
            f"Field 'confidence_score' must be an integer, got: '{value}'"
        )

    if isinstance(value, int):
        return value

    raise ReportGenerationError(
        f"Field 'confidence_score' must be an integer, got: '{value}'"
    )


def validate_credit_report(report):
    """
    Validate structured output from credit agent.
    Checks existence, type, and value constraints.
    """

    # 1. Existence check
    missing_fields = [
        field for field in REQUIRED_FIELDS
        if field not in report
    ]

    if missing_fields:
        raise ReportGenerationError(
            f"Missing required fields: {missing_fields}"
        )

    # 2. Type & value checks
    if not isinstance(report["company"], str) or not report["company"].strip():
        raise ReportGenerationError(
            "Field 'company' must be a non-empty string.")

    if not isinstance(report["decision"], str) or not report["decision"].strip():
        raise ReportGenerationError(
            "Field 'decision' must be a non-empty string.")

    report["decision"] = normalize_decision(report["decision"])

    if report["decision"] not in VALID_DECISIONS:
        raise ReportGenerationError(
            f"Field 'decision' must be one of {set(VALID_DECISIONS)}, "
            f"got: '{report['decision']}'"
        )

    if not isinstance(report["risk_level"], str):
        raise ReportGenerationError("Field 'risk_level' must be a string.")
    if report["risk_level"].lower() not in VALID_RISK_LEVELS:
        raise ReportGenerationError(
            f"Field 'risk_level' must be one of {VALID_RISK_LEVELS}, "
            f"got: '{report['risk_level']}'"
        )

    report["confidence_score"] = normalize_confidence_score(
        report["confidence_score"]
    )
    if not (0 <= report["confidence_score"] <= 100):
        raise ReportGenerationError(
            "Field 'confidence_score' must be between 0 and 100."
        )

    for field in ("executive_summary", "financial_analysis_detailed",
                  "trend_analysis", "article_141_assessment",
                  "external_risk_assessment", "credit_policy_compliance",
                  "suggested_loan_amount", "suggested_repayment_months",
                  "loan_justification", "final_notes"):
        if not isinstance(report[field], str):
            raise ReportGenerationError(f"Field '{field}' must be a string.")

    for field in ("strengths", "weaknesses", "reasons",
                  "supporting_factors", "objection_factors", "recommendations"):
        if not isinstance(report[field], list):
            raise ReportGenerationError(f"Field '{field}' must be a list.")
        if not all(isinstance(item, str) for item in report[field]):
            raise ReportGenerationError(
                f"All items in '{field}' must be strings.")

    return True
