"""Chat API endpoints for student-bot interactions."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from app.services.bot_service import BotService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize bot service
bot_service = BotService()


class ChatMessage(BaseModel):
    """Request model for chat message."""
    user_id: str
    message: str
    language: str = "en"  # en or ja
    conversation_history: Optional[List[Dict[str, str]]] = None
    use_rag: bool = True
    use_web_search: bool = True


class ChatResponse(BaseModel):
    """Response model for chat."""
    response: str
    user_id: str
    language: str
    context_used: bool
    web_search_used: bool
    model: str


@router.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """
    Chat endpoint for student-bot interactions.
    
    Students send messages and receive bot responses powered by RAG + Web Search + Ollama.
    """
    try:
        result = await bot_service.chat(
            user_id=message.user_id,
            message=message.message,
            language=message.language,
            conversation_history=message.conversation_history,
            use_rag=message.use_rag,
            use_web_search=message.use_web_search
        )
        
        return ChatResponse(**result)
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@router.get("/health")
async def bot_health():
    """Check bot service health."""
    try:
        health = await bot_service.health_check()
        return health
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return {
            "ollama": False,
            "rag": False,
            "web_search": False,
            "overall": False,
            "error": str(e)
        }


@router.get("/test")
async def test_chat():
    """Test endpoint to verify bot is working."""
    try:
        result = await bot_service.chat(
            user_id="test_user",
            message="What is artificial intelligence?",
            language="en",
            use_rag=True,
            use_web_search=False
        )
        return {
            "status": "success",
            "test_response": result["response"][:200] + "..." if len(result["response"]) > 200 else result["response"],
            "context_used": result["context_used"],
            "web_search_used": result["web_search_used"]
        }
    except Exception as e:
        logger.error(f"Test chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Test error: {str(e)}")

