"""Bot orchestration service that combines RAG, Ollama, and Web Search."""
from typing import List, Dict, Optional
from app.services.ollama_service import OllamaService
from app.services.rag_service import RAGService
from app.services.web_search_service import WebSearchService
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class BotService:
    """Service that orchestrates RAG retrieval, web search, and LLM generation."""
    
    def __init__(self):
        self.ollama = OllamaService(model=settings.OLLAMA_MODEL)
        self.rag = RAGService()
        self.web_search = WebSearchService()
        
        # System prompt for the bot
        self.system_prompt = """You are AI-300 Bot, a helpful AI tutor for a Basic Artificial Intelligence course at Kwansei Gakuin University in Japan.

Your role:
- Provide educational guidance and support for AI-300: Basic Artificial Intelligence (人工知能基礎)
- Help students understand AI concepts including: history of AI, search algorithms, game theory, probability, Bayes' theorem, and machine learning basics
- Be encouraging, patient, and educational
- Guide students to solutions rather than giving direct answers

Course Topics (14 weeks):
1-3. History of Artificial Intelligence (人工知能の歴史)
4. Search: Breadth-first and Depth-first (幅優先探索と深さ優先探索)
5. Search: Best-first, A* algorithm (最良優先探索、A*探索)
6. Game Theory and Game Trees (ゲーム理論とゲーム木探索)
7. Probability and Bayes' Theorem (確率論とベイズ定理)
8-9. Overview of AI and ML (AI・機械学習概論)
10-11. Supervised Learning (教師あり学習)
12. ML Algorithms (機械学習アルゴリズム)
13. Reinforcement Learning (強化学習)
14. Final Examination (授業中試験)

When answering:
1. Use the provided course context to give accurate, relevant answers
2. Reference specific weeks or topics when relevant
3. Encourage students to think through problems
4. Provide hints and guidance rather than complete solutions
5. Be supportive and understanding of student struggles
6. If you have web search results, use them to supplement your knowledge about AI topics
7. If you don't know something, admit it rather than guessing

Always maintain a friendly, educational tone.

IMPORTANT - BILINGUAL RESPONSE FORMAT:
You MUST respond in a BILINGUAL format. For each paragraph or concept:
1. First write in the PRIMARY language (specified below)
2. Then write the English translation

Format each response like this (paragraph by paragraph):
[Primary Language paragraph]

[English translation of that paragraph]

[Primary Language next paragraph]

[English translation]

...and so on."""

    async def chat(
        self,
        user_id: str,
        message: str,
        language: str = "en",
        conversation_history: Optional[List[Dict[str, str]]] = None,
        use_rag: bool = True,
        use_web_search: bool = True
    ) -> Dict[str, any]:
        """
        Main chat function that combines RAG, web search, and Ollama.
        
        Args:
            user_id: Student identifier
            message: User's message
            language: Preferred language (en/ja)
            conversation_history: Previous messages in conversation
            use_rag: Whether to use RAG for context retrieval
            use_web_search: Whether to search web for additional context
            
        Returns:
            Dictionary with response and metadata
        """
        try:
            # Retrieve relevant context from knowledge base
            rag_context = ""
            if use_rag:
                rag_context = self.rag.build_context(message, k=5)
                if rag_context:
                    logger.info(f"Retrieved RAG context for query: {message[:50]}...")
            
            # Check if we need web search (when RAG context is insufficient or for AI topics)
            web_context = ""
            used_web_search = False
            if use_web_search and self.web_search.is_ai_related(message):
                # Only search web if RAG context seems insufficient
                if not rag_context or len(rag_context) < 200:
                    web_context = self.web_search.build_web_context(message)
                    if web_context:
                        used_web_search = True
                        logger.info(f"Added web search context for: {message[:50]}...")
            
            # Build conversation messages
            messages = conversation_history or []
            messages.append({"role": "user", "content": message})
            
            # Enhance system prompt with context
            enhanced_prompt = self.system_prompt
            
            if rag_context:
                enhanced_prompt += f"\n\n--- Course Materials Context ---\n{rag_context}"
            
            if web_context:
                enhanced_prompt += f"\n\n--- Additional Web Research (AI Topics Only) ---\n{web_context}"
            
            # Add bilingual language instruction
            language_instructions = {
                "ja": "\n\nPRIMARY LANGUAGE: Japanese (日本語)\nRespond bilingually: Japanese first, then English translation for each paragraph.",
                "zh": "\n\nPRIMARY LANGUAGE: Chinese (中文)\nRespond bilingually: Chinese first, then English translation for each paragraph.",
                "ko": "\n\nPRIMARY LANGUAGE: Korean (한국어)\nRespond bilingually: Korean first, then English translation for each paragraph.",
                "en": "\n\nPRIMARY LANGUAGE: Japanese (日本語)\nRespond bilingually: Japanese first, then English translation for each paragraph. (Default bilingual mode)"
            }
            enhanced_prompt += language_instructions.get(language, language_instructions["ja"])
            
            # Get response from Ollama
            response = await self.ollama.chat(
                messages=messages,
                system_prompt=enhanced_prompt,
                temperature=0.7,
                max_tokens=2000
            )
            
            # Prepare response
            result = {
                "response": response,
                "user_id": user_id,
                "language": language,
                "context_used": bool(rag_context),
                "web_search_used": used_web_search,
                "model": settings.OLLAMA_MODEL
            }
            
            logger.info(f"Generated response for user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error in bot chat: {str(e)}")
            raise Exception(f"Bot service error: {str(e)}")
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of bot components."""
        ollama_healthy = await self.ollama.health_check()
        
        return {
            "ollama": ollama_healthy,
            "rag": self.rag is not None,
            "web_search": self.web_search.enabled,
            "overall": ollama_healthy and self.rag is not None
        }
    
    async def close(self):
        """Clean up resources."""
        await self.ollama.close()

