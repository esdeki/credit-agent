class ConversationManager:
    """
    Manages the current analysis context and conversation history
    during a single user session.
    """

    def __init__(self):
        self.clear()

    def save_context(
        self,
        company,
        analysis,
        rule_result,
        report
    ):
        """
        Save the latest company analysis context.
        """

        self.context = {
            "company": company,
            "analysis": analysis,
            "rule_result": rule_result,
            "report": report
        }

    def get_context(self):
        """
        Return current analysis context.
        """

        return self.context

    def add_user_message(
        self,
        message
    ):
        """
        Store a user message.
        """

        self.chat_history.append(
            {
                "role": "user",
                "content": message
            }
        )

    def add_assistant_message(
        self,
        message
    ):
        """
        Store an assistant message.
        """

        self.chat_history.append(
            {
                "role": "assistant",
                "content": message
            }
        )

    def get_chat_history(self):
        """
        Return complete chat history.
        """

        return self.chat_history

    def clear_chat_history(self):
        """
        Clear only conversation history.
        """

        self.chat_history = []

    def clear_context(self):
        """
        Clear only current analysis context.
        """

        self.context = {}

    def clear(self):
        """
        Reset entire conversation session.
        """

        self.context = {}
        self.chat_history = []
