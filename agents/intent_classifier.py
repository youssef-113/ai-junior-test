"""
NovaBite Intent Classifier

Classifies user messages into intents for routing to appropriate agents.
Uses LLM for classification with schema validation.
"""

import logging
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

from config.settings import get_settings
from tools.schemas import IntentClassification, OrchestratorRequest

logger = logging.getLogger(__name__)
settings = get_settings()

# Intent definitions matching the schema
INTENT_KNOWLEDGE = "KNOWLEDGE"
INTENT_OPERATIONS = "OPERATIONS"
INTENT_HYBRID = "HYBRID"
INTENT_CLARIFY = "CLARIFY"
INTENT_FAREWELL = "FAREWELL"

INTENT_PROMPT = """You are the NovaBite Intent Classifier.
Your job is to analyze the customer's message and determine their intent.

CLASSIFICATION OPTIONS:
- KNOWLEDGE: Questions about menu, allergens, opening hours, policies, general info
  Examples: "Do you have vegan pasta?", "What are your hours?", "What's in the Caesar salad?"
  
- OPERATIONS: Requests for booking, availability, loyalty checks, specials
  Examples: "Book a table for 2", "Check my points", "What's today's special?", "Is there availability?"
  
- HYBRID: Mix of knowledge and operations in same message
  Examples: "Do you have gluten-free options and can I book a table?"
  
- CLARIFY: Message is unclear, ambiguous, or needs more information
  Examples: "I need help", "Tell me about your restaurant", "What do you offer?"

- FAREWELL: Goodbye, end of conversation
  Examples: "Thanks, bye", "Goodbye", "That's all"

RULES:
1. Analyze the message carefully
2. Return the single best intent match
3. Provide confidence score (0.0 to 1.0)
4. If CLARIFY, include a clarification question
5. If OPERATIONS or HYBRID, list tools that might be needed

CONVERSATION HISTORY:
{history}

CUSTOMER MESSAGE: {message}

Respond with ONLY the intent name in uppercase."""


class IntentClassifier:
    """Classifies user intent for agent routing."""
    
    def __init__(self):
        # Support both OpenAI and OpenRouter
        if settings.llm_provider == "openrouter":
            self.llm = ChatOpenAI(
                model=settings.llm_model,  # e.g., "openai/gpt-4o-mini"
                temperature=0,
                openai_api_key=settings.openrouter_api_key,
                openai_api_base=settings.openrouter_base_url,
            )
        else:
            self.llm = ChatOpenAI(
                model=settings.llm_model,
                temperature=0,
                openai_api_key=settings.openai_api_key,
            )
        self.prompt = PromptTemplate(
            template=INTENT_PROMPT,
            input_variables=["message", "history"]
        )
    
    def classify(self, message: str, history: Optional[str] = None) -> IntentClassification:
        """
        Classify user intent from message.
        
        Args:
            message: User's message
            history: Optional conversation history as string
            
        Returns:
            IntentClassification with intent, confidence, reasoning
        """
        logger.info(f"Classifying intent for: {message[:80]}")
        
        history_str = history or "No previous conversation"
        
        # Simple keyword-based classification first
        intent, confidence, reasoning = self._keyword_classify(message)
        
        if confidence < 0.8:
            # Use LLM for ambiguous cases
            intent, confidence, reasoning = self._llm_classify(message, history_str)
        
        # Build response
        required_tools = self._get_required_tools(intent, message)
        clarification = None
        
        if intent == INTENT_CLARIFY:
            clarification = self._generate_clarification(message)
        
        return IntentClassification(
            intent=intent,
            confidence=confidence,
            reasoning=reasoning,
            requiredTools=required_tools,
            clarificationQuestion=clarification
        )
    
    def _keyword_classify(self, message: str) -> tuple:
        """Quick keyword-based classification."""
        msg_lower = message.lower()
        
        # Farewell keywords
        farewell_words = ["bye", "goodbye", "thanks", "thank you", "that's all", "done"]
        if any(word in msg_lower for word in farewell_words):
            return INTENT_FAREWELL, 0.95, "Detected farewell keywords"
        
        # Operations keywords
        ops_words = [
            "book", "reservation", "table", "available", "availability",
            "special", "loyalty", "points", "tier", "check my", "cancel booking"
        ]
        ops_count = sum(1 for word in ops_words if word in msg_lower)
        
        # Knowledge keywords
        knowledge_words = [
            "menu", "price", "cost", "allergen", "vegan", "vegetarian",
            "gluten", "dairy", "ingredients", "hours", "open", "close",
            "where", "location", "address", "policy", "refund", "event"
        ]
        knowledge_count = sum(1 for word in knowledge_words if word in msg_lower)
        
        if ops_count > 0 and knowledge_count > 0:
            return INTENT_HYBRID, 0.85, f"Detected {ops_count} ops + {knowledge_count} knowledge keywords"
        elif ops_count > 0:
            return INTENT_OPERATIONS, 0.9, f"Detected {ops_count} operations keywords"
        elif knowledge_count > 0:
            return INTENT_KNOWLEDGE, 0.9, f"Detected {knowledge_count} knowledge keywords"
        else:
            return INTENT_CLARIFY, 0.6, "No clear keywords detected"
    
    def _llm_classify(self, message: str, history: str) -> tuple:
        """Use LLM for classification when keywords are ambiguous."""
        try:
            prompt_text = self.prompt.format(message=message, history=history)
            response = self.llm.invoke(prompt_text)
            
            # Parse response
            result = response.content.strip().upper()
            
            # Map to valid intents
            valid_intents = [INTENT_KNOWLEDGE, INTENT_OPERATIONS, INTENT_HYBRID, INTENT_CLARIFY, INTENT_FAREWELL]
            for intent in valid_intents:
                if intent in result:
                    return intent, 0.85, "Classified by LLM"
            
            return INTENT_CLARIFY, 0.5, "LLM returned unclear classification"
            
        except Exception as e:
            logger.error(f"LLM classification error: {e}")
            return INTENT_CLARIFY, 0.5, "Classification failed"
    
    def _get_required_tools(self, intent: str, message: str) -> list:
        """Determine which tools might be needed."""
        msg_lower = message.lower()
        tools = []
        
        if intent in [INTENT_OPERATIONS, INTENT_HYBRID]:
            if any(word in msg_lower for word in ["book", "reservation"]):
                tools.append("book_table")
            if any(word in msg_lower for word in ["available", "availability", "free table"]):
                tools.append("check_table_availability")
            if any(word in msg_lower for word in ["special", "today's menu"]):
                tools.append("get_today_special")
            if any(word in msg_lower for word in ["loyalty", "points", "tier", "check my"]):
                tools.append("check_loyalty_points")
        
        return tools
    
    def _generate_clarification(self, message: str) -> str:
        """Generate a clarification question for ambiguous messages."""
        return ("I'm not sure what you're looking for. Are you asking about:\n"
                "• Our menu and dishes?\n"
                "• Making a reservation?\n"
                "• Checking your loyalty points?\n"
                "Please let me know so I can help you better!")


# Singleton instance
classifier = IntentClassifier()


def classify_intent(message: str, history: Optional[str] = None) -> str:
    """
    Simple function interface for intent classification.
    Returns just the intent string for easy use.
    """
    result = classifier.classify(message, history)
    return result.intent.lower() if result.confidence > 0.5 else "clarify"
