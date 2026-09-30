import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
import uvicorn
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from .db.database import get_db
from .services.agent_service import AgentService
from .services.conversation_service import ConversationService


# =========================================================
# Logging
# =========================================================

logging.basicConfig(
    level=getattr(
        logging,
        os.getenv("LOG_LEVEL", "INFO")
    ),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


# =========================================================
# FastAPI Application
# =========================================================

app = FastAPI(
    title="AI Agent System",
    version="1.0.0"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# Services
# =========================================================

agent_service = AgentService()


# =========================================================
# Request / Response Models
# =========================================================

class MessageRequest(BaseModel):
    message: str
    agent_name: Optional[str] = None
    conversation_id: Optional[int] = None
    context: Optional[Dict[str, Any]] = None


class MessageResponse(BaseModel):
    success: bool
    response: Optional[str] = None
    conversation_id: Optional[int] = None
    agent_name: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# =========================================================
# Root
# =========================================================

@app.get("/")
async def root():
    return {
        "service": "AI Agent System",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "/": "Info",
            "/health": "Health",
            "/api/agents": "List agents",
            "/api/chat": "Non-streaming chat",
            "/api/chat/stream": "Streaming chat (SSE)",
            "/api/conversations": "Manage conversations"
        }
    }


# =========================================================
# Health Check
# =========================================================

@app.get("/health")
async def health_check(
    db: Session = Depends(get_db)
):
    conversation_service = ConversationService(db)

    return {
        "status": "healthy",
        "agents": len(agent_service.list_agents()),
        "conversations": len(
            conversation_service.list_conversations()
        )
    }


# =========================================================
# Agents
# =========================================================

@app.get("/api/agents")
async def list_agents():
    return {
        "success": True,
        "agents": agent_service.list_agents()
    }


# =========================================================
# Non-Streaming Chat
# =========================================================

@app.post(
    "/api/chat",
    response_model=MessageResponse
)
async def chat(
    request: MessageRequest,
    db: Session = Depends(get_db)
):

    try:

        conversation_service = ConversationService(db)

        # -------------------------------------------------
        # Create or reuse conversation
        # -------------------------------------------------

        conv_id = request.conversation_id

        if not conv_id:

            conv_id = conversation_service.create_conversation(
                request.agent_name or "Assistant"
            )

        # -------------------------------------------------
        # Save user message
        # -------------------------------------------------

        conversation_service.add_message(
            conversation_id=conv_id,
            role="user",
            content=request.message
        )

        # -------------------------------------------------
        # Get conversation history
        # -------------------------------------------------

        conversation_history = (
            conversation_service.get_conversation_history(
                conv_id
            )
        )

        # -------------------------------------------------
        # Build agent context
        # -------------------------------------------------

        agent_context = dict(
            request.context or {}
        )

        agent_context["conversation_history"] = (
            conversation_history
        )

        # -------------------------------------------------
        # Select agent
        # -------------------------------------------------

        agent_to_use = request.agent_name

        if not agent_to_use:

            agent_to_use = await agent_service.route_to_agent(
                request.message,
                agent_context
            )

        # -------------------------------------------------
        # Process request
        # -------------------------------------------------

        result = await agent_service.process_with_agent(
            agent_name=agent_to_use,
            input_text=request.message,
            context=agent_context
        )

        # -------------------------------------------------
        # Save assistant response
        # -------------------------------------------------

        if (
            result.get("success")
            and result.get("response")
        ):

            conversation_service.add_message(
                conversation_id=conv_id,
                role="assistant",
                content=result["response"],
                agent_name=agent_to_use
            )

        # -------------------------------------------------
        # Return response
        # -------------------------------------------------

        return MessageResponse(
            success=result.get(
                "success",
                False
            ),
            response=result.get(
                "response"
            ),
            conversation_id=conv_id,
            agent_name=agent_to_use,
            error=result.get(
                "error"
            ),
            metadata={
                "usage": result.get(
                    "usage"
                ),
                "tool_used": result.get(
                    "tool_used"
                ),
                "tool_result": result.get(
                    "tool_result"
                )
            }
        )

    except Exception as e:

        logger.exception(
            "Chat error"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================================================
# Streaming Chat - SSE
# =========================================================

@app.post(
    "/api/chat/stream"
)
async def chat_stream(
    request: MessageRequest,
    db: Session = Depends(get_db)
):

    try:

        conversation_service = ConversationService(db)

        # -------------------------------------------------
        # Create or reuse conversation
        # -------------------------------------------------

        conv_id = request.conversation_id

        if not conv_id:

            conv_id = conversation_service.create_conversation(
                request.agent_name or "Assistant"
            )

        # -------------------------------------------------
        # Save user message
        # -------------------------------------------------

        conversation_service.add_message(
            conversation_id=conv_id,
            role="user",
            content=request.message
        )

        # -------------------------------------------------
        # Get conversation history
        # -------------------------------------------------

        conversation_history = (
            conversation_service.get_conversation_history(
                conv_id
            )
        )

        # -------------------------------------------------
        # Build agent context
        # -------------------------------------------------

        agent_context = dict(
            request.context or {}
        )

        agent_context["conversation_history"] = (
            conversation_history
        )

        # -------------------------------------------------
        # Select agent
        # -------------------------------------------------

        agent_to_use = request.agent_name

        if not agent_to_use:

            agent_to_use = await agent_service.route_to_agent(
                request.message,
                agent_context
            )

        # -------------------------------------------------
        # Streaming generator
        # -------------------------------------------------

        async def event_generator():

            full_response = ""

            # Send conversation ID
            yield (
                f"data: conversation_id:{conv_id}\n\n"
            )

            # Send selected agent
            yield (
                f"data: agent:{agent_to_use}\n\n"
            )

            # Stream response
            async for chunk in agent_service.process_stream(
                agent_to_use,
                request.message,
                agent_context
            ):

                full_response += chunk

                yield f"data: {chunk}\n\n"

            # -------------------------------------------------
            # Save assistant response
            # -------------------------------------------------

            conversation_service.add_message(
                conversation_id=conv_id,
                role="assistant",
                content=full_response,
                agent_name=agent_to_use
            )

            # End stream
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream"
        )

    except Exception as e:

        logger.exception(
            "Stream error"
        )

        return StreamingResponse(
            iter([
                f"data: Error: {str(e)}\n\n"
            ]),
            media_type="text/event-stream"
        )


# =========================================================
# Get Conversation
# =========================================================

@app.get(
    "/api/conversations/{conversation_id}"
)
async def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db)
):

    conversation_service = ConversationService(db)

    conversation = (
        conversation_service.get_conversation(
            conversation_id
        )
    )

    if not conversation:

        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    return {
        "success": True,
        "conversation": conversation
    }


# =========================================================
# Delete Conversation
# =========================================================

@app.delete(
    "/api/conversations/{conversation_id}"
)
async def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db)
):

    conversation_service = ConversationService(db)

    deleted = (
        conversation_service.delete_conversation(
            conversation_id
        )
    )

    if not deleted:

        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    return {
        "success": True,
        "message": "Conversation deleted"
    }


# =========================================================
# List Conversations
# =========================================================

@app.get(
    "/api/conversations"
)
async def list_conversations(
    db: Session = Depends(get_db)
):

    conversation_service = ConversationService(db)

    return {
        "success": True,
        "conversations": (
            conversation_service.list_conversations()
        )
    }


# =========================================================
# Run Application
# =========================================================

if __name__ == "__main__":

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
