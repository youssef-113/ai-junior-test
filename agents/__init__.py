"""
NovaBite Agents Module

Provides agents for the multi-agent system:
- MainOrchestrator: Routes requests to appropriate sub-agents
- RAGKnowledgeAgent: KNOWLEDGE intent (menu, allergens, policies)
- OperationsAgent: OPERATIONS intent (bookings, availability, loyalty)
- IntentClassifier: Classifies user intent for routing
"""

from .rag_agent import RAGKnowledgeAgent, rag_agent
from .ops_agent import OperationsAgent, ops_agent
from .intent_classifier import IntentClassifier, classify_intent, INTENT_KNOWLEDGE, INTENT_OPERATIONS, INTENT_HYBRID, INTENT_CLARIFY, INTENT_FAREWELL
from .orchestrator import chat, chat_simple

__all__ = [
    # Main Orchestrator
    "chat",
    "chat_simple",
    # RAG Knowledge Agent
    "RAGKnowledgeAgent",
    "rag_agent",
    # Operations Agent
    "OperationsAgent",
    "ops_agent",
    # Intent Classifier
    "IntentClassifier",
    "classify_intent",
    "INTENT_KNOWLEDGE",
    "INTENT_OPERATIONS",
    "INTENT_HYBRID",
    "INTENT_CLARIFY",
    "INTENT_FAREWELL",
]
