from enum import Enum
from src.data_loader import load_financial_data
from src.llm_service import get_llm_response


class UserIntent(Enum):
    """
    Types of questions that credit analyst agent can handle.
    """

    CREDIT_ASSESSMENT = "credit_assessment"
    FINANCIAL_ANALYSIS = "financial_analysis"
    COMPANY_INFORMATION = "company_information"
    CREDIT_POLICY = "credit_policy"
    GENERAL_QUESTION = "general_question"


class ReasoningEngine:
    """
    Responsible for:

    1. Detecting user intent
    2. Creating execution plan
    3. Preparing tool inputs
    4. Running reasoning loop

    This layer does NOT execute business logic.

    It only coordinates:

    ReasoningEngine
            |
            v
       ToolManager
            |
            v
          Tools
            |
            v
       Business Services
    """

    def __init__(self):
        pass

    # ==================================================
    # Intent Detection (LLM-based, with keyword fallback)
    # ==================================================

    INTENT_SYSTEM_PROMPT = """
You are an intent classifier for a bank credit-analysis assistant.
The user (a bank credit manager) writes a question in Persian.

Classify the question into EXACTLY one of these categories:
- credit_assessment   (loan/credit decision, risk approval or rejection)
- financial_analysis  (financial ratios, balance sheet, profit, debt figures)
- credit_policy       (bank rules, regulations, policy thresholds)
- company_information (general info about a company)
- general_question    (anything else, small talk, unclear)

Rules:
- Return ONLY the category label exactly as written above.
- No explanation. No punctuation. No JSON. No extra words.
"""

    def detect_intent_llm(self, question):
        """
        Ask the LLM to classify intent. Raises on failure
        so the caller can fall back to keyword detection.
        """

        response = get_llm_response(
            self.INTENT_SYSTEM_PROMPT,
            question
        )

        response = response.strip().lower()

        for intent in UserIntent:
            if intent.value in response:
                return intent

        raise ValueError(
            f"LLM returned an unrecognized intent label: '{response}'"
        )

    def detect_intent_keywords(self, question):
        """
        Fallback intent detection based on keyword scoring.
        Used only if the LLM call fails.
        """

        question = question.lower()

        credit_keywords = [
            "وام",
            "اعتبار",
            "تسهیلات",
            "ریسک",
            "پرداخت",
            "تایید",
            "رد"
        ]

        financial_keywords = [
            "نسبت",
            "بدهی",
            "دارایی",
            "صورت مالی",
            "ترازنامه",
            "سود"
        ]

        policy_keywords = [
            "قانون",
            "سیاست",
            "ضابطه",
            "حد مجاز"
        ]

        credit_score = sum(
            1 for word in credit_keywords if word in question
        )

        financial_score = sum(
            1 for word in financial_keywords if word in question
        )

        policy_score = sum(
            1 for word in policy_keywords if word in question
        )

        scores = {
            UserIntent.CREDIT_ASSESSMENT: credit_score,
            UserIntent.FINANCIAL_ANALYSIS: financial_score,
            UserIntent.CREDIT_POLICY: policy_score,
        }

        max_score = max(scores.values())

        if max_score == 0:
            return UserIntent.COMPANY_INFORMATION

        for intent in (
            UserIntent.CREDIT_ASSESSMENT,
            UserIntent.FINANCIAL_ANALYSIS,
            UserIntent.CREDIT_POLICY,
        ):
            if scores[intent] == max_score:
                return intent

        return UserIntent.COMPANY_INFORMATION

    def detect_intent(self, question):
        """
        Primary intent detection entry point.

        Tries LLM-based classification first (understands meaning,
        not just keyword overlap). Falls back to keyword scoring
        if the LLM call fails for any reason (network, bad response).
        """

        try:
            return self.detect_intent_llm(question)

        except Exception as error:
            print(
                "LLM intent detection failed, falling back to keywords:",
                error
            )
            return self.detect_intent_keywords(question)

    # ==================================================
    # Company Extraction
    # ==================================================

    def get_all_company_names(self):
        """
        لیست واقعی و به‌روز شرکت‌ها را مستقیم از داده بخوان،
        نه از یک لیست ثابت داخل کد.
        """
        df = load_financial_data()
        return df["Company_Name"].dropna().unique().tolist()

    def extract_company_name(self, question):

        companies = self.get_all_company_names()
        question_lower = question.lower()

        for company in companies:
            if str(company).lower() in question_lower:
                return company

        return None

    # ==================================================

    # Create Plan
    # ==================================================

    def create_plan(self, question):
        """
        تصمیم طراحی آگاهانه:

        برنامه‌ی CREDIT_ASSESSMENT عمداً شامل step
        "generate_credit_answer" نمی‌شود. آن step یک گزارش کامل
        ۲۰-فیلدی JSON با SYSTEM_CREDIT_PROMPT تولید می‌کند (همان
        منطق سنگین دکمه‌ی Analyze Credit)، درحالی‌که chat_agent.py
        خودش با SYSTEM_CHAT_PROMPT یک پاسخ مکالمه‌ای سبک‌تر می‌سازد.

        اگر این step به این برنامه اضافه شود:
        1) یک فراخوانی سنگین و غیرضروری مدل اضافه می‌شود،
        2) طبق evaluate_step_result حلقه بلافاصله بعد از این step
           متوقف می‌شود ("finish")، پس step بعدی (get_company_memory)
           اصلاً اجرا نخواهد شد.

        پس این حذف عمدی است، نه فراموشی — اگر روزی خواستی این
        رفتار را تغییر بدهی، همین کامنت را هم به‌روزرسانی کن.
        """

        intent = self.detect_intent(question)

        if intent == UserIntent.CREDIT_ASSESSMENT:

            steps = [

                "load_company_context",

                "review_financial_analysis",

                "check_credit_rules",

                "evaluate_risk",

                "get_company_memory"

            ]

        elif intent == UserIntent.FINANCIAL_ANALYSIS:

            steps = [

                "load_company_context",

                "review_financial_analysis"

            ]

        elif intent == UserIntent.CREDIT_POLICY:

            steps = [

                "load_company_context",

                "check_credit_rules",

                "generate_policy_answer"

            ]

        else:

            steps = [

                "load_company_context"

            ]

        use_knowledge_base = intent in (
            UserIntent.CREDIT_POLICY,
            UserIntent.GENERAL_QUESTION
        )

        return {

            "intent": intent.value,

            "steps": steps,

            "use_knowledge_base": use_knowledge_base

        }

    # ==================================================
    # Prepare Tool Input
    # ==================================================

    def prepare_tool_input(
        self,
        step,
        context
    ):
        """
        ابزارها در tools.py خودشان با signature و fallback=None
        مشخص کرده‌اند چه ورودی‌هایی می‌پذیرند.
        پس نیازی نیست اینجا mapping دستی تکرار شود؛
        کل context پاس داده می‌شود تا هر ابزار چیز مورد نیازش را بردارد.
        """
        return context

    # ==================================================
    # Result Evaluation
    # ==================================================

    def evaluate_step_result(
        self,
        step,
        result
    ):

        if isinstance(result, dict):

            if result.get(
                "status"
            ) == "error":

                return "break"

        if step in ("generate_credit_answer", "generate_policy_answer"):

            return "finish"

        return "continue"

    # ==================================================
    # Adaptive Plan Adjustment
    # ==================================================

    def adjust_plan(self, plan, context, last_step, last_result):
        """
        Dynamically adjust remaining steps based on execution results.
        Can insert, skip, or reorder steps. Override to add logic.
        """
        pass

    # ==================================================
    # Reasoning Loop
    # ==================================================

    def run_reasoning_loop(
        self,
        question,
        tool_manager,
        initial_context=None
    ):

        plan = self.create_plan(question)

        print(
            "\n========== REASONING TRACE =========="
        )

        print(
            "\nQuestion:"
        )

        print(question)

        print(
            "\nPlan:"
        )

        print(plan)

        context = {
            "question": question,
        }

        if initial_context:
            context.update(initial_context)

        if "company_name" not in context:
            context["company_name"] = self.extract_company_name(question)

        results = []

        MAX_STEPS = 15  # محافظ ایمنی در برابر رشد بی‌پایان plan["steps"]

        for step in plan["steps"]:

            if len(results) >= MAX_STEPS:
                print("Reasoning Stopped: Max step limit reached.")
                break

            if step in context and context[step] is not None:

                print(f"Skipping '{step}': using cached value from context.")

                cached_result = {
                    "status": "success",
                    "tool": step,
                    "result": context[step],
                    "cached": True
                }

                results.append({"step": step, "result": cached_result})

                status = self.evaluate_step_result(step, cached_result)

                print("Status:", status, "(cached)")

                if status == "finish":
                    print("Reasoning Finished.")
                    break

                if status == "break":
                    print("Reasoning Stopped Due To Error.")
                    break

                self.adjust_plan(plan, context, step, cached_result)
                continue

            print(
                "\n----------------------------"
            )

            print(
                "Executing:",
                step
            )

            tool_input = self.prepare_tool_input(
                step,
                context
            )

            result = tool_manager.run_tool(
                step,
                **tool_input
            )

            print(
                "Result:"
            )

            print(result)

            results.append(

                {
                    "step": step,
                    "result": result
                }

            )

            if isinstance(result, dict):

                if (
                    result.get("status")
                    == "success"
                    and
                    "result" in result
                ):

                    context[step] = result["result"]

                else:

                    context[step] = result

            else:

                context[step] = result

            print(
                "Context Keys:"
            )

            print(
                context.keys()
            )

            status = self.evaluate_step_result(
                step,
                result
            )

            print(
                "Status:",
                status
            )

            if status == "finish":

                print(
                    "Reasoning Finished."
                )

                break

            if status == "break":

                print(
                    "Reasoning Stopped Due To Error."
                )

                break

            self.adjust_plan(plan, context, step, result)

        print(
            "\n========== END TRACE =========="
        )

        return {

            "intent":
                plan["intent"],

            "plan":
                plan,

            "context":
                context,

            "execution_results":
                results

        }
