"""
NovaBite — FAISS Retriever Setup

Loads the persisted FAISS index and returns a configured retriever.
"""

import logging
from pathlib import Path

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_vectorstore_cache: FAISS | None = None


def load_vectorstore() -> FAISS:
    """Load FAISS index from disk. Raises if index not found."""
    global _vectorstore_cache
    if _vectorstore_cache is not None:
        return _vectorstore_cache

    index_path = settings.faiss_index_path
    if not Path(index_path).exists():
        raise FileNotFoundError(
            f"FAISS index not found at '{index_path}'. "
            "Run ingestion first: python -m rag.ingest"
        )

    embeddings = OpenAIEmbeddings(
        model=settings.embedding_model,
        openai_api_key=settings.openai_api_key,
    )
    _vectorstore_cache = FAISS.load_local(
        index_path,
        embeddings,
        allow_dangerous_deserialization=True,
    )
    logger.info(f"FAISS index loaded from {index_path}")
    return _vectorstore_cache


def get_retriever():
    """
    Return a configured retriever with score threshold filtering.

    - top_k=4: returns 4 most relevant chunks.
    - score_threshold=0.75: discards low-confidence matches.
      If no chunk scores above this, the RAG agent will NOT
      hallucinate — it returns a "don't know" response instead.
    """
    vectorstore = load_vectorstore()
    retriever = vectorstore.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={
            "k": settings.retrieval_top_k,
            "score_threshold": settings.retrieval_score_threshold,
        },
    )
    return retriever


def invalidate_cache() -> None:
    """Clear cached vectorstore (used after re-ingestion)."""
    global _vectorstore_cache
    _vectorstore_cache = None
    logger.info("Vectorstore cache invalidated.")
