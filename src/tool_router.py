# هدف این مرحله فقط ساخت مسیر تصمیم‌گیری است.

class ToolRouter:
    """
    Decide which tool should be used based on user question.
    """

    def decide_tool(self, question: str) -> str | None:
        question = question.lower()

        # ۱. ابزار حافظه و سوابق
        if any(w in question for w in ["سابقه", "تاریخچه", "قبلا", "پیشینه"]):
            return "get_company_memory"

        # ۲. ابزار صورت‌های مالی و تحلیل نسبت‌ها
        if any(w in question for w in ["مالی", "نسبت", "نقدینگی", "سود", "زیان", "ترازنامه"]):
            return "review_financial_analysis"

        # ۳. ابزار بررسی قوانین و مقررات اعتباری
        if any(w in question for w in ["قانون", "قوانین", "آیین‌نامه", "شرایط", "حد اعتباری"]):
            return "check_credit_rules"

        # ۴. ابزار ارزیابی ریسک
        if any(w in question for w in ["ریسک", "خطرات", "رتبه‌بندی", "نمره اعتباری"]):
            return "evaluate_risk"

        # ۵. ابزار اطلاعات پایه شرکت
        if any(w in question for w in ["اطلاعات", "شناسنامه", "معرفی", "درباره"]):
            return "load_company_context"

        # اگر هیچ کلمه کلیدی تطبیق نیافت
        return None


"""
توصیه معماری: در سیستم‌های پیشرفته، معمولاً ابتدا یک ToolRouter سریع بر پایه کلمات کلیدی بررسی می‌شود 
و در صورت برگرداندن None، تصمیم‌گیری به مدل هوش مصنوعی 
(ReasoningEngine) واگذار می‌گردد تا با درک معنایی (Semantic Understanding) ابزار مناسب را انتخاب کند.

"""
"""
خلاصه کاربردی:
این کلاس یک «فیلترِ سریع و کم‌هزینه» است. اگر کلمات کلیدی مشخصی را ببیند، بلافاصله آدرس ابزار را می‌دهد تا سیستم معطل نشود؛ اگر نبیند، بدون هیچ خطایی اعلام بی‌اطلاعی 
(None) می‌کند تا بخش‌های هوشمندتر سیستم تصمیم‌گیری را به دست بگیرند.

"""
