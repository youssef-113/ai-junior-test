"""
NovaBite — Operations Agent

Handles operational queries (table availability, bookings, specials,
loyalty) by calling MCP-style tools via LangChain's agent executor.
Connected with schemas and databaseShared for validation.
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from config.settings import get_settings
from tools import ALL_TOOLS
from tools.schemas import (
    BranchName,
    LoyaltyTier,
    SpecialEventType,
    CheckAvailabilityInput,
    BookTableInput,
    GetTodaySpecialInput,
    CheckLoyaltyPointsInput,
    OrchestratorRequest,
    OrchestratorResponse,
    Booking,
)
from tools.databaseShared import LOYALTYDB, SPECIALDB, PLANS, EVENTS, BOOKING

logger = logging.getLogger(__name__)
settings = get_settings()

OPS_SYSTEM_PROMPT = """You are the NovaBite operations assistant — an expert at managing 
reservations, table availability, daily specials, and loyalty points for NovaBite Restaurants.

You have access to the following tools:
- check_table_availability: Check if tables are free for a date/time/branch
- book_table: Confirm a reservation for a customer
- get_today_special: Get today's chef special at a branch
- check_loyalty_points: Look up a customer's points and tier

RULES:
1. Always use a tool to answer operational questions. Never guess.
2. If a customer wants to book a table, FIRST check availability, then book.
3. If required information is missing (e.g., no date, no branch), ask for it.
4. Format responses in a friendly, clear, and concise way.
5. Always confirm booking details back to the customer.
6. If a tool returns an error, explain the issue clearly and offer alternatives.
7. Valid branches are ONLY: nacrCity, ShroukCity (case-sensitive).
8. Loyalty tiers are: base (0-299 points), pro (300-749 points), premium (750+ points).
9. Available events for booking: birthday, anniversary, holiday, EidDay.

Today's date: {today_date}
"""

def get_ops_prompt(today_date: str = None) -> ChatPromptTemplate:
    """Generate ops prompt with current date context."""
    if today_date is None:
        today_date = datetime.now().strftime("%Y-%m-%d")
    
    prompt_text = OPS_SYSTEM_PROMPT.format(today_date=today_date)
    
    return ChatPromptTemplate.from_messages([
        ("system", prompt_text),
        MessagesPlaceholder("chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])


class OperationsAgent:
    """
    Tool-based agent for NovaBite operational tasks.
    Fully integrated with schemas and databaseShared for validation.

    Uses OpenAI function-calling (tools) to select and invoke
    the right MCP-style tool based on the customer's request.
    """

    def __init__(self):
        self._executor: Optional[AgentExecutor] = None
        self._branches = [BranchName.NACR_CITY.value, BranchName.SHROUQ_CITY.value]
        self._tiers = [LoyaltyTier.BASE.value, LoyaltyTier.PRO.value, LoyaltyTier.PREMIUM.value]
        self._events = [SpecialEventType.BIRTHDAY.value, SpecialEventType.ANNIVERSARY.value,
                       SpecialEventType.HOLIDAY.value, SpecialEventType.EID_DAY.value]

    def _build_executor(self, today_date: str = None) -> AgentExecutor:
        llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=0,
            openai_api_key=settings.openai_api_key,
        )
        prompt = get_ops_prompt(today_date)
        agent = create_openai_tools_agent(llm, ALL_TOOLS, prompt)
        executor = AgentExecutor(
            agent=agent,
            tools=ALL_TOOLS,
            verbose=settings.verbose if hasattr(settings, 'verbose') else False,
            handle_parsing_errors=True,
            max_iterations=settings.max_iterations,
            return_intermediate_steps=False,
        )
        return executor

    def get_executor(self, today_date: str = None) -> AgentExecutor:
        """Get or build executor with optional date context."""
        if self._executor is None:
            self._executor = self._build_executor(today_date)
        return self._executor

    def run(self, query: str, chat_history: list | None = None, 
            user_id: str = "unknown", today_date: str = None) -> OrchestratorResponse:
        """
        Execute an operational query using available tools.
        Returns structured OrchestratorResponse matching schema.

        Args:
            query: User's operational query
            chat_history: Optional conversation history
            user_id: User identifier for response
            today_date: Optional date context for the agent

        Returns:
            OrchestratorResponse with answer, confidence, and metadata
        """
        logger.info(f"Operations Agent handling: {query[:80]}")

        try:
            executor = self.get_executor(today_date)
            result = executor.invoke({
                "input": query,
                "chat_history": chat_history or [],
            })
            answer = result.get("output", "")
            
            # Track which tools were used
            tools_used = []
            if "intermediate_steps" in result:
                for step in result["intermediate_steps"]:
                    if hasattr(step, 'tool'):
                        tools_used.append(step.tool)
            
            return OrchestratorResponse(
                userId=user_id,
                response=answer.strip(),
                intent="OPERATIONS",
                toolsUsed=tools_used if tools_used else ["operations_agent"],
                confidence=0.9,
                context={
                    "query": query,
                    "tool_execution_success": True,
                }
            )
        except Exception as e:
            logger.error(f"Operations Agent error: {e}")
            return OrchestratorResponse(
                userId=user_id,
                response="I encountered an issue processing your request. Please try again or contact our team directly.",
                intent="OPERATIONS",
                toolsUsed=[],
                confidence=0.0,
                context={
                    "error": str(e),
                    "query": query,
                }
            )


    def validate_branch(self, branch: str) -> bool:
        """Validate branch name against BranchName enum."""
        return branch in self._branches

    def validate_user_id(self, user_id: str) -> bool:
        """Validate user ID exists in LOYALTYDB."""
        uid = user_id.strip().upper()
        return uid in LOYALTYDB

    def get_user_loyalty_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user loyalty info directly from database."""
        uid = user_id.strip().upper()
        return LOYALTYDB.get(uid)

    def get_branch_specials(self, branch: str) -> Dict[str, Any]:
        """Get branch specials directly from SPECIALDB."""
        branch_key = None
        for key in SPECIALDB.keys():
            if key.lower() == branch.lower().strip():
                branch_key = key
                break
        
        if not branch_key:
            return {
                "error": f"Branch '{branch}' not found",
                "available_branches": list(SPECIALDB.keys())
            }
        
        return {
            "branch": branch_key,
            "specials": SPECIALDB[branch_key],
        }

    def get_available_branches(self) -> List[str]:
        """Return list of valid branch names."""
        return self._branches

    def get_loyalty_tiers(self) -> List[str]:
        """Return list of valid loyalty tiers."""
        return self._tiers

    def get_special_events(self) -> List[str]:
        """Return list of valid special event types."""
        return self._events

    def get_booking_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get booking history for a user from BOOKING database."""
        uid = user_id.strip().upper()
        user_bookings = [
            b for b in BOOKING
            if b.get("userId", "").upper() == uid
        ]
        return user_bookings


ops_agent = OperationsAgent()
