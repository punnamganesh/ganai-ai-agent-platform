from typing import Dict, Any, List, Optional
from .calculator import CalculatorTool
from .weather import WeatherTool  
from .datetime_tool import DateTimeTool

class ToolRegistry:
    """Registry for managing available tools"""
    
    def __init__(self):
        self._tools: Dict[str, Any] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register default tools"""
        self.register_tool(CalculatorTool())
        self.register_tool(WeatherTool())
        self.register_tool(DateTimeTool())
      
    
    def register_tool(self, tool: Any) -> None:
        """Register a new tool"""
        tool_name = tool.name if hasattr(tool, 'name') else tool.__class__.__name__
        self._tools[tool_name] = tool
    
    def get_tool(self, name: str) -> Optional[Any]:
        """Get a tool by name"""
        return self._tools.get(name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools with metadata"""
        return [
            {
                "name": name,
                "metadata": tool.get_metadata() if hasattr(tool, 'get_metadata') else {}
            }
            for name, tool in self._tools.items()
        ]
    
    def execute_tool(self, name: str, *args, **kwargs) -> Dict[str, Any]:
        """Execute a tool by name"""
        tool = self.get_tool(name)
        if not tool:
            return {
                "success": False,
                "error": f"Tool '{name}' not found",
                "available_tools": list(self._tools.keys())
            }
        
        if hasattr(tool, 'execute'):
            return tool.execute(*args, **kwargs)
        else:
            return {
                "success": False,
                "error": f"Tool '{name}' does not have execute method"
            }