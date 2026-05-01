"""
NovaBite Agents Module

Provides sub-agents for the multi-agent system:
- RAGKnowledgeAgent: Answers menu, allergen, policy questions
- OperationsAgent: Handles booking, availability, loyalty checks
"""

from .rag_agent import RAGKnowledgeAgent, rag_agent

__all__ = [
    "RAGKnowledgeAgent",
    "rag_agent",
]
