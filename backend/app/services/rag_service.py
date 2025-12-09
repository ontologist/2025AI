"""RAG (Retrieval-Augmented Generation) service using ChromaDB and Ollama embeddings."""
import chromadb
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from pathlib import Path
from typing import List, Dict, Optional
from app.core.config import settings
import logging
import os

logger = logging.getLogger(__name__)


class RAGService:
    """Service for RAG operations using ChromaDB."""
    
    def __init__(self, persist_directory: Optional[str] = None):
        self.persist_directory = persist_directory or settings.CHROMA_DB_PATH
        
        # Get absolute path to knowledge base
        kb_path = Path(settings.KNOWLEDGE_BASE_PATH)
        if not kb_path.is_absolute():
            # If relative, make it relative to backend directory
            backend_dir = Path(__file__).parent.parent.parent
            self.knowledge_base_path = (backend_dir / kb_path).resolve()
        else:
            self.knowledge_base_path = kb_path.resolve()
        
        # Initialize embeddings
        self.embeddings = OllamaEmbeddings(
            model=settings.OLLAMA_EMBEDDING_MODEL,
            base_url=settings.OLLAMA_BASE_URL
        )
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection_name = f"course_knowledge_{settings.COURSE_ID}"
        
        # Create or get collection
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"Loaded existing collection: {self.collection_name}")
        except:
            self.collection = self.client.create_collection(name=self.collection_name)
            logger.info(f"Created new collection: {self.collection_name}")
        
        # Initialize vectorstore with persistence
        self.vectorstore = Chroma(
            client=self.client,
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory
        )
        
        # Text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
    
    def ingest_documents(self, directory: Optional[str] = None) -> int:
        """Load and index all course documents from the knowledge base."""
        source_dir = Path(directory) if directory else self.knowledge_base_path
        
        if not source_dir.exists():
            logger.warning(f"Knowledge base directory does not exist: {source_dir}")
            return 0
        
        logger.info(f"Loading documents from: {source_dir}")
        
        documents = []
        file_extensions = ['.md', '.txt', '.html', '.yaml', '.yml', '.py', '.json', '.csv']
        
        # Walk through directory and load files
        for root, dirs, files in os.walk(str(source_dir)):
            for file in files:
                if any(file.lower().endswith(ext) for ext in file_extensions):
                    file_path = os.path.join(root, file)
                    try:
                        loader = TextLoader(file_path, encoding='utf-8')
                        docs = loader.load()
                        documents.extend(docs)
                    except Exception as e:
                        logger.debug(f"Could not load {file_path}: {e}")
                        continue
        
        logger.info(f"Loaded {len(documents)} documents")
        
        if not documents:
            logger.warning("No documents found to index")
            return 0
        
        try:
            # Split documents into chunks
            texts = self.text_splitter.split_documents(documents)
            logger.info(f"Split into {len(texts)} text chunks")
            
            # Add to vectorstore
            self.vectorstore.add_documents(texts)
            self.vectorstore.persist()
            
            logger.info(f"Successfully indexed {len(texts)} chunks")
            return len(texts)
            
        except Exception as e:
            logger.error(f"Error ingesting documents: {str(e)}")
            raise
    
    def retrieve_context(self, query: str, k: int = 5) -> List[Dict]:
        """Retrieve relevant context for a query."""
        try:
            docs = self.vectorstore.similarity_search_with_score(query, k=k)
            
            results = []
            for doc, score in docs:
                results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score)
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}")
            return []
    
    def build_context(self, query: str, k: int = 5) -> str:
        """Build formatted context string from retrieved documents."""
        contexts = self.retrieve_context(query, k)
        
        if not contexts:
            return ""
        
        formatted = []
        for i, ctx in enumerate(contexts, 1):
            source = ctx["metadata"].get("source", "Unknown")
            content = ctx["content"]
            formatted.append(f"[Context {i} from {source}]:\n{content}")
        
        return "\n\n".join(formatted)
    
    def get_collection_info(self) -> Dict:
        """Get information about the vector database collection."""
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {str(e)}")
            return {"error": str(e)}

