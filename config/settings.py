"""
NovaBite Configuration Settings
Centralized configuration for RAG, tools, and agents.
"""

import os
from pathlib import Path
from functools import lru_cache
from typing import Optional


class Settings:
    """Application settings loaded from environment variables."""
    
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    
    KNOWLEDGE_DIR: str = str(DATA_DIR / "Knowledge")
    FAISS_INDEX_PATH: str = str(DATA_DIR / "faiss_index")
    
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "50"))
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
    
    RETRIEVAL_TOP_K: int = int(os.getenv("RETRIEVAL_TOP_K", "4"))
    RETRIEVAL_SCORE_THRESHOLD: float = float(os.getenv("RETRIEVAL_SCORE_THRESHOLD", "0.75"))
    
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.1"))
    
    MAX_TABLES_PER_SLOT: int = 5
    
    MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", "5"))
    
    @property
    def knowledge_dir(self) -> str:
        """Knowledge documents directory."""
        return self.KNOWLEDGE_DIR
    
    @property
    def faiss_index_path(self) -> str:
        """FAISS index storage path."""
        return self.FAISS_INDEX_PATH
    
    @property
    def chunk_size(self) -> int:
        """Document chunk size for splitting."""
        return self.CHUNK_SIZE
    
    @property
    def chunk_overlap(self) -> int:
        """Overlap between chunks."""
        return self.CHUNK_OVERLAP
    
    @property
    def embedding_model(self) -> str:
        """OpenAI embedding model name."""
        return self.EMBEDDING_MODEL
    
    @property
    def openai_api_key(self) -> Optional[str]:
        """OpenAI API key."""
        return self.OPENAI_API_KEY
    
    @property
    def retrieval_top_k(self) -> int:
        """Number of documents to retrieve."""
        return self.RETRIEVAL_TOP_K
    
    @property
    def retrieval_score_threshold(self) -> float:
        """Minimum similarity score for retrieval."""
        return self.RETRIEVAL_SCORE_THRESHOLD
    
    @property
    def llm_model(self) -> str:
        """LLM model for agents."""
        return self.LLM_MODEL
    
    @property
    def temperature(self) -> float:
        """LLM temperature."""
        return self.TEMPERATURE
    
    @property
    def max_iterations(self) -> int:
        """Max agent iterations."""
        return self.MAX_ITERATIONS
    
    def validate(self) -> None:
        """Validate critical settings."""
        if not self.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY is not set. "
                "Please set it in your .env file or environment variables."
            )
        
        Path(self.KNOWLEDGE_DIR).mkdir(parents=True, exist_ok=True)
        Path(self.FAISS_INDEX_PATH).mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses LRU cache to avoid reloading on every call.
    """
    settings = Settings()
    settings.validate()
    return settings
