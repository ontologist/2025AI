"""Web search service for AI-related queries using DuckDuckGo."""
from typing import List, Dict, Optional
from duckduckgo_search import DDGS
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# AI-related keywords to filter searches
AI_KEYWORDS = [
    "artificial intelligence", "machine learning", "deep learning", "neural network",
    "AI", "ML", "NLP", "natural language processing", "computer vision",
    "reinforcement learning", "supervised learning", "unsupervised learning",
    "clustering", "classification", "regression", "decision tree",
    "random forest", "gradient descent", "backpropagation", "transformer",
    "GPT", "BERT", "LLM", "large language model", "chatbot",
    "data science", "algorithm", "turing test", "expert system",
    "bayesian", "probability", "search algorithm", "A*", "minimax",
    "game tree", "heuristic", "alpha-beta pruning",
    "人工知能", "機械学習", "深層学習", "ニューラルネットワーク",
    "強化学習", "教師あり学習", "教師なし学習", "クラスタリング",
    "ベイズ", "確率", "探索", "ゲーム木"
]


class WebSearchService:
    """Service for searching the web for AI-related information."""
    
    def __init__(self):
        self.max_results = settings.WEB_SEARCH_MAX_RESULTS
        self.enabled = settings.WEB_SEARCH_ENABLED
    
    def is_ai_related(self, query: str) -> bool:
        """Check if the query is related to AI topics."""
        query_lower = query.lower()
        return any(keyword.lower() in query_lower for keyword in AI_KEYWORDS)
    
    def search(self, query: str, max_results: Optional[int] = None) -> List[Dict]:
        """
        Search the web for AI-related information.
        
        Args:
            query: The search query
            max_results: Maximum number of results to return
            
        Returns:
            List of search results with title, body, and href
        """
        if not self.enabled:
            logger.info("Web search is disabled")
            return []
        
        results_limit = max_results or self.max_results
        
        try:
            # Add AI context to the query for better results
            enhanced_query = f"{query} artificial intelligence machine learning"
            
            with DDGS() as ddgs:
                results = list(ddgs.text(
                    enhanced_query,
                    max_results=results_limit,
                    safesearch='moderate'
                ))
            
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "title": result.get("title", ""),
                    "body": result.get("body", ""),
                    "url": result.get("href", ""),
                    "source": "web_search"
                })
            
            logger.info(f"Web search returned {len(formatted_results)} results for: {query}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Web search error: {str(e)}")
            return []
    
    def build_web_context(self, query: str) -> str:
        """Build formatted context string from web search results."""
        results = self.search(query)
        
        if not results:
            return ""
        
        formatted = ["[Web Search Results]:"]
        for i, result in enumerate(results, 1):
            formatted.append(f"\n{i}. **{result['title']}**")
            formatted.append(f"   {result['body']}")
            formatted.append(f"   Source: {result['url']}")
        
        return "\n".join(formatted)

