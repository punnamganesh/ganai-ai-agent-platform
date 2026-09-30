import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class DateTimeTool:
    """Tool to get current date and time"""
    
    def __init__(self):
        self.name = "datetime"
        self.description = "Returns the current date and time"
    
    def execute(self, format: str = "full") -> Dict[str, Any]:
        """
        Execute the datetime tool.
        
        Args:
            format (str): "date" for date only, "time" for time only, "full" for both.
        
        Returns:
            Dict with success flag and formatted result.
        """
        now = datetime.now()
        
        # Build different formats
        date_str = now.strftime("%A, %B %d, %Y")   # e.g., "Monday, March 10, 2025"
        time_str = now.strftime("%I:%M %p")        # e.g., "03:45 PM"
        full_str = f"{date_str} at {time_str}"
        
        if format == "date":
            result = date_str
        elif format == "time":
            result = time_str
        else:
            result = full_str
        
        return {
            "success": True,
            "data": {
                "date": date_str,
                "time": time_str,
                "full": full_str,
                "iso": now.isoformat()
            },
            "formatted": result
        }
    
    def get_metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "version": "1.0.0"
        }