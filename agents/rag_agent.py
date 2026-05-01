"""
NovaBite — RAG Knowledge Agent

Answers questions from internal knowledge base (menu, allergens,
opening hours, policies) using FAISS retrieval + grounded generation.
Connected with schemas and databaseShared for validation.
"""

import logging
from typing import Optional, List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain.chains.retrieval_qa.base import RetrievalQA

from config.settings import get_settings
from RAG.retriever import get_retriever
from tools.schemas import (
    BranchName,
    MenuItem,
    LoyaltyTier,
    SpecialEventType,
    OrchestratorRequest,
    OrchestratorResponse,
    IntentClassification,
)
from tools.databaseShared import LOYALTYDB, SPECIALDB, PLANS, EVENTS

logger = logging.getLogger(__name__)
settings = get_settings()

RAG_PROMPT_TEMPLATE = """You are the NovaBite restaurant knowledge assistant for NovaBite Restaurants.
Your ONLY job is to answer questions using the provided context below.

AVAILABLE BRANCHES:
- nacrCity (Nacr City, Cairo)
- ShroukCity (Shrouk City, Cairo)

STRICT RULES:
1. ONLY use information from the context provided. Do NOT invent menu items, prices, or policies.
2. If the context does not contain the answer, respond EXACTLY with:
   "I don't have that information in our knowledge base. Please contact us directly at info@novabite.com or call your nearest branch."
3. Be friendly, helpful, and concise.
4. If answering about allergens, always recommend the customer inform their server of any allergies.
5. When mentioning prices, always state they are in EGP.
6. For loyalty questions, mention the three tiers: base (0-299 points), pro (300-749 points), premium (750+ points).
7. For today's special questions, mention that specials vary by branch and day of week.

Context:
{context}

Question: {question}

Answer:"""

RAG_PROMPT = PromptTemplate(
    template=RAG_PROMPT_TEMPLATE,
    input_variables=["context", "question"],
)


class RAGKnowledgeAgent:
    """
    Retrieval-Augmented Generation agent for NovaBite knowledge queries.
    Fully integrated with schemas and databaseShared for validation.

    Flow:
      1. Query → FAISS retriever (score threshold filtering)
      2. If no chunks above threshold → grounded fallback response
      3. Retrieved chunks → LLM with strict grounding prompt
      4. Return answer with source metadata
      5. Validate against databaseShared schemas
    """

    def __init__(self):
        self._chain: Optional[RetrievalQA] = None
        self._branches = [BranchName.NACR_CITY.value, BranchName.SHROUQ_CITY.value]
        self._tiers = [LoyaltyTier.BASE.value, LoyaltyTier.PRO.value, LoyaltyTier.PREMIUM.value]
        self._events = [SpecialEventType.BIRTHDAY.value, SpecialEventType.ANNIVERSARY.value,
                       SpecialEventType.HOLIDAY.value, SpecialEventType.EID_DAY.value]

    def _build_chain(self) -> RetrievalQA:
        llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=0, 
            openai_api_key=settings.openai_api_key,
        )
        retriever = get_retriever()
        from langchain.chains.combine_documents.stuff import StuffDocumentsChain
        from langchain.chains.llm import LLMChain
        
        # Build the RAG chain using LCEL pattern
        llm_chain = LLMChain(llm=llm, prompt=RAG_PROMPT)
        combine_docs_chain = StuffDocumentsChain(
            llm_chain=llm_chain,
            document_variable_name="context"
        )
        chain = RetrievalQA(
            combine_documents_chain=combine_docs_chain,
            retriever=retriever,
            return_source_documents=True,
        )
        return chain

    @property
    def chain(self) -> RetrievalQA:
        if self._chain is None:
            self._chain = self._build_chain()
        return self._chain

    def answer(self, question: str) -> OrchestratorResponse:
        """
        Answer a knowledge question. Returns structured OrchestratorResponse.

        Args:
            question: User's knowledge question about menu, allergens, hours, policies

        Returns:
            OrchestratorResponse with answer, confidence, and metadata
        """
        logger.info(f"RAG Agent querying: {question[:80]}")

        try:
            result = self.chain.invoke({"query": question})
        except Exception as e:
            logger.error(f"RAG chain error: {e}")
            return OrchestratorResponse(
                userId="unknown",
                response="I'm experiencing a technical issue retrieving that information. Please try again or contact our team directly.",
                intent="KNOWLEDGE",
                toolsUsed=[],
                confidence=0.0,
            )

        answer_text = result.get("result", "")
        source_docs = result.get("source_documents", [])

        grounded = "I don't have that information" not in answer_text and bool(source_docs)

        sources = list({
            doc.metadata.get("source", "internal knowledge base")
            for doc in source_docs
        })

        confidence = 0.85 if grounded else 0.3

        logger.info(f"RAG Agent response grounded={grounded}, sources={sources}")
        return OrchestratorResponse(
            userId="unknown",  # Will be set by orchestrator
            response=answer_text.strip(),
            intent="KNOWLEDGE",
            toolsUsed=["rag_knowledge"] if grounded else [],
            confidence=confidence,
            context={
                "sources": sources,
                "grounded": grounded,
                "source_count": len(source_docs),
            }
        )

    def get_branch_specials(self, branch: str) -> Dict[str, Any]:
        """
        Get today's specials for a branch directly from databaseShared.

        Args:
            branch: Branch name (nacrCity or ShroukCity)

        Returns:
            Special dish info from SPECIALDB
        """
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

    def get_loyalty_tier_info(self, tier: str) -> Dict[str, Any]:
        """
        Get loyalty tier information from databaseShared.

        Args:
            tier: Tier name (base, pro, premium)

        Returns:
            Tier benefits from PLANS
        """
        tier_key = tier.lower()
        if tier_key not in PLANS:
            return {
                "error": f"Tier '{tier}' not found",
                "available_tiers": list(PLANS.keys())
            }

        return {
            "tier": tier_key,
            "benefits": PLANS[tier_key],
        }

    def get_event_info(self, event_type: str) -> Dict[str, Any]:
        """
        Get special event information from databaseShared.

        Args:
            event_type: Event type (birthday, anniversary, holiday, EidDay)

        Returns:
            Event description from EVENTS
        """
        event_key = event_type.lower()
        # Handle EidDay special case
        if event_key == "eidday" or event_key == "eid_day":
            event_key = "EidDay"

        if event_key not in EVENTS:
            return {
                "error": f"Event '{event_type}' not found",
                "available_events": list(EVENTS.keys())
            }

        return {
            "event_type": event_key,
            "description": EVENTS[event_key],
        }

    def validate_branch(self, branch: str) -> bool:
        """Validate branch name against BranchName enum."""
        return branch in [b.value for b in BranchName]

    def validate_tier(self, tier: str) -> bool:
        """Validate loyalty tier against LoyaltyTier enum."""
        return tier.lower() in [t.value for t in LoyaltyTier]


rag_agent = RAGKnowledgeAgent()
