import logging
from typing import Dict, Any, Optional
from .base_agent import BaseAgent
from ..models.llm_provider import LLMProvider
from ..tools.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)

class AssistantAgent(BaseAgent):
    """General assistant agent that can use tools"""
    
    def __init__(self, name: str = "Assistant", 
                 description: str = "General assistant that can use tools"):
        super().__init__(name, description)
        self.llm = LLMProvider()
        self.tools = ToolRegistry()
        # ==== Custom system prompt – edit as needed ====
        self._system_prompt = """You are an AI assistant named "GanAI", created by Ganesh.
Your purpose is to be helpful, friendly, and knowledgeable.
When users ask about your identity, tell them you are GanAI, developed by Ganesh.
You can use tools like calculator, weather, datetime, and web search to help users.
Be concise, accurate, and polite in all responses."""
    
    # ---- Non‑streaming process ----
    async def process(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            self.add_to_history("user", input_text)
            tool_response = await self._check_and_use_tools(input_text)
            if tool_response and tool_response.get("success"):
                return await self._generate_response_with_tool_result(input_text, tool_response)
            else:
                return await self._generate_response(input_text)
        except Exception as e:
            logger.error(f"Process error: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "I encountered an error processing your request."
            }
    
    # ---- Streaming process (SSE) ----
    async def process_stream(self, input_text: str, context: Optional[Dict[str, Any]] = None):
        """Yields text chunks as they arrive from the LLM."""
        try:
            self.add_to_history("user", input_text)
            tool_response = await self._check_and_use_tools(input_text)

            if tool_response and tool_response.get("success"):
                tool_name = tool_response.get("tool", "unknown")
                result_data = tool_response.get("result", {})
                if result_data.get("success", False):
                    result_text = result_data.get("formatted", str(result_data))
                else:
                    result_text = result_data.get("message", "Could not get a result.")
                prompt = f"User request: {input_text}\nTool used: {tool_name}\nTool result: {result_text}\nProvide a helpful response incorporating this information."
                full_response = ""
                for chunk in self.llm.generate_stream(prompt=prompt, system_prompt=self._system_prompt):
                    if chunk.startswith("data: "):
                        content = chunk[6:].strip()
                        if content == "[DONE]":
                            break
                        full_response += content
                        yield content
                self.add_to_history("assistant", full_response)
            else:
                full_response = ""
                for chunk in self.llm.generate_stream(prompt=input_text, system_prompt=self._system_prompt):
                    if chunk.startswith("data: "):
                        content = chunk[6:].strip()
                        if content == "[DONE]":
                            break
                        full_response += content
                        yield content
                self.add_to_history("assistant", full_response)
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"Error: {str(e)}"
    
    # ---------- Tool detection ----------
    async def _check_and_use_tools(self, input_text: str) -> Optional[Dict[str, Any]]:
        lower = input_text.lower()
        
        # 1. Date/Time
        date_keywords = ["today", "date", "time", "current date", "current time", "what day", "what time"]
        if any(k in lower for k in date_keywords):
            fmt = "full"
            if "time" in lower and "date" not in lower:
                fmt = "time"
            elif "date" in lower and "time" not in lower:
                fmt = "date"
            res = self.tools.execute_tool("datetime", fmt)
            return {"success": True, "tool": "datetime", "result": res}
        
        # 2. Weather
        weather_kw = ["weather", "temperature", "forecast", "rain", "sunny", "cloudy", "wind"]
        if any(k in lower for k in weather_kw):
            city = self._extract_city(input_text)
            if city:
                res = self.tools.execute_tool("weather", city)
                return {"success": True, "tool": "weather", "result": res}
            return {"success": False, "error": "City missing", "message": "Please specify a city."}
        
        # 3. Web Search
        search_kw = ["search", "find", "google", "bing", "what is", "who is", "tell me about", "news", "latest"]
        if any(k in lower for k in search_kw):
            query = self._extract_search_query(input_text)
            if query:
                res = self.tools.execute_tool("web_search", query)
                return {"success": True, "tool": "web_search", "result": res}
            return {"success": False, "error": "No query", "message": "What do you want to search for?"}
        
        # 4. Calculator
        triggers = {"calculate": "calculator", "compute": "calculator", "math": "calculator", "solve": "calculator"}
        for trigger, tool_name in triggers.items():
            if trigger in lower:
                expr = self._extract_expression(input_text)
                if expr:
                    res = self.tools.execute_tool(tool_name, expr)
                    return {"success": True, "tool": tool_name, "result": res}
        return None
    
    # ---------- Helper extraction methods ----------
    def _extract_expression(self, text: str) -> Optional[str]:
        import re
        patterns = [
            r'(\d+[\+\-\*/]\d+)',
            r'(\d+\s*[\+\-\*/]\s*\d+)',
            r'(\([^)]+\))',
        ]
        for p in patterns:
            m = re.search(p, text)
            if m:
                return m.group(1)
        return None

    def _extract_city(self, text: str) -> Optional[str]:
        import re
        patterns = [
            r'in\s+([A-Za-z\s]+)$',
            r'for\s+([A-Za-z\s]+)$',
            r'weather\s+([A-Za-z\s]+)$',
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                city = m.group(1).strip()
                if city:
                    return city
        words = text.split()
        return words[-1] if words else None

    def _extract_search_query(self, text: str) -> Optional[str]:
        import re
        patterns = [
            r'^search\s+for\s+(.+)',
            r'^find\s+(.+)',
            r'^what\s+is\s+(.+)',
            r'^who\s+is\s+(.+)',
            r'^tell\s+me\s+about\s+(.+)',
            r'^news\s+about\s+(.+)',
            r'^latest\s+(.+)',
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return text.strip()
    
    # ---------- LLM response generation (non‑streaming) ----------
    async def _generate_response(self, input_text: str) -> Dict[str, Any]:
        resp = self.llm.generate_response(prompt=input_text, system_prompt=self._system_prompt)
        if resp.get("success"):
            self.add_to_history("assistant", resp["response"])
        return resp

    async def _generate_response_with_tool_result(self, input_text: str, tool_result: Dict[str, Any]) -> Dict[str, Any]:
        tool_name = tool_result.get("tool", "unknown")
        result_data = tool_result.get("result", {})
        if result_data.get("success", False):
            result_text = result_data.get("formatted", str(result_data))
        else:
            result_text = result_data.get("message", "Could not get a result.")
        prompt = f"User request: {input_text}\nTool used: {tool_name}\nTool result: {result_text}\nProvide a helpful response."
        resp = self.llm.generate_response(prompt=prompt, system_prompt=self._system_prompt)
        if resp.get("success"):
            self.add_to_history("assistant", resp["response"])
        return {**resp, "tool_used": tool_name, "tool_result": result_data}