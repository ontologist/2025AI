"""Service for interacting with Ollama LLM."""
import httpx
from typing import List, Dict, Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class OllamaService:
    """Service wrapper for Ollama API."""
    
    def __init__(self, model: Optional[str] = None):
        self.model = model or settings.OLLAMA_MODEL
        self.base_url = settings.OLLAMA_BASE_URL
        self.client = httpx.AsyncClient(timeout=300.0)  # 5 minute timeout for large models
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """Generate response using Ollama chat API."""
        try:
            # Prepare messages
            request_messages = messages.copy()
            if system_prompt:
                request_messages = [{"role": "system", "content": system_prompt}] + request_messages
            
            # Call Ollama API
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": request_messages,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    },
                    "stream": False
                }
            )
            response.raise_for_status()
            
            result = response.json()
            # Handle Ollama chat API response format
            if "message" in result:
                return result["message"].get("content", "")
            elif "response" in result:
                return result["response"]
            else:
                # Fallback: return full response as string
                return str(result)
            
        except Exception as e:
            logger.error(f"Ollama API error: {str(e)}")
            raise Exception(f"Ollama error: {str(e)}")
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """Generate text using Ollama generate API."""
        try:
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    },
                    "stream": False
                }
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
            
        except Exception as e:
            logger.error(f"Ollama generate error: {str(e)}")
            raise Exception(f"Ollama error: {str(e)}")
    
    async def health_check(self) -> bool:
        """Check if Ollama is running and accessible."""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except:
            return False
    
    async def list_models(self) -> List[str]:
        """List available Ollama models."""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except Exception as e:
            logger.error(f"Error listing models: {str(e)}")
            return []
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

