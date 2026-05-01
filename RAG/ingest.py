"""
Loads knowledge documents → chunks → embeds → stores in FAISS.
"""

import os
import logging
from pathlib import Path

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def load_documents(knowledge_dir: str) -> list:
    """Load all .txt files from the knowledge directory."""
    loader = DirectoryLoader(
        knowledge_dir,
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
        show_progress=True,
    )
    docs = loader.load()
    logger.info(f"Loaded {len(docs)} document(s) from {knowledge_dir}")
    return docs


def chunk_documents(docs: list) -> list:
    """
    Split documents using RecursiveCharacterTextSplitter.
    Chunking strategy:
    - chunk_size=500: Keeps each chunk semantically focused while
      retaining enough context (dish name + description + allergens).
    - chunk_overlap=50: Prevents context loss at boundaries.
    - separators respect paragraph > sentence > word hierarchy.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )
    chunks = splitter.split_documents(docs)
    logger.info(f"Created {len(chunks)} chunks from {len(docs)} document(s)")
    return chunks


def build_vectorstore(chunks: list) -> FAISS:
    """Embed chunks and build FAISS vector store."""
    embeddings = OpenAIEmbeddings(
        model=settings.embedding_model,
        openai_api_key=settings.openai_api_key,
    )
    vectorstore = FAISS.from_documents(chunks, embeddings)
    logger.info("FAISS vector store built successfully")
    return vectorstore


def save_vectorstore(vectorstore: FAISS, index_path: str) -> None:
    """Persist FAISS index to disk."""
    Path(index_path).mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(index_path)
    logger.info(f"FAISS index saved to {index_path}")


def run_ingestion() -> FAISS:
    """Full ingestion pipeline: load → chunk → embed → save."""
    logger.info("Starting NovaBite RAG ingestion pipeline...")

    docs = load_documents(settings.knowledge_dir)
    if not docs:
        raise ValueError(f"No documents found in {settings.knowledge_dir}")

    chunks = chunk_documents(docs)
    vectorstore = build_vectorstore(chunks)
    save_vectorstore(vectorstore, settings.faiss_index_path)

    logger.info("Ingestion pipeline completed successfully.")
    return vectorstore


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_ingestion()
