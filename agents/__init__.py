"""
NovaBite Agents Module

Provides sub-agents for the multi-agent system:
- RAGKnowledgeAgent: Answers menu, allergen, policy questions (KNOWLEDGE intent)
- OperationsAgent: Handles booking, availability, loyalty checks (OPERATIONS intent)
"""

from .rag_agent import RAGKnowledgeAgent, rag_agent
from .ops_agent import OperationsAgent, ops_agent

__all__ = [
    # RAG Knowledge Agent
    "RAGKnowledgeAgent",
    "rag_agent",
    # Operations Agent
    "OperationsAgent",
    "ops_agent",
]
