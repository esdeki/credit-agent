def build_chat_prompt(
    question,
    context,
    history_text,
    memory,
    knowledge
):
    """
    Build the complete user prompt for the Chat Agent.
    """

    return f"""
Current credit analysis:

{context}


Previous conversation:

{history_text}


Long-term memory:

{memory}


External knowledge:

{knowledge}


Manager question:

{question}
"""
