# 🍽️ NovaBite AI Restaurant Assistant

A production-grade multi-agent RAG system for NovaBite Restaurants, built with LangChain, FastAPI, and Docker.

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)](https://fastapi.tiangolo.com)
[![LangChain](https://img.shields.io/badge/LangChain-0.1+-orange)](https://langchain.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://docker.com)

---

## 📋 Table of Contents

1. [Architecture Explanation](#-architecture-explanation)
2. [RAG Design Decisions](#-rag-design-decisions)
3. [Tool Simulation/MCP Integration](#-tool-simulation--mcp-integration)
4. [Memory Design](#-memory-design)
5. [Example Queries & Outputs](#-example-queries--outputs)
6. [Assumptions Made](#-assumptions-made)
7. [Quick Start](#-quick-start)

---

## 🏗️ Architecture Explanation

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Layer                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   cURL/HTTP │  │  Streamlit  │  │   Swagger   │         │
│  │    Client   │  │     UI      │  │    UI       │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
└─────────┼────────────────┼────────────────┼─────────────────┘
          │                │                │
          └────────────────┴────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│              FastAPI Server (Port 8000)                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Main Orchestrator Agent                     │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │  │
│  │  │   Intent     │  │   Router     │  │  Response  │  │  │
│  │  │  Classifier  │──►│   (Route)    │──►│  Merger    │  │  │
│  │  └──────────────┘  └──────────────┘  └────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                 │
│         ┌─────────────────┼─────────────────┐              │
│         ▼                 ▼                 ▼              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  RAG Agent   │  │  Operations  │  │  Session     │      │
│  │  (Knowledge) │  │   Agent      │  │  Memory      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
         │                    │
         ▼                    ▼
┌─────────────────┐  ┌─────────────────────────┐
│  FAISS Vector   │  │  Tool Functions         │
│  Database       │  │  ┌──────────────────┐  │
│                 │  │  │ check_table_     │  │
│  ┌───────────┐  │  │  │ availability()   │  │
│  │ Embeddings│  │  │  └──────────────────┘  │
│  │ (OpenAI)  │  │  │  ┌──────────────────┐  │
│  └───────────┘  │  │  │ book_table()     │  │
│  ┌───────────┐  │  │  └──────────────────┘  │
│  │  Chunks   │  │  │  ┌──────────────────┐  │
│  │ (500char) │  │  │  │ get_today_       │  │
│  └───────────┘  │  │  │ special()        │  │
└─────────────────┘  │  └──────────────────┘  │
                     │  ┌──────────────────┐  │
                     │  │ check_loyalty_   │  │
                     │  │ points()         │  │
                     │  └──────────────────┘  │
                     └─────────────────────────┘
```

### Agent Responsibilities

#### 1. Main Orchestrator Agent
- **Intent Classification**: Uses keyword + LLM-based classification into KNOWLEDGE, OPERATIONS, HYBRID, CLARIFY, or FAREWELL intents
- **Routing**: Delegates to appropriate sub-agent based on classified intent
- **Response Merging**: Combines responses from multiple agents for HYBRID queries
- **Validation**: Ensures all responses conform to `OrchestratorResponse` schema

#### 2. RAG Knowledge Agent
- Handles menu, allergen, policy, and general information queries
- Uses FAISS retrieval with score threshold filtering
- Implements hallucination prevention through strict prompt engineering

#### 3. Operations Agent (Tool-Based)
- Implements 4 MCP-style tools via LangChain AgentExecutor
- Direct database access for validation and enrichment
- Maintains tool state and booking confirmations

---

## 🔍 RAG Design Decisions

### 1. Chunking Strategy

**Choice**: RecursiveCharacterTextSplitter with:
- `chunk_size=500` characters
- `chunk_overlap=50` characters  
- Separators: `["\n\", "\n", ". ", " ", ""]`

**Justification**:
- **500 characters**: Keeps each chunk semantically focused while retaining enough context (dish name + description + allergens + price)
- **50 overlap**: Prevents context loss at boundaries between chunks
- **Hierarchical separators**: Respects document structure (paragraph > sentence > word), ensuring natural break points

### 2. Embedding Model

**Choice**: OpenAI `text-embedding-ada-002`

**Justification**:
- Proven performance for semantic similarity tasks
- 1536-dimensional vectors capture nuanced relationships
- Consistent with LLM provider (OpenAI) for compatibility
- Industry standard for production RAG systems

**Alternative Considered**: HuggingFace `all-MiniLM-L6-v2` (free, local, but lower quality)

### 3. Vector Database

**Choice**: FAISS (Facebook AI Similarity Search)

**Justification**:
- Local execution (no external service dependency)
- Fast approximate nearest neighbor search
- Efficient memory usage for small-to-medium datasets
- Easy persistence to disk for Docker volumes
- No network latency vs. cloud vector DBs

### 4. Retrieval Strategy

**Choice**: Similarity Score Threshold with:
- `top_k=4` documents
- `score_threshold=0.75`

**Justification**:
- **Threshold filtering**: Discards low-confidence matches, preventing hallucinations from irrelevant chunks
- **Top-4**: Balances context richness with token limits
- **Grounded responses**: If no chunks score above 0.75, agent returns "I don't have that information" instead of hallucinating

### 5. Hallucination Prevention

**Strategy**:
1. Strict system prompt: "ONLY use information from the context provided. Do NOT invent menu items, prices, or policies."
2. Fallback response: "I don't have that information in our knowledge base. Please contact us directly at info@novabite.com or call your nearest branch."
3. Confidence scoring: 0.85 for grounded responses, 0.3 for fallback
4. Source tracking: Returns document sources in response metadata

---

## 🛠️ Tool Simulation & MCP Integration

### Architecture: Simulated MCP Server

We implemented **simulated MCP-style tools** rather than connecting to a real external server. This approach:
- Demonstrates tool-calling patterns without external dependencies
- Enables offline testing and development
- Provides deterministic responses for evaluation
- Follows MCP tool specification format

### Implemented Tools

#### 1. `check_table_availability`
```python
Input:  CheckAvailabilityInput(date, time, branch, party_size)
Output: AvailabilityResponse(available, reason, alternative_slots)
Logic:  Validates datetime format → Checks BOOKING database for conflicts → 
        Returns availability status with alternative time suggestions
```

#### 2. `book_table`
```python
Input:  BookTableInput(name, phone, email, date, time, branch, party_size, special_event)
Output: BookingConfirmation(confirmation_id, status, details)
Logic:  Generates UUID confirmation → Validates party size (2-20) → 
        Checks availability → Inserts into BOOKING database
```

#### 3. `get_today_special`
```python
Input:  GetTodaySpecialInput(branch, day_of_week)
Output: TodaySpecialResponse(dish_name, description, price, tags)
Logic:  Validates branch → Looks up SPECIALDB by weekday → 
        Returns chef's special with dietary tags (vegan, gluten-free, etc.)
```

#### 4. `check_loyalty_points`
```python
Input:  CheckLoyaltyPointsInput(user_id)
Output: LoyaltyPointsResponse(points, tier, next_tier_points, benefits)
Logic:  Validates user_id format (USRXXXX) → Queries LOYALTYDB → 
        Calculates points to next tier based on PLANS config
```

### Tool Integration with LangChain

```python
# Tools decorated with @tool and registered in ALL_TOOLS
from langchain.tools import tool

@tool
def check_table_availability(input_data: CheckAvailabilityInput) -> AvailabilityResponse:
    """Check if tables are available for a given date/time/branch"""
    # Implementation

# Agent uses OpenAI function calling to select and invoke tools
agent = create_openai_tools_agent(llm, ALL_TOOLS, prompt)
executor = AgentExecutor(agent=agent, tools=ALL_TOOLS)
```

### Database Schema (Simulated)

**BOOKING**: List of reservation dictionaries with confirmation IDs
**LOYALTYDB**: User profiles with points, tiers, and booking history  
**SPECIALDB**: Branch-specific daily specials by weekday
**PLANS**: Loyalty tier definitions (base/pro/premium benefits)
**EVENTS**: Special event types for bookings (birthday, anniversary, etc.)

---

## 🧠 Memory Design

### Architecture: Session-Based Conversation Memory

```
┌──────────────────────────────────────────────┐
│         Session Memory Store                  │
│  ┌────────────────────────────────────────┐  │
│  │  Session ID: "sess-uuid-123"          │  │
│  │  Created: "2024-01-15T10:30:00Z"      │  │
│  │                                        │  │
│  │  Messages:                             │  │
│  │  ├─ Human: "Book a table"             │  │
│  │  ├─ AI:   "For how many people?"      │  │
│  │  ├─ Human: "For 4"                    │  │
│  │  └─ AI:   "Booked! Confirmation: ..." │  │
│  └────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘
```

### Implementation Details

**Storage**: In-memory dictionary with session IDs as keys
- Uses LangChain's `ChatMessageHistory` for message management
- Stores `HumanMessage` and `AIMessage` objects
- Accessible via `get_session_history(session_id)` function

**Retrieval**: Last 3 exchanges (6 messages) sent to agents
- Provides context for follow-up questions without exceeding token limits
- Enables multi-turn conversations about same topic

**Persistence**: Session data is ephemeral (in-memory only)
- Resets on server restart
- Can be extended to Redis/database for production scaling

**Privacy**: No PII stored permanently
- User IDs extracted from messages but not persisted
- Booking data stored separately in BOOKING database

### Memory Integration in Orchestrator

```python
history = get_session_history(session_id)
chat_history = history.messages  # Retrieved for context

# After getting response
history.add_user_message(user_message)
history.add_ai_message(response)
```

---

## 💬 Example Queries & Outputs

### 1. Knowledge Query (RAG)

**Input**: "Do you have vegan pasta options?"

**Intent Classification**: KNOWLEDGE (confidence: 0.95)

**RAG Retrieval**:
- Source: `data/Knowledge/menu_nacrCity.txt`
- Chunks: 2 relevant passages about vegan dishes
- Score: 0.82 (above 0.75 threshold)

**Output**:
```json
{
  "userId": "unknown",
  "response": "Yes, we have vegan pasta! Our Linguine Primavera is completely vegan, featuring seasonal vegetables tossed with garlic olive oil and fresh herbs. We also offer a vegan Tomato Basil Pasta made with ripe tomatoes, fresh basil, and olive oil. Both are priced at 190-200 EGP.",
  "intent": "KNOWLEDGE",
  "toolsUsed": ["rag_knowledge"],
  "confidence": 0.85,
  "context": {
    "sources": ["menu_nacrCity.txt"],
    "grounded": true,
    "source_count": 2
  }
}
```

---

### 2. Operations Query - Check Availability

**Input**: "Check table availability at nacrCity for 2024-05-15 at 19:00"

**Intent Classification**: OPERATIONS (confidence: 0.92)

**Tool Execution**:
- Tool: `check_table_availability`
- Parameters: date="2024-05-15", time="19:00", branch="nacrCity", party_size=2
- Result: Available

**Output**:
```json
{
  "userId": "unknown",
  "response": "Good news! We have tables available at Nacr City on May 15, 2024 at 7:00 PM. Would you like to make a reservation?",
  "intent": "OPERATIONS",
  "toolsUsed": ["check_table_availability"],
  "confidence": 0.9,
  "context": {
    "query": "Check table availability at nacrCity for 2024-05-15 at 19:00",
    "tool_execution_success": true
  }
}
```

---

### 3. Operations Query - Book Table

**Input**: "Book a table for 4 at ShroukCity tomorrow at 8pm, name: John, phone: 01234567890"

**Intent Classification**: OPERATIONS (confidence: 0.93)

**Tool Chain**:
1. `check_table_availability` → Available ✓
2. `book_table` → Confirmation generated

**Output**:
```json
{
  "userId": "unknown",
  "response": "Perfect! Your table has been booked. Here are your confirmation details:\n\nConfirmation ID: NOVA-20240515-001\nName: John\nDate: 2024-05-16\nTime: 20:00\nBranch: Shrouk City\nParty Size: 4 people\n\nPlease arrive 10 minutes early. We look forward to seeing you!",
  "intent": "OPERATIONS",
  "toolsUsed": ["check_table_availability", "book_table"],
  "confidence": 0.9,
  "context": {
    "confirmation_id": "NOVA-20240515-001"
  }
}
```

---

### 4. Operations Query - Loyalty Check

**Input**: "What are my loyalty points? (USR0001)"

**Intent Classification**: OPERATIONS (confidence: 0.88)

**Tool Execution**:
- Tool: `check_loyalty_points`
- User: USR0001 (youssef bassiony)
- Result: 450 points, pro tier

**Output**:
```json
{
  "userId": "USR0001",
  "response": "Hello youssef! You currently have 450 loyalty points, placing you in our PRO tier. You're 300 points away from reaching PREMIUM tier (750 points), which unlocks exclusive benefits like priority reservations and complimentary appetizers!",
  "intent": "OPERATIONS",
  "toolsUsed": ["check_loyalty_points"],
  "confidence": 0.9
}
```

---

### 5. Hybrid Query (Knowledge + Operations)

**Input**: "Do you have gluten-free options and can I book a table for tonight?"

**Intent Classification**: HYBRID (confidence: 0.85)

**Execution**: Both RAG Agent + Operations Agent run in parallel

**Output**:
```json
{
  "userId": "unknown",
  "response": "Yes, we have several gluten-free options including Grilled Salmon, Quinoa Salad, and our signature Chickpea & Avocado Bowl. All gluten-free dishes are clearly marked with (GF) on our menu.\n\nRegarding your operational request:\nTo book a table for tonight, I'll need a few details: Which branch (nacrCity or ShroukCity)? What time? And how many people will be dining?",
  "intent": "HYBRID",
  "toolsUsed": ["rag_knowledge", "operations_agent"],
  "confidence": 0.8
}
```

---

### 6. Session Memory (Follow-up)

**Session ID**: "test-session-123"

**Turn 1**: "I want to book a table"
→ AI: "Sure! Which branch, date, time, and how many people?"

**Turn 2**: "For 2 people at nacrCity"
→ AI: "Got it - nacrCity for 2 people. What date and time?"

**Turn 3**: "Tomorrow at 7pm"
→ AI: "Perfect! Let me check availability and book that for you..."

Memory enables context-aware follow-ups without repeating branch/party size.

---

## 📋 Assumptions Made

### 1. Data & Knowledge
- **Static Knowledge Base**: Menu items, prices, and policies are static in text files. In production, these would connect to a CMS or POS system API.
- **Sample Data**: Only 2 branches (nacrCity, ShroukCity) and 3 sample users (USR0001-0003) are implemented for demonstration.
- **English Only**: System assumes English queries. Multi-language support would require translation layer.

### 2. Tool Simulation
- **In-Memory Database**: All booking and loyalty data is stored in Python dictionaries (`BOOKING`, `LOYALTYDB`). Production would use PostgreSQL/MySQL.
- **No Real-Time Inventory**: Table availability is simulated based on hardcoded capacity (5 tables per slot), not connected to actual reservation system.
- **No Payment Integration**: Bookings don't require deposits or payment processing.

### 3. RAG & Embeddings
- **OpenAI Dependency**: Requires valid OpenAI API key with available credits. Free tier ($5) is sufficient for testing.
- **No Embedding Updates**: FAISS index is built once at startup. Adding new documents requires re-ingestion (via `/ingest` endpoint).
- **CPU-Only**: FAISS uses CPU. GPU acceleration would speed up ingestion for large datasets.

### 4. Architecture
- **Single Server**: All components (API, RAG, Tools) run in one container. Production would separate:
  - API servers (horizontal scaling)
  - Vector database (Pinecone/Weaviate)
  - Tool services (microservices)
  - Redis for distributed memory
- **No Authentication**: API endpoints are open. Production would add JWT/API key auth.

### 5. Deployment
- **Docker-First**: Optimized for containerized deployment. Local development without Docker requires manual dependency management.
- **Environment Variables**: All secrets (OpenAI key) passed via environment, never committed to code.
- **Ephemeral Storage**: Session memory resets on container restart. For persistence, mount Redis or database volume.

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API Key ([Get one here](https://platform.openai.com/api-keys))

### 1. Clone & Setup

```bash
git clone <your-repo-url>
cd ai-junior-test

# Setup environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 2. Run with Docker

```bash
# Build and start
docker-compose up --build -d

# Watch logs (first run builds FAISS index ~2-3 min)
docker-compose logs -f novabite-api

# Wait for: "FAISS index saved successfully"
```

### 3. Test the API

```bash
# Health check
curl http://localhost:8000/health

# Test query
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Do you have vegan pasta?"}'
```

### 4. Run Streamlit UI (Optional)

```bash
# Terminal 1: Start API (already running via Docker)

# Terminal 2: Start UI
pip install streamlit
streamlit run streamlit_app.py

# Open http://localhost:8501
```

### 5. API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 📁 Project Structure

```
ai-junior-test/
├── agents/                 # Multi-agent system
│   ├── __init__.py
│   ├── orchestrator.py     # Main orchestrator
│   ├── intent_classifier.py
│   ├── rag_agent.py        # RAG Knowledge Agent
│   └── ops_agent.py        # Operations Agent
├── api/                    # FastAPI server
│   ├── __init__.py
│   └── server.py
├── RAG/                    # RAG pipeline
│   ├── __init__.py
│   ├── ingest.py           # Document ingestion
│   └── retriever.py        # FAISS retrieval
├── tools/                  # MCP-style tools
│   ├── __init__.py
│   ├── schemas.py          # Pydantic models
│   ├── databaseShared.py   # Simulated databases
│   ├── availability.py     # Tool 1: Check availability
│   ├── bookTable.py        # Tool 2: Book table
│   ├── specialDay.py       # Tool 3: Today's special
│   └── loyaltyCheck.py     # Tool 4: Loyalty points
├── memory/                 # Session memory
│   ├── __init__.py
│   └── session_memory.py
├── config/                 # Configuration
│   ├── __init__.py
│   └── settings.py
├── data/
│   └── Knowledge/          # Knowledge documents
│       ├── menu_nacrCity.txt
│       ├── menu_ShoukCity.txt
│       ├── allergen_guide.txt
│       ├── branch_info.txt
│       ├── loyalty_program.txt
│       ├── opening_hours.txt
│       └── refund_policy.txt
├── streamlit_app.py        # Web UI
├── Dockerfile              # Container image
├── docker-compose.yml      # Orchestration
├── requirements.txt        # Python deps
├── .env.example            # Environment template
└── README.md               # This file
```

