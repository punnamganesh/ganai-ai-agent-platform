from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self._conversation_history = []
    
    @abstractmethod
    async def process(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process input and return response"""
        pass
    
    def add_to_history(self, role: str, content: str):
        """Add message to conversation history"""
        self._conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": self._get_timestamp()
        })
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get conversation history"""
        return self._conversation_history
    
    def clear_history(self):
        """Clear conversation history"""
        self._conversation_history = []
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get agent metadata"""
        return {
            "name": self.name,
            "description": self.description,
            "type": self.__class__.__name__,
            "history_count": len(self._conversation_history)
        }