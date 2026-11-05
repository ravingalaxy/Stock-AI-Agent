"""Unified LLM Client supporting OpenAI-compatible APIs and local Ollama."""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union, AsyncGenerator
from abc import ABC, abstractmethod

from openai import OpenAI, AsyncOpenAI
from pydantic import BaseModel

from src.utils.logger import logger
from src.config import get_config


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.2,
        max_tokens: int = 2048,
        response_format: Optional[Dict] = None,
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None
    ) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def embeddings(self, texts: List[str]) -> List[List[float]]:
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI API Provider (supports any OpenAI-compatible endpoint)."""
    
    def __init__(self, api_key: str, base_url: str, model: str, embedding_model: str):
        self.client = OpenAI(
            api_key=api_key, 
            base_url=base_url,
            timeout=15.0,  # Shorter timeout for faster fallback
            max_retries=1
        )
        self.async_client = AsyncOpenAI(
            api_key=api_key, 
            base_url=base_url,
            timeout=15.0,
            max_retries=1
        )
        self.model = model
        self.embedding_model = embedding_model
        
    def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.2,
        max_tokens: int = 2048,
        response_format: Optional[Dict] = None,
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None
    ) -> Dict[str, Any]:
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            params["response_format"] = response_format
        if tools:
            params["tools"] = tools
            params["tool_choice"] = tool_choice or "auto"
            
        try:
            response = self.client.chat.completions.create(**params)
            return {
                "content": response.choices[0].message.content,
                "tool_calls": response.choices[0].message.tool_calls,
                "usage": response.usage.model_dump() if response.usage else None,
                "model": response.model
            }
        except Exception as e:
            logger.error(f"OpenAI chat completion failed: {e}")
            raise
            
    def embeddings(self, texts: List[str]) -> List[List[float]]:
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=texts
            )
            return [d.embedding for d in response.data]
        except Exception as e:
            logger.error(f"OpenAI embeddings failed: {e}")
            raise


class OllamaProvider(LLMProvider):
    """Local Ollama Provider."""
    
    def __init__(self, base_url: str, model: str, embedding_model: str = "nomic-embed-text"):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.embedding_model = embedding_model
        import httpx
        self.client = httpx.Client(timeout=120.0)
        
    def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.2,
        max_tokens: int = 2048,
        response_format: Optional[Dict] = None,
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None
    ) -> Dict[str, Any]:
        # Ollama uses different API format
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        
        # Ollama supports format parameter for JSON mode
        if response_format and response_format.get("type") == "json_object":
            payload["format"] = "json"
            
        try:
            response = self.client.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            return {
                "content": data["message"]["content"],
                "tool_calls": None,  # Ollama doesn't support tool calling in same way
                "usage": None,
                "model": data.get("model", self.model)
            }
        except Exception as e:
            logger.error(f"Ollama chat completion failed: {e}")
            raise
            
    def embeddings(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for text in texts:
            try:
                response = self.client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": self.embedding_model, "prompt": text}
                )
                response.raise_for_status()
                embeddings.append(response.json()["embedding"])
            except Exception as e:
                logger.error(f"Ollama embedding failed: {e}")
                embeddings.append([0.0] * 384)  # Default dim for nomic-embed-text
        return embeddings


class LLMClient:
    """Unified LLM Client with provider abstraction."""
    
    def __init__(self):
        self.config = get_config()
        self.provider = None
        self._init_provider()
        
    def _init_provider(self):
        """Initialize provider with graceful fallback."""
        llm_cfg = self.config.llm
        provider_name = getattr(llm_cfg, "provider", "").lower()
        if provider_name in ["deterministic", "none", "offline"]:
            logger.info("Deterministic quantitative mode active (algorithmic multi-factor scoring).")
            self.provider = None
            return

        # Check for unconfigured or placeholder API keys before attempting network calls
        api_key = ""
        if provider_name == "freellmapi":
            api_key = llm_cfg.freellmapi_api_key or os.getenv("FREELLM_API_KEY") or ""
        elif provider_name == "openai":
            api_key = llm_cfg.openai_api_key or os.getenv("OPENAI_API_KEY") or ""

        if not api_key or api_key.startswith("your_") or "placeholder" in api_key.lower():
            logger.info(f"LLM API key not configured for '{provider_name}' — proceeding in deterministic quantitative mode.")
            self.provider = None
            return

        try:
            self.provider = self._create_provider()
            if not self._test_connectivity():
                logger.info("External LLM API unreachable — proceeding in deterministic quantitative mode.")
                self.provider = None
        except Exception as e:
            logger.info(f"LLM provider offline ({e}) — proceeding in deterministic quantitative mode.")
            self.provider = None
            
    def _test_connectivity(self) -> bool:
        """Quick connectivity test to LLM API."""
        try:
            import httpx
            # Quick HEAD request to check connectivity
            response = httpx.head(self.config.llm.freellmapi_api_base.replace("/v1", ""), timeout=3.0)
            return response.status_code < 500
        except Exception:
            return False
            
    def _create_provider(self) -> LLMProvider:
        """Create and return the appropriate LLM provider."""
        llm_cfg = self.config.llm
        
        # Debug logging
        logger.info(f"LLM Config - Provider: {llm_cfg.provider}, Model: {llm_cfg.model_name}")
        
        if llm_cfg.provider == "freellmapi":
            # freellmapi uses OpenAI-compatible API format
            api_key = llm_cfg.freellmapi_api_key or os.getenv("FREELLM_API_KEY")
            if not api_key:
                raise ValueError("FREELLM_API_KEY not set. Please configure in .env or config.yaml")
            logger.info(f"Using freellmapi - API Key: {api_key[:10]}... Base URL: {llm_cfg.freellmapi_api_base}")
            return OpenAIProvider(
                api_key=api_key,
                base_url=llm_cfg.freellmapi_api_base,
                model=llm_cfg.model_name,
                embedding_model=llm_cfg.embedding_model
            )
        elif llm_cfg.provider == "openai":
            api_key = llm_cfg.openai_api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set. Please configure in .env or config.yaml")
            logger.info(f"Using OpenAI - API Key: {api_key[:10]}... Base URL: {llm_cfg.openai_api_base}")
            return OpenAIProvider(
                api_key=api_key,
                base_url=llm_cfg.openai_api_base,
                model=llm_cfg.model_name,
                embedding_model=llm_cfg.embedding_model
            )
        elif llm_cfg.provider == "ollama":
            logger.info(f"Using Ollama - Base URL: {llm_cfg.ollama_base_url}")
            return OllamaProvider(
                base_url=llm_cfg.ollama_base_url,
                model=llm_cfg.ollama_model_name,
                embedding_model="nomic-embed-text"
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_cfg.provider}")
            
    def chat(
        self, 
        messages: List[Dict[str, str]], 
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
        schema: Optional[Dict] = None
    ) -> str:
        """Simple chat completion returning content string."""
        if self.provider is None:
            return "LLM analysis unavailable (provider not configured)."
            
        temp = temperature if temperature is not None else self.config.llm.temperature
        max_t = max_tokens if max_tokens is not None else self.config.llm.max_tokens
        
        response_format = None
        if json_mode:
            response_format = {"type": "json_object"}
        if schema:
            response_format = {"type": "json_schema", "json_schema": schema}
            
        try:
            result = self.provider.chat_completion(
                messages=messages,
                temperature=temp,
                max_tokens=max_t,
                response_format=response_format
            )
            return result["content"]
        except Exception as e:
            logger.warning(f"LLM API call failed, using fallback: {e}")
            return "LLM analysis unavailable (API error - using deterministic fallback)."
    
    def chat_structured(
        self, 
        messages: List[Dict[str, str]], 
        response_model: type[BaseModel],
        temperature: Optional[float] = None
    ) -> BaseModel:
        """Chat completion with structured Pydantic output."""
        if self.provider is None:
            return response_model.model_construct(error="LLM provider not configured")
            
        schema = response_model.model_json_schema()
        
        try:
            content = self.chat(messages, temperature=temperature, json_mode=True, schema={"schema": schema})
            
            # Check if content is a fallback message (not JSON)
            if content.startswith("LLM analysis unavailable"):
                return response_model.model_construct(error="LLM API unavailable")
            
            try:
                parsed = json.loads(content)
                return response_model(**parsed)
            except Exception as e:
                logger.error(f"Failed to parse structured output: {e}")
                logger.debug(f"Raw content: {content}")
                return response_model.model_construct(error="LLM parsing failed")
        except Exception as e:
            logger.warning(f"LLM structured call failed, using fallback: {e}")
            return response_model.model_construct(error="LLM API error")
            
    def embed(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """Generate embeddings for text(s)."""
        if self.provider is None:
            if isinstance(texts, str):
                texts = [texts]
            return [[0.0] * 384 for _ in texts]
        try:
            return self.provider.embeddings(texts)
        except Exception as e:
            logger.warning(f"LLM embedding failed, using zero vectors: {e}")
            if isinstance(texts, str):
                texts = [texts]
            return [[0.0] * 384 for _ in texts]


# Global client instance
_client: Optional[LLMClient] = None

def get_llm_client() -> LLMClient:
    """Get or create global LLM client."""
    global _client
    if _client is None:
        _client = LLMClient()
    return _client