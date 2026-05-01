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
    
    # LLM Provider Settings (OpenRouter or OpenAI)
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")  # "openai" or "openrouter"
    
    # OpenAI Settings (for both direct OpenAI and embeddings)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # OpenRouter Settings
    OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    
    # Model Settings
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")  # For OpenAI: "gpt-4o-mini", For OpenRouter: "openai/gpt-4o-mini"
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.1"))
    
    MAX_TABLES_PER_SLOT: int = 5
    
    MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", "5"))
    
    # API Server settings
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
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
    
    @property
    def api_host(self) -> str:
        """API server host."""
        return self.API_HOST
    
    @property
    def api_port(self) -> int:
        """API server port."""
        return self.API_PORT
    
    @property
    def log_level(self) -> str:
        """Logging level."""
        return self.LOG_LEVEL
    
    @property
    def llm_provider(self) -> str:
        """LLM provider type."""
        return self.LLM_PROVIDER
    
    @property
    def openrouter_api_key(self) -> Optional[str]:
        """OpenRouter API key."""
        return self.OPENROUTER_API_KEY
    
    @property
    def openrouter_base_url(self) -> str:
        """OpenRouter API base URL."""
        return self.OPENROUTER_BASE_URL
    
    def validate(self) -> None:
        """Validate critical settings."""
        # Check LLM provider settings
        if self.LLM_PROVIDER == "openrouter":
            if not self.OPENROUTER_API_KEY:
                raise ValueError(
                    "OPENROUTER_API_KEY is not set. "
                    "Please set it in your .env file or environment variables."
                )
            # OpenRouter still needs OpenAI for embeddings
            if not self.OPENAI_API_KEY:
                raise ValueError(
                    "OPENAI_API_KEY is also required for embeddings when using OpenRouter. "
                    "Please set both OPENROUTER_API_KEY and OPENAI_API_KEY."
                )
        else:
            # Direct OpenAI usage
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
