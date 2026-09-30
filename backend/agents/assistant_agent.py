import logging
from typing import Dict, Any, Optional, List

from .base_agent import BaseAgent
from ..models.llm_provider import LLMProvider
from ..tools.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


class AssistantAgent(BaseAgent):
    """General assistant agent that can use tools and conversation memory."""

    def __init__(
        self,
        name: str = "Assistant",
        description: str = "General assistant that can use tools"
    ):
        super().__init__(name, description)

        self.llm = LLMProvider()
        self.tools = ToolRegistry()

        self._system_prompt = """You are an AI assistant named "GanAI", created by Ganesh.

Your purpose is to be helpful, friendly, and knowledgeable.

When users ask about your identity, tell them you are GanAI, developed by Ganesh.

You can use tools like calculator, weather, datetime, and web search to help users.

Use the conversation history provided to maintain context across messages.

Be concise, accurate, and polite in all responses."""


    # ---------------------------------------------------------
    # Non-streaming process
    # ---------------------------------------------------------

    async def process(
        self,
        input_text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:

        try:

            self.add_to_history("user", input_text)

            tool_response = await self._check_and_use_tools(input_text)

            if tool_response and tool_response.get("success"):

                return await self._generate_response_with_tool_result(
                    input_text,
                    tool_response,
                    context
                )

            return await self._generate_response(
                input_text,
                context
            )

        except Exception as e:

            logger.error(f"Process error: {e}")

            return {
                "success": False,
                "error": str(e),
                "response": "I encountered an error processing your request."
            }


    # ---------------------------------------------------------
    # Streaming process
    # ---------------------------------------------------------

    async def process_stream(
        self,
        input_text: str,
        context: Optional[Dict[str, Any]] = None
    ):

        try:

            self.add_to_history("user", input_text)

            tool_response = await self._check_and_use_tools(input_text)

            if tool_response and tool_response.get("success"):

                tool_name = tool_response.get(
                    "tool",
                    "unknown"
                )

                result_data = tool_response.get(
                    "result",
                    {}
                )

                if result_data.get("success", False):
                    result_text = result_data.get(
                        "formatted",
                        str(result_data)
                    )
                else:
                    result_text = result_data.get(
                        "message",
                        "Could not get a result."
                    )

                prompt = self._build_prompt(
                    input_text=input_text,
                    context=context,
                    tool_name=tool_name,
                    tool_result=result_text
                )

            else:

                prompt = self._build_prompt(
                    input_text=input_text,
                    context=context
                )

            full_response = ""

            for chunk in self.llm.generate_stream(
                prompt=prompt,
                system_prompt=self._system_prompt
            ):

                if chunk.startswith("data: "):

                    content = chunk[6:].strip()

                    if content == "[DONE]":
                        break

                    full_response += content

                    yield content

            self.add_to_history(
                "assistant",
                full_response
            )

        except Exception as e:

            logger.error(f"Stream error: {e}")

            yield f"Error: {str(e)}"


    # ---------------------------------------------------------
    # Build conversation-aware prompt
    # ---------------------------------------------------------

    def _build_prompt(
        self,
        input_text: str,
        context: Optional[Dict[str, Any]] = None,
        tool_name: Optional[str] = None,
        tool_result: Optional[str] = None
    ) -> str:

        history: List[Dict[str, Any]] = []

        if context:

            history = context.get(
                "conversation_history",
                []
            )

        prompt_parts = []

        # Previous conversation
        if history:

            prompt_parts.append(
                "Previous conversation:"
            )

            for message in history:

                role = message.get(
                    "role",
                    "user"
                )

                content = message.get(
                    "content",
                    ""
                )

                prompt_parts.append(
                    f"{role.capitalize()}: {content}"
                )

            prompt_parts.append("")

        # Tool information
        if tool_name:

            prompt_parts.append(
                f"Tool used: {tool_name}"
            )

            prompt_parts.append(
                f"Tool result: {tool_result}"
            )

            prompt_parts.append("")

        # Current request
        prompt_parts.append(
            f"Current user message: {input_text}"
        )

        prompt_parts.append(
            "Provide a helpful response using the conversation context when relevant."
        )

        return "\n".join(prompt_parts)


    # ---------------------------------------------------------
    # Tool detection
    # ---------------------------------------------------------

    async def _check_and_use_tools(
        self,
        input_text: str
    ) -> Optional[Dict[str, Any]]:

        lower = input_text.lower()

        # 1. Date / Time

        date_keywords = [
            "today",
            "date",
            "time",
            "current date",
            "current time",
            "what day",
            "what time"
        ]

        if any(
            keyword in lower
            for keyword in date_keywords
        ):

            fmt = "full"

            if "time" in lower and "date" not in lower:
                fmt = "time"

            elif "date" in lower and "time" not in lower:
                fmt = "date"

            result = self.tools.execute_tool(
                "datetime",
                fmt
            )

            return {
                "success": True,
                "tool": "datetime",
                "result": result
            }


        # 2. Weather

        weather_keywords = [
            "weather",
            "temperature",
            "forecast",
            "rain",
            "sunny",
            "cloudy",
            "wind"
        ]

        if any(
            keyword in lower
            for keyword in weather_keywords
        ):

            city = self._extract_city(
                input_text
            )

            if city:

                result = self.tools.execute_tool(
                    "weather",
                    city
                )

                return {
                    "success": True,
                    "tool": "weather",
                    "result": result
                }

            return {
                "success": False,
                "error": "City missing",
                "message": "Please specify a city."
            }


        # 3. Web Search

        search_keywords = [
            "search",
            "find",
            "google",
            "bing",
            "what is",
            "who is",
            "tell me about",
            "news",
            "latest"
        ]

        if any(
            keyword in lower
            for keyword in search_keywords
        ):

            query = self._extract_search_query(
                input_text
            )

            if query:

                result = self.tools.execute_tool(
                    "web_search",
                    query
                )

                return {
                    "success": True,
                    "tool": "web_search",
                    "result": result
                }

            return {
                "success": False,
                "error": "No query",
                "message": "What do you want to search for?"
            }


        # 4. Calculator

        triggers = {
            "calculate": "calculator",
            "compute": "calculator",
            "math": "calculator",
            "solve": "calculator"
        }

        for trigger, tool_name in triggers.items():

            if trigger in lower:

                expression = self._extract_expression(
                    input_text
                )

                if expression:

                    result = self.tools.execute_tool(
                        tool_name,
                        expression
                    )

                    return {
                        "success": True,
                        "tool": tool_name,
                        "result": result
                    }

        return None


    # ---------------------------------------------------------
    # Helper: Extract expression
    # ---------------------------------------------------------

    def _extract_expression(
        self,
        text: str
    ) -> Optional[str]:

        import re

        patterns = [
            r'(\d+(?:\s*[+\-*/]\s*\d+)+)',
            r'(\d+\s*\*\s*\d+)',
            r'\(([^)]+)\)'
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text
            )

            if match:

                return match.group(1)

        return None


    # ---------------------------------------------------------
    # Helper: Extract city
    # ---------------------------------------------------------

    def _extract_city(
        self,
        text: str
    ) -> Optional[str]:

        import re

        patterns = [
            r'in\s+([A-Za-z\s]+)$',
            r'for\s+([A-Za-z\s]+)$',
            r'weather\s+([A-Za-z\s]+)$'
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                re.IGNORECASE
            )

            if match:

                city = match.group(1).strip()

                if city:
                    return city

        words = text.split()

        return words[-1] if words else None


    # ---------------------------------------------------------
    # Helper: Extract search query
    # ---------------------------------------------------------

    def _extract_search_query(
        self,
        text: str
    ) -> Optional[str]:

        import re

        patterns = [
            r'^search\s+for\s+(.+)',
            r'^find\s+(.+)',
            r'^what\s+is\s+(.+)',
            r'^who\s+is\s+(.+)',
            r'^tell\s+me\s+about\s+(.+)',
            r'^news\s+about\s+(.+)',
            r'^latest\s+(.+)'
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                re.IGNORECASE
            )

            if match:

                return match.group(1).strip()

        return text.strip()


    # ---------------------------------------------------------
    # LLM response generation
    # ---------------------------------------------------------

    async def _generate_response(
        self,
        input_text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:

        prompt = self._build_prompt(
            input_text=input_text,
            context=context
        )

        response = self.llm.generate_response(
            prompt=prompt,
            system_prompt=self._system_prompt
        )

        if response.get("success"):

            self.add_to_history(
                "assistant",
                response["response"]
            )

        return response


    # ---------------------------------------------------------
    # LLM response with tool result
    # ---------------------------------------------------------

    async def _generate_response_with_tool_result(
        self,
        input_text: str,
        tool_result: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:

        tool_name = tool_result.get(
            "tool",
            "unknown"
        )

        result_data = tool_result.get(
            "result",
            {}
        )

        if result_data.get("success", False):

            result_text = result_data.get(
                "formatted",
                str(result_data)
            )

        else:

            result_text = result_data.get(
                "message",
                "Could not get a result."
            )

        prompt = self._build_prompt(
            input_text=input_text,
            context=context,
            tool_name=tool_name,
            tool_result=result_text
        )

        response = self.llm.generate_response(
            prompt=prompt,
            system_prompt=self._system_prompt
        )

        if response.get("success"):

            self.add_to_history(
                "assistant",
                response["response"]
            )

        return {
            **response,
            "tool_used": tool_name,
            "tool_result": result_data
        }