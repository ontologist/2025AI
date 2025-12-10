"""Configuration settings for the AI-300 Bot backend."""
from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Course Configuration
    COURSE_ID: str = "ai300"
    COURSE_NAME: str = "AI-300 Basic Artificial Intelligence | 人工知能基礎"
    
    # Server Configuration
    BACKEND_PORT: int = 8003
    FRONTEND_PORT: int = 3003
    FIXED_IP: Optional[str] = None
    
    # GitHub Configuration
    GITHUB_REPO_URL: str = "https://github.com/ontologist/2025AI.git"
    GITHUB_PAGES_URL: str = "https://2025ai.tijerino.ai/"
    
    # Ollama Configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:latest"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"
    
    # RAG Configuration
    CHROMA_DB_PATH: str = "./chroma_db"
    KNOWLEDGE_BASE_PATH: str = "./knowledge_base"
    
    @property
    def knowledge_base_path_absolute(self) -> Path:
        """Get absolute path to knowledge base."""
        base = Path(__file__).parent.parent.parent
        return base / self.KNOWLEDGE_BASE_PATH.lstrip("./")
    
    # Web Search Configuration
    WEB_SEARCH_ENABLED: bool = True
    WEB_SEARCH_MAX_RESULTS: int = 3
    
    # Security
    SECRET_KEY: str = "ai300-secret-key-change-in-production"

    # Assignment Grading / Resource Limits
    ASSIGNMENT_RESOURCE_LIMIT: float = float(os.getenv("ASSIGNMENT_RESOURCE_LIMIT", "0.2"))
    EMAIL_DOMAIN: str = os.getenv("EMAIL_DOMAIN", "kwansei.ac.jp")
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Create settings instance
settings = Settings()

# Ensure directories exist
Path(settings.CHROMA_DB_PATH).mkdir(parents=True, exist_ok=True)
Path(settings.KNOWLEDGE_BASE_PATH).mkdir(parents=True, exist_ok=True)
Path(settings.LOG_FILE).parent.mkdir(parents=True, exist_ok=True)

