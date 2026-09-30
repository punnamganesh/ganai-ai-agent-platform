import math
import re
from typing import Dict, Any, Optional

class CalculatorTool:
    """A tool for performing mathematical calculations"""
    
    def __init__(self):
        self.name = "calculator"
        self.description = "Performs mathematical calculations including basic arithmetic and advanced operations"
        
    def execute(self, expression: str) -> Dict[str, Any]:
        """
        Execute a mathematical calculation
        
        Args:
            expression: Mathematical expression as string
            
        Returns:
            Dictionary containing result and metadata
        """
        try:
            # Sanitize the expression
            sanitized = self._sanitize_expression(expression)
            
            # Evaluate safely
            result = self._safe_evaluate(sanitized)
            
            return {
                "success": True,
                "expression": expression,
                "result": result,
                "formatted": self._format_result(result)
            }
        except Exception as e:
            return {
                "success": False,
                "expression": expression,
                "error": str(e),
                "message": "Failed to calculate expression"
            }
    
    def _sanitize_expression(self, expression: str) -> str:
        """Remove dangerous characters and validate expression"""
        # Remove whitespace
        expression = expression.replace(" ", "")
        
        # Allowed characters: numbers, operators, parentheses, and basic functions
        allowed_pattern = r'^[\d+\-*/()^.,sqrtlogsinhcosta n]+$'
        if not re.match(allowed_pattern, expression):
            raise ValueError("Expression contains invalid characters")
        
        return expression
    
    def _safe_evaluate(self, expression: str) -> float:
        """Safely evaluate mathematical expression"""
        # Define allowed functions
        safe_dict = {
            'sqrt': math.sqrt,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'log': math.log,
            'log10': math.log10,
            'exp': math.exp,
            'pi': math.pi,
            'e': math.e,
            'abs': abs,
            'pow': pow,
            'round': round,
            'factorial': math.factorial
        }
        
        # Evaluate expression
        result = eval(expression, {"__builtins__": {}}, safe_dict)
        return float(result)
    
    def _format_result(self, result: float) -> str:
        """Format result for display"""
        if result == int(result):
            return str(int(result))
        return f"{result:.10f}".rstrip('0').rstrip('.')
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get tool metadata"""
        return {
            "name": self.name,
            "description": self.description,
            "version": "1.0.0",
            "capabilities": ["arithmetic", "trigonometry", "logarithms", "statistics"]
        }