import os
from typing import Optional
from pydantic import BaseModel, Field

class ModelConfig(BaseModel):
    provider: str = Field(
        default=os.getenv("LLM_PROVIDER", "openai"),
        description="LLM provider (openai, anthropic, gemini)"
    )
    model: str = Field(
        default=os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
        description="Model name"
    )
    temperature: float = Field(
        default=float(os.getenv("TEMPERATURE", "0.7")),
        ge=0.0, le=1.0
    )
    max_tokens: int = Field(
        default=int(os.getenv("MAX_TOKENS", "2000")),
        ge=1
    )
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)

    class Config:
        extra = "allow"