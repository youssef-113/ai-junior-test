"""
NovaBite — FastAPI Server

Exposes the multi-agent system via HTTP endpoints.
"""

import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config.settings import get_settings
from agents.orchestrator import chat as orchestrator_chat
from memory import memory_store
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Verify FAISS index exists on startup."""
    index_path = Path(settings.faiss_index_path)
    if not index_path.exists():
        logger.warning(
            f"FAISS index not found at '{index_path}'. "
            "RAG queries will fail until ingestion is run: python -m rag.ingest"
        )
    else:
        logger.info(f"FAISS index found at '{index_path}' ✓")
    yield

app = FastAPI(
    title="NovaBite AI Restaurant Assistant",
    description="Multi-agent RAG system for NovaBite restaurant chain",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str | None = Field(None, description="Leave empty to start a new session")


class ChatResponse(BaseModel):
    response: str
    intent: str
    session_id: str
    timestamp: str
    confidence: float = Field(default=0.0, description="Confidence score of the response")
    tools_used: list = Field(default_factory=list, description="Tools used to generate response")
    user_id: str = Field(default="unknown", description="User identifier")


class IngestRequest(BaseModel):
    confirm: bool = Field(..., description="Set to true to confirm re-ingestion")


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "NovaBite AI Restaurant Assistant",
        "status": "running",
        "version": "1.0.0",
    }


@app.get("/health", tags=["Health"])
async def health():
    index_exists = Path(settings.faiss_index_path).exists()
    return {
        "status": "healthy",
        "faiss_index": "ready" if index_exists else "not_found — run /ingest",
        "active_sessions": len(memory_store.list_sessions()),
    }


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    Send a message to the NovaBite AI assistant.

    - If session_id is omitted, a new session is created automatically.
    - Include the same session_id across turns to maintain memory.
    """
    session_id = request.session_id or str(uuid.uuid4())

    try:
        result = orchestrator_chat(
            user_message=request.message,
            session_id=session_id,
        )
        # Convert OrchestratorResponse to ChatResponse
        return ChatResponse(
            response=result.response,
            intent=result.intent,
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            confidence=result.confidence,
            tools_used=result.toolsUsed,
            user_id=result.userId,
        )
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error. Please try again.")


@app.post("/ingest", tags=["Admin"])
async def ingest_documents(request: IngestRequest):
    """
    Re-run the RAG ingestion pipeline.
    Reloads all documents from the knowledge directory and rebuilds the FAISS index.
    """
    if not request.confirm:
        raise HTTPException(status_code=400, detail="Set confirm=true to run ingestion.")

    try:
        from RAG.ingest import run_ingestion
        from RAG.retriever import invalidate_cache
        invalidate_cache()
        run_ingestion()
        return {"status": "success", "message": "Ingestion pipeline completed. FAISS index rebuilt."}
    except Exception as e:
        logger.error(f"Ingestion error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@app.delete("/session/{session_id}", tags=["Session"])
async def clear_session(session_id: str):
    """Clear conversation memory for a specific session."""
    memory_store.clear(session_id)
    return {"status": "cleared", "session_id": session_id}


@app.get("/sessions", tags=["Session"])
async def list_sessions():
    """List all active session IDs."""
    return {"sessions": memory_store.list_sessions()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.server:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level=settings.log_level.lower(),
    )
