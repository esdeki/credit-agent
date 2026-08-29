# هدف این مرحله فقط ساخت مسیر تصمیم‌گیری است.

class ToolRouter:
    """
    Decide which tool should be used based on user question.
    """

    def decide_tool(self, question):

        question = question.lower()

        if "سابقه" in question or "تاریخچه" in question:
            return "get_company_memory"

        return None
