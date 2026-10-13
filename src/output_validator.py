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


"""
جمع‌بندی: آیا این کد کافی است؟
کدی که نوشتید برای لایه اول پایش (فرمت و ساختار JSON) ضروری و عالی است، اما برای تصمیم‌گیری اعتباری کاملاً کافی نیست.

در سیستم‌های اعتبارسنجی پیشرفته مبتنی بر ایجنت، معمولاً دو لایه مکمل اضافه می‌کنند:

قوانین سخت‌گیرانه متنی و منطقی (Deterministic Rules): مثل چک کردن حداقل طول متون و عدم پذیرش لیست‌های خالی.

یک ایجنت منتقد (Critic Agent / Evaluator): یک ایجنت کوچک‌تر و سریع‌تر که وظیفه‌اش چک کردن تناقضات منطقی است (مثلاً: "آیا با توجه به این دلایل، تصمیم به تایید منطقی است یا خیر؟").
"""

"""
نقاط ضعف و منفذهای خطا (چرا ۲.۵ نمره کم شد؟)
این کد نمی‌تواند جلوی ۴ دسته از خطاهای رایج LLM را بگیرد:

متن‌های پوچ اما معتبر از نظر جنس (Empty/Whitespace Strings):

برای فیلد company و decision شرط .strip() گذاشته شده تا خالی نباشند، اما برای فیلدهای متنی دیگر مثل executive_summary یا financial_analysis_detailed فقط چک شده که str باشند.

خطای احتمالی: اگر LLM برای یک فیلد متنی مقدار "" (رشته خالی) یا " " بفرستد، این کد آن را رد نمی‌کند و گزارشِ ناقص رد می‌شود.

لیست‌های خالی (Empty Lists):

برای فیلدهایی مثل strengths یا weaknesses چک شده که list باشند، اما طول لیست (len > 0) بررسی نشده است.

خطای احتمالی: اگر LLM یک لیست خالی [] بفرستد، کد آن را کاملاً صحیح تلقی می‌کند.

تناقضات منطقی و محتوایی (Semantic Contradictions):

این کد فقط ظاهر داده را می‌سنجد نه مفهوم آن را.

خطای احتمالی: اگر LLM تصمیم را "تایید" بزند، اما در فیلد reasons بنویسد "شرکت ورشکسته است و نباید وام بگیرد"، این کد متوجه تناقض بین تصمیم و دلایل نمی‌شود.

عدم تطابق اعداد پیشنهادی (Data Consistency):

فیلدهای suggested_loan_amount و suggested_repayment_months به عنوان str تعریف شده‌اند. اگر LLM به‌جای عدد، متنی مثل "نامشخص" بفرستد یا مبلغی منفی پیشنهاد دهد، کد مانع آن نمی‌شود.
"""


"""
تأثیر این ۴ دسته خطا بر تصمیم اعتباری به شرح زیر است:

۱. تناقضات منطقی و محتوایی (بسیار حیاتی / ریسک بالا)
درجه اهمیت: 🔥 بحرانی (Critical)

تأثیر در تصمیم اعتباری: اگر LLM در بخش تحلیل مالی نوشتارهای منفی تولید کند (مثلاً: "نسبت بدهی شرکت بحرانی است" یا "شرکت مشمول ماده ۱۴۱ قانون تجارت شده")، اما در فیلد تصمیم نهایی به اشتباه مقدار "تایید" یا "تایید مشروط" را بگذارد، کد فعلی بدون هیچ اشکالی گزارش را صادر می‌کند!

نتیجه: پرداخت تسهیلات مالی به شرکتی پرریسک، صرفاً به دلیل یک خطای منطقی/هالوژنیشن (Hallucination) در هوش مصنوعی.

۲. متون پوچ یا خالی بودن فیلدهای توضیحی (حیاتی)
درجه اهمیت: ⚠️ بالا (High)

تأثیر در تصمیم اعتباری: تصمیمات اعتباری نیاز به «توجیه حقوقی و مالی» دارند. اگر فیلدی مثل executive_summary یا loan_justification به صورت یک رشته خالی ("") یا فقط چند فاصله برگردد:

نتیجه: گزارش نهایی وارد کمیته اعتبار می‌شود اما هیچ پرونده یا مستند تحلیلی برای دفاع از آن تصمیم وجود ندارد. کمیته مجبور می‌شود کل فرآیند ارزیابی را مجددا انجام دهد که باعث اتلاف وقت و اعتبار سیستم می‌شود.

۳. عدم تطابق عددی در مبالغ و اقساط (حیاتی)
درجه اهمیت: ⚠️ بالا (High)

تأثیر در تصمیم اعتباری: فیلدهای suggested_loan_amount و suggested_repayment_months به صورت رشته متنی (str) دریافت می‌شوند. اگر مدل به جای عدد، عبارتی مثل "مطابق با آیین‌نامه" یا یک عدد منفی بفرستد، کد آن را رد نمیکند.

نتیجه: زمانی که سیستم‌های پایپ‌لاین بعدی (مثلاً سیستم صدور قرارداد یا پایگاه‌داده) بخواهند این ارزش را پردازش کنند، کل برنامه با خطای محاسباتی متوقف می‌شود یا رقم پیشنهادی غیراستانداردی در پرونده ذخیره می‌گردد.

۴. لیست‌های خالی (متوسط تا بالا)
درجه اهمیت: 🔸 متوسط (Medium)

تأثیر در تصمیم اعتباری: فیلدهایی مثل weaknesses (نقاط ضعف) یا reasons (دلایل) جهت شفاف‌سازیِ ریسک هستند. اگر این لیست‌ها خالی ([]) برگردند، ارزیاب انسانی یا سیستم بالادستی نمی‌داند که آیا شرکت هیچ نقطه ضعفی نداشته یا مدل فراموش کرده آن‌ها را بنویسد.

نتیجه: عدم شفافیت در تحلیل ریسک و ایجاد تصویر غلط از وضعیت ریسک‌پذیری مشتری.
"""
