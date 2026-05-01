#!/bin/bash
# NovaBite Docker Entrypoint Script
# Handles RAG ingestion on first run and starts the API server
 
set -e
 
echo "========================================"
echo "NovaBite AI Restaurant Assistant"
echo "========================================"
 
# Check if FAISS index exists, if not run ingestion
if [ ! -d "/app/data/faiss_index" ] || [ -z "$(ls -A /app/data/faiss_index 2>/dev/null)" ]; then
    echo "📚 FAISS index not found. Running RAG ingestion..."
    python -m RAG.ingest
    echo "✅ Ingestion complete!"
else
    echo "✅ FAISS index found. Skipping ingestion."
fi
 
echo ""
echo "🚀 Starting NovaBite API Server..."
echo ""
 
# Execute the main command (passed from Dockerfile or docker-compose)
exec "$@"