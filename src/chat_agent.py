from src.llm_service import get_llm_response
from src.knowledge_manager_rag import KnowledgeManager
from src.prompt_builder import build_chat_prompt
from src.memory_manager import MemoryManager
from src.tool_manager import ToolManager
from src.reasoning_engine import ReasoningEngine


SYSTEM_CHAT_PROMPT = """
You are an AI credit analyst assistant working for a bank.

You communicate with credit managers in Persian language.

Your job:
- Answer questions about the analyzed company.
- Use only the provided financial analysis, credit rules, and report.
- Explain financial risks clearly.
- Do not invent information.
- If information is not available, say that it is not available.

Your answers should be:
- In Persian language.
- Professional.
- Concise.
- Suitable for credit managers.
"""


def create_chat_response(
    question,
    context,
    chat_history
):
    """
    Generate conversational answer based on
    current credit analysis context.
    """

    print("CHAT AGENT CALLED")

    tool_manager = ToolManager()

    history_text = ""

    for message in chat_history:

        if message["role"] == "user":
            history_text += f"Manager: {message['content']}\n"
        else:
            history_text += f"AI Credit Analyst: {message['content']}\n"

    memory_manager = MemoryManager()

    previous_memory = (
        memory_manager.get_latest_memory_summary(
            context["company"]
        )
    )

    reasoning_engine = ReasoningEngine()

    initial_context = {
        "company_name": context["company"]
    }

    if context.get("report"):
        initial_context["review_financial_analysis"] = context["analysis"]
        initial_context["check_credit_rules"] = context["rule_result"]

    reasoning_result = reasoning_engine.run_reasoning_loop(
        question,
        tool_manager,
        initial_context=initial_context
    )

    for step_result in reasoning_result["execution_results"]:
        if step_result["result"].get("status") == "error":

            print(
                "REASONING ERROR at step:",
                step_result["step"],
                "-",
                step_result["result"].get("message")
            )

            return (
                "⚠️ اطلاعاتی برای این شرکت در سیستم یافت نشد یا در حین بررسی خطایی رخ داد.\n"
                "لطفاً نام شرکت را بررسی کنید یا مجدداً تلاش نمایید."
            )

    # -------------------------------
    # Knowledge Retrieval
    # -------------------------------

    knowledge_manager = KnowledgeManager()

    if reasoning_result["plan"]["use_knowledge_base"]:
        external_documents = (
            knowledge_manager.get_relevant_documents(
                question
            )
        )
    else:
        external_documents = []

    # لاگ برای تأیید رفتار واقعی RAG
    print(
        f"[RAG] use_knowledge_base={reasoning_result['plan']['use_knowledge_base']} "
        f"-> {len(external_documents)} document(s) retrieved."
    )

    reasoning_context = reasoning_result["context"]

    prompt_context = {
        **context,
        "reasoning_result": reasoning_result,
        "financial_analysis": reasoning_context.get("review_financial_analysis"),
        "credit_rule_evaluation": reasoning_context.get("check_credit_rules"),
        "evaluate_risk": reasoning_context.get("evaluate_risk"),
        "previous_memory": previous_memory,
        "external_documents": external_documents,
    }

    print("Reasoning Result:")
    print(reasoning_result)

    user_prompt = build_chat_prompt(
        question,
        prompt_context,
        history_text,
        previous_memory,
        external_documents
    )

    # -------------------------------
    # LLM Response
    # -------------------------------

    response = get_llm_response(
        SYSTEM_CHAT_PROMPT,
        user_prompt
    )

    # لاگ برای تأیید پاسخ نهایی متنی که واقعاً به کاربر می‌رسد
    print("\n========== FINAL CHAT RESPONSE ==========")
    print(response)
    print("==========================================\n")

    return response
