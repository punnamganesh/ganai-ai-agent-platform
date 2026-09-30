import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models import Conversation, Message

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for managing conversations using PostgreSQL."""

    def __init__(self, db: Session):
        self.db = db

    def create_conversation(
        self,
        agent_name: str = "Assistant",
        title: str = "New Conversation",
    ) -> int:
        """Create and persist a new conversation."""

        conversation = Conversation(
            title=title,
            agent_name=agent_name,
        )

        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)

        return conversation.id

    def add_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        agent_name: Optional[str] = None,
        token_usage: Optional[int] = None,
    ) -> bool:
        """Add and persist a message."""

        conversation = self.db.get(Conversation, conversation_id)

        if not conversation:
            return False

        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            agent_name=agent_name,
            token_usage=token_usage,
        )

        self.db.add(message)
        self.db.commit()

        return True

    def get_conversation(
        self,
        conversation_id: int,
    ) -> Optional[Dict[str, Any]]:
        """Get a conversation and its messages."""

        conversation = self.db.get(Conversation, conversation_id)

        if not conversation:
            return None

        return {
            "id": conversation.id,
            "title": conversation.title,
            "agent_name": conversation.agent_name,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
            "messages": [
                {
                    "id": message.id,
                    "role": message.role,
                    "content": message.content,
                    "agent_name": message.agent_name,
                    "token_usage": message.token_usage,
                    "timestamp": message.created_at.isoformat(),
                }
                for message in conversation.messages
            ],
        }

    def get_conversation_history(
        self,
        conversation_id: int,
    ) -> List[Dict[str, Any]]:
        """Get message history for a conversation."""

        conversation = self.db.get(Conversation, conversation_id)

        if not conversation:
            return []

        return [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in conversation.messages
        ]

    def delete_conversation(
        self,
        conversation_id: int,
    ) -> bool:
        """Delete a conversation and its messages."""

        conversation = self.db.get(Conversation, conversation_id)

        if not conversation:
            return False

        self.db.delete(conversation)
        self.db.commit()

        return True

    def list_conversations(self) -> List[Dict[str, Any]]:
        """List all conversations."""

        statement = (
            select(Conversation)
            .order_by(Conversation.updated_at.desc())
        )

        conversations = self.db.scalars(statement).all()

        return [
            {
                "id": conversation.id,
                "title": conversation.title,
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat(),
                "message_count": len(conversation.messages),
                "agent_name": conversation.agent_name,
            }
            for conversation in conversations
        ]