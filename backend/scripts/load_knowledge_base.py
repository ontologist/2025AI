"""Script to load course documents into the RAG knowledge base."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.rag_service import RAGService
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Load all course documents into the knowledge base."""
    logger.info("=" * 60)
    logger.info("AI-300 Knowledge Base Loading")
    logger.info("=" * 60)
    logger.info(f"Knowledge base path: {settings.KNOWLEDGE_BASE_PATH}")
    logger.info(f"ChromaDB path: {settings.CHROMA_DB_PATH}")
    logger.info(f"Course ID: {settings.COURSE_ID}")
    
    # Initialize RAG service
    logger.info("\nInitializing RAG service...")
    rag = RAGService()
    
    # Load documents
    try:
        logger.info("\nIngesting documents...")
        chunk_count = rag.ingest_documents()
        logger.info(f"\n✅ Successfully loaded {chunk_count} document chunks")
        
        # Get collection info
        info = rag.get_collection_info()
        logger.info(f"\nCollection info:")
        logger.info(f"  - Collection name: {info.get('collection_name', 'N/A')}")
        logger.info(f"  - Document count: {info.get('document_count', 0)}")
        logger.info(f"  - Persist directory: {info.get('persist_directory', 'N/A')}")
        
        # Test retrieval
        logger.info("\nTesting retrieval...")
        test_query = "What is artificial intelligence?"
        test_context = rag.build_context(test_query, k=2)
        if test_context:
            logger.info(f"✅ Retrieval test successful!")
            logger.info(f"Sample context (first 300 chars): {test_context[:300]}...")
        else:
            logger.warning("⚠ No context retrieved for test query")
        
    except Exception as e:
        logger.error(f"❌ Error loading knowledge base: {str(e)}")
        raise


if __name__ == "__main__":
    main()

