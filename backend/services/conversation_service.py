import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class ConversationService:
    """Service for managing conversations"""
    
    def __init__(self):
        self._conversations: Dict[str, Dict[str, Any]] = {}
    
    def create_conversation(self, agent_name: str = "Assistant") -> str:
        """Create a new conversation"""
        conversation_id = str(uuid.uuid4())
        self._conversations[conversation_id] = {
            "id": conversation_id,
            "agent_name": agent_name,
            "created_at": datetime.now().isoformat(),
            "messages": [],
            "metadata": {}
        }
        return conversation_id
    
    def add_message(self, conversation_id: str, role: str, content: str) -> bool:
        """Add a message to a conversation"""
        if conversation_id not in self._conversations:
            return False
        
        self._conversations[conversation_id]["messages"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        return True
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get a conversation by ID"""
        return self._conversations.get(conversation_id)
    
    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get messages from a conversation"""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return []
        return conversation.get("messages", [])
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation"""
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            return True
        return False
    
    def list_conversations(self) -> List[Dict[str, Any]]:
        """List all conversations"""
        return [
            {
                "id": conv_id,
                "created_at": conv["created_at"],
                "message_count": len(conv["messages"]),
                "agent_name": conv["agent_name"]
            }
            for conv_id, conv in self._conversations.items()
        ]