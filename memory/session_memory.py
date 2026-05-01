"""
Session Memory Management for NovaBite

Stores and retrieves conversation history by session ID.
"""

from typing import Dict, List, Optional
from datetime import datetime
from langchain.memory import ChatMessageHistory
from langchain.schema import BaseMessage, HumanMessage, AIMessage

# In-memory session store
_session_store: Dict[str, ChatMessageHistory] = {}


class SessionMemory:
    """Manages conversation history for a session."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.now().isoformat()
        self._history = ChatMessageHistory()
    
    @property
    def messages(self) -> List[BaseMessage]:
        """Get all messages in the session."""
        return self._history.messages
    
    def add_user_message(self, message: str) -> None:
        """Add a user message to the history."""
        self._history.add_user_message(message)
    
    def add_ai_message(self, message: str) -> None:
        """Add an AI message to the history."""
        self._history.add_ai_message(message)
    
    def clear(self) -> None:
        """Clear the session history."""
        self._history.clear()
    
    def to_string(self) -> str:
        """Convert history to string format."""
        return "\n".join(
            f"{'Customer' if isinstance(msg, HumanMessage) else 'Assistant'}: {msg.content}"
            for msg in self._history.messages
        )
    
    def get_last_n_messages(self, n: int = 5) -> List[BaseMessage]:
        """Get last N messages."""
        return self._history.messages[-n:]


def get_session_history(session_id: str) -> ChatMessageHistory:
    """
    Get or create a session history by session ID.
    
    Args:
        session_id: Unique session identifier
        
    Returns:
        ChatMessageHistory for the session
    """
    if session_id not in _session_store:
        _session_store[session_id] = ChatMessageHistory()
    return _session_store[session_id]


def clear_session(session_id: str) -> None:
    """Clear a specific session."""
    if session_id in _session_store:
        del _session_store[session_id]


def get_all_sessions() -> List[str]:
    """Get all active session IDs."""
    return list(_session_store.keys())
