import os
import logging
from typing import Optional, Dict, Any, Generator
import google.generativeai as genai
from openai import OpenAI
from anthropic import Anthropic
from .model_config import ModelConfig

logger = logging.getLogger(__name__)

class LLMProvider:
    """Provider for language model interactions with streaming support"""
    
    def __init__(self, config: Optional[ModelConfig] = None):
        self.config = config or ModelConfig()
        self._client = None
        self._initialized = False
        self._error = None
        
    def _ensure_initialized(self):
        if self._initialized:
            return
        try:
            provider = self.config.provider
            if provider == "openai":
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY not set")
                self._client = OpenAI(api_key=api_key)
            elif provider == "anthropic":
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    raise ValueError("ANTHROPIC_API_KEY not set")
                self._client = Anthropic(api_key=api_key)
            elif provider == "gemini":
                api_key = os.getenv("GEMINI_API_KEY")
                if not api_key:
                    raise ValueError("GEMINI_API_KEY not set")
                genai.configure(api_key=api_key)
                model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
                self._client = genai.GenerativeModel(model_name)
            else:
                raise ValueError(f"Unsupported provider: {provider}")
            self._initialized = True
        except Exception as e:
            self._error = str(e)
            logger.error(f"Failed to initialize LLM client: {e}")

    # ---- Non‑streaming ----
    def generate_response(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        self._ensure_initialized()
        if self._error:
            return {"success": False, "error": self._error, "response": "LLM not configured."}
        try:
            if self.config.provider == "openai":
                return self._generate_openai(prompt, system_prompt, **kwargs)
            elif self.config.provider == "anthropic":
                return self._generate_anthropic(prompt, system_prompt, **kwargs)
            elif self.config.provider == "gemini":
                return self._generate_gemini(prompt, system_prompt, **kwargs)
        except Exception as e:
            logger.error(f"Generate error: {e}")
            return {"success": False, "error": str(e), "response": "Error generating response."}

    # ---- Streaming (SSE) ----
    def generate_stream(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Generator[str, None, None]:
        self._ensure_initialized()
        if self._error:
            yield f"data: Error: {self._error}\n\n"
            return
        try:
            if self.config.provider == "gemini":
                yield from self._generate_gemini_stream(prompt, system_prompt, **kwargs)
            elif self.config.provider == "openai":
                yield from self._generate_openai_stream(prompt, system_prompt, **kwargs)
            elif self.config.provider == "anthropic":
                yield from self._generate_anthropic_stream(prompt, system_prompt, **kwargs)
            else:
                yield f"data: Error: Unsupported provider for streaming\n\n"
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: Error: {str(e)}\n\n"

    # ---------- Provider implementations (non‑streaming) ----------
    def _generate_openai(self, prompt, system_prompt=None, **kwargs):
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        resp = self._client.chat.completions.create(
            model=kwargs.get("model", self.config.model),
            messages=messages,
            temperature=kwargs.get("temperature", self.config.temperature),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            top_p=kwargs.get("top_p", self.config.top_p),
        )
        return {
            "success": True,
            "response": resp.choices[0].message.content,
            "model": resp.model,
            "usage": {
                "prompt_tokens": resp.usage.prompt_tokens,
                "completion_tokens": resp.usage.completion_tokens,
                "total_tokens": resp.usage.total_tokens
            }
        }

    def _generate_anthropic(self, prompt, system_prompt=None, **kwargs):
        resp = self._client.messages.create(
            model=kwargs.get("model", self.config.model),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            temperature=kwargs.get("temperature", self.config.temperature),
            system=system_prompt if system_prompt else "",
            messages=[{"role": "user", "content": prompt}]
        )
        return {
            "success": True,
            "response": resp.content[0].text,
            "model": resp.model,
            "usage": {
                "input_tokens": resp.usage.input_tokens,
                "output_tokens": resp.usage.output_tokens
            }
        }

    def _generate_gemini(self, prompt, system_prompt=None, **kwargs):
        full = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        resp = self._client.generate_content(
            full,
            generation_config={
                "temperature": kwargs.get("temperature", self.config.temperature),
                "max_output_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "top_p": kwargs.get("top_p", self.config.top_p),
            }
        )
        return {
            "success": True,
            "response": resp.text,
            "model": "gemini",
            "usage": {}
        }

    # ---------- Streaming (SSE) implementations ----------
    def _generate_gemini_stream(self, prompt, system_prompt=None, **kwargs):
        full = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        response = self._client.generate_content(
            full,
            generation_config={
                "temperature": kwargs.get("temperature", self.config.temperature),
                "max_output_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "top_p": kwargs.get("top_p", self.config.top_p),
            },
            stream=True
        )
        for chunk in response:
            if chunk.text:
                yield f"data: {chunk.text}\n\n"
        yield "data: [DONE]\n\n"

    def _generate_openai_stream(self, prompt, system_prompt=None, **kwargs):
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        stream = self._client.chat.completions.create(
            model=kwargs.get("model", self.config.model),
            messages=messages,
            temperature=kwargs.get("temperature", self.config.temperature),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            top_p=kwargs.get("top_p", self.config.top_p),
            stream=True
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield f"data: {chunk.choices[0].delta.content}\n\n"
        yield "data: [DONE]\n\n"

    def _generate_anthropic_stream(self, prompt, system_prompt=None, **kwargs):
        with self._client.messages.stream(
            model=kwargs.get("model", self.config.model),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            temperature=kwargs.get("temperature", self.config.temperature),
            system=system_prompt if system_prompt else "",
            messages=[{"role": "user", "content": prompt}]
        ) as stream:
            for text in stream.text_stream:
                yield f"data: {text}\n\n"
        yield "data: [DONE]\n\n"