"""
NovaBite Main Orchestrator Agent

Routes user requests to appropriate sub-agents:
- RAGKnowledgeAgent: KNOWLEDGE intent (menu, allergens, policies)
- OperationsAgent: OPERATIONS intent (bookings, availability, loyalty)

Connected with schemas and database for validation.
"""

import logging
from typing import Optional

from memory import get_session_history
from agents.intent_classifier import classify_intent, INTENT_KNOWLEDGE, INTENT_OPERATIONS, INTENT_HYBRID, INTENT_CLARIFY, INTENT_FAREWELL
from agents.rag_agent import rag_agent
from agents.ops_agent import ops_agent
from tools.schemas import OrchestratorRequest, OrchestratorResponse, IntentClassification
from tools.databaseShared import LOYALTYDB

logger = logging.getLogger(__name__)


def extract_user_id_from_message(message: str) -> str:
    """Try to extract user ID from message (USRXXXX format)."""
    import re
    match = re.search(r'USR\d{4}', message.upper())
    return match.group(0) if match else "unknown"


def chat(user_message: str, session_id: str = "default", user_id: str = None) -> OrchestratorResponse:
    """
    Main chat entry point. Routes to appropriate agent based on intent.
    
    Args:
        user_message: Customer's message
        session_id: Session identifier for memory
        user_id: Optional user ID (extracted from message if not provided)
        
    Returns:
        OrchestratorResponse with answer and metadata
    """
    history = get_session_history(session_id)
    chat_history = history.messages
    
    history_str = "\n".join(
        f"{'Customer' if i % 2 == 0 else 'Assistant'}: {msg.content}"
        for i, msg in enumerate(chat_history[-6:])  # Last 3 exchanges
    )
    
    if user_id is None:
        user_id = extract_user_id_from_message(user_message)
    
    intent_result = classify_intent(user_message, history=history_str)
    logger.info(f"[Intent: {intent_result.intent}, Confidence: {intent_result.confidence}]")
    
    if intent_result.intent == INTENT_FAREWELL:
        response = OrchestratorResponse(
            userId=user_id,
            response="Thanks for visiting NovaBite! We hope to see you soon. Bon appétit! 🍽️",
            intent=INTENT_FAREWELL,
            toolsUsed=[],
            confidence=1.0,
        )
    
    elif intent_result.intent == INTENT_OPERATIONS:
        ops_response = ops_agent.run(
            query=user_message,
            chat_history=chat_history,
            user_id=user_id
        )
        response = ops_response
    
    elif intent_result.intent == INTENT_HYBRID:
        rag_response = rag_agent.answer(user_message)
        ops_response = ops_agent.run(
            query=user_message,
            chat_history=chat_history,
            user_id=user_id
        )
        combined = f"{rag_response.response}\n\nRegarding your operational request:\n{ops_response.response}"
        response = OrchestratorResponse(
            userId=user_id,
            response=combined,
            intent=INTENT_HYBRID,
            toolsUsed=rag_response.toolsUsed + ops_response.toolsUsed,
            confidence=(rag_response.confidence + ops_response.confidence) / 2,
            context={
                "rag_context": rag_response.context,
                "ops_context": ops_response.context,
            }
        )
    
    elif intent_result.intent == INTENT_CLARIFY:
        clarification = intent_result.clarificationQuestion or "Could you please provide more details about what you're looking for?"
        response = OrchestratorResponse(
            userId=user_id,
            response=clarification,
            intent=INTENT_CLARIFY,
            toolsUsed=[],
            confidence=intent_result.confidence,
        )
    
    else:
        rag_response = rag_agent.answer(user_message)
        response = OrchestratorResponse(
            userId=user_id,
            response=rag_response.response,
            intent=INTENT_KNOWLEDGE,
            toolsUsed=rag_response.toolsUsed,
            confidence=rag_response.confidence,
            context=rag_response.context,
        )
    
    history.add_user_message(user_message)
    history.add_ai_message(response.response)
    
    return response


def chat_simple(user_message: str, session_id: str = "default") -> str:
    """
    Simple interface that returns just the response string.
    For backward compatibility.
    """
    result = chat(user_message, session_id)
    return result.response


if __name__ == "__main__":
    test_messages = [
        "Do you have vegan pasta?",
        "Book a table for 2 at nacrCity on 2024-05-15 at 19:00",
        "What are my loyalty points? USR0001",
        "Thanks, bye!"
    ]
    
    for msg in test_messages:
        print(f"\nUser: {msg}")
        result = chat(msg, session_id="test")
        print(f"Intent: {result.intent}")
        print(f"Assistant: {result.response[:100]}...")
        print(f"Confidence: {result.confidence}")
        print(f"Tools: {result.toolsUsed}")
