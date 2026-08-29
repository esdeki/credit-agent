"""
ToolManager

Central registry and executor for Agent Tools.

Architecture:

Reasoning Engine
        |
        | step name
        ↓
ToolManager
        |
        | tool function
        ↓
tools.py
        |
        ↓
Business Services


Responsibilities:

1. Register available tools.
2. Execute selected tool.
3. Return standardized result.

ToolManager does NOT:
- contain business logic
- analyze financial data
- know company rules
- generate reports

It only manages tool execution.
"""


from src import tools


class ToolManager:
    """
    Manage tools available for AI Credit Agent.
    """

    def __init__(self):

        self.tools = {}

        self.register_default_tools()

    # --------------------------------------------------
    # Register Tool
    # --------------------------------------------------

    def register_tool(
        self,
        name,
        function
    ):
        """
        Register a tool.

        Example:

        "review_financial_analysis"
                |
                ↓
        financial_analysis_tool()
        """

        self.tools[name] = function

    # --------------------------------------------------
    # Default Agent Tools
    # --------------------------------------------------

    def register_default_tools(self):
        """
        Register all tools used by Reasoning Engine.

        IMPORTANT:

        These names must exactly match
        ReasoningEngine steps.

        Reasoning Step
                |
                ↓
        Tool Name
                |
                ↓
        Function
        """

        self.register_tool(
            "load_company_context",
            tools.load_company_context_tool
        )

        self.register_tool(
            "review_financial_analysis",
            tools.financial_analysis_tool
        )

        self.register_tool(
            "check_credit_rules",
            tools.credit_rule_check_tool
        )

        self.register_tool(
            "evaluate_risk",
            tools.evaluate_risk_tool
        )

        self.register_tool(
            "get_company_memory",
            tools.get_company_memory_tool
        )

    # --------------------------------------------------
    # Execute Tool
    # --------------------------------------------------

    def run_tool(
        self,
        name,
        **kwargs
    ):
        """
        Execute selected tool.

        Input:

        name:
            tool name from ReasoningEngine

        kwargs:
            prepared input from ReasoningEngine


        Output:

        Standard response:

        {
            status,
            tool,
            result
        }

        """

        if name not in self.tools:

            return {

                "status": "error",

                "tool": name,

                "message":
                    f"Tool '{name}' not registered"

            }

        tool_function = self.tools[name]

        try:

            result = tool_function(
                **kwargs
            )

            return {

                "status":
                    "success",

                "tool":
                    name,

                "result":
                    result

            }

        except Exception as error:

            return {

                "status":
                    "error",

                "tool":
                    name,

                "message":
                    str(error)

            }

    # --------------------------------------------------
    # Utility
    # --------------------------------------------------

    def list_tools(self):
        """
        Return available tools.

        Useful for debugging.
        """

        return list(
            self.tools.keys()
        )
