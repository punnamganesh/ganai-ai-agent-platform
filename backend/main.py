import os
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from .services.agent_service import AgentService
from .services.conversation_service import ConversationService

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Agent System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent_service = AgentService()
conversation_service = ConversationService()

# ---- Models ----
class MessageRequest(BaseModel):
    message: str
    agent_name: Optional[str] = None
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class MessageResponse(BaseModel):
    success: bool
    response: Optional[str] = None
    conversation_id: Optional[str] = None
    agent_name: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

# ---- Routes ----
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
            "/api/chat": "Non‑streaming chat",
            "/api/chat/stream": "Streaming chat (SSE)",
            "/api/conversations": "Manage conversations"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "agents": len(agent_service.list_agents()),
        "conversations": len(conversation_service.list_conversations())
    }

@app.get("/api/agents")
async def list_agents():
    return {"success": True, "agents": agent_service.list_agents()}

# ---- Non‑streaming endpoint ----
@app.post("/api/chat", response_model=MessageResponse)
async def chat(request: MessageRequest):
    try:
        conv_id = request.conversation_id
        if not conv_id:
            conv_id = conversation_service.create_conversation(request.agent_name or "Assistant")
        conversation_service.add_message(conv_id, "user", request.message)

        agent_to_use = request.agent_name
        if not agent_to_use:
            agent_to_use = await agent_service.route_to_agent(request.message, request.context)

        result = await agent_service.process_with_agent(
            agent_name=agent_to_use,
            input_text=request.message,
            context=request.context
        )

        if result.get("success") and result.get("response"):
            conversation_service.add_message(conv_id, "assistant", result["response"])

        return MessageResponse(
            success=result.get("success", False),
            response=result.get("response"),
            conversation_id=conv_id,
            agent_name=agent_to_use,
            error=result.get("error"),
            metadata={
                "usage": result.get("usage"),
                "tool_used": result.get("tool_used"),
                "tool_result": result.get("tool_result")
            }
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ---- Streaming (SSE) endpoint ----
@app.post("/api/chat/stream")
async def chat_stream(request: MessageRequest):
    try:
        conv_id = request.conversation_id
        if not conv_id:
            conv_id = conversation_service.create_conversation(request.agent_name or "Assistant")
        conversation_service.add_message(conv_id, "user", request.message)

        agent_to_use = request.agent_name
        if not agent_to_use:
            agent_to_use = await agent_service.route_to_agent(request.message, request.context)

        async def event_generator():
            full_response = ""
            # First, send the chosen agent name (optional)
            yield f"data: agent:{agent_to_use}\n\n"
            async for chunk in agent_service.process_stream(agent_to_use, request.message, request.context):
                full_response += chunk
                yield f"data: {chunk}\n\n"
            conversation_service.add_message(conv_id, "assistant", full_response)
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        logger.error(f"Stream error: {e}")
        return StreamingResponse(
            iter([f"data: Error: {str(e)}\n\n"]),
            media_type="text/event-stream"
        )

# ---- Conversation management (unchanged) ----
@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    conv = conversation_service.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"success": True, "conversation": conv}

@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    if not conversation_service.delete_conversation(conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"success": True, "message": "Conversation deleted"}

@app.get("/api/conversations")
async def list_conversations():
    return {"success": True, "conversations": conversation_service.list_conversations()}

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)