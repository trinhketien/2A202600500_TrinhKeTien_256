"""
Debate Chain — LangGraph orchestration cho 5 agents + Moderator.

Thứ tự tranh luận: Thị Trường → Chiến Lược → Tài Chính → Kỹ Thuật → Pháp Lý → Moderator
Mỗi agent chạy tuần tự, kết quả được tích lũy.

Chạy test: python -m ai_engine.debate_chain
"""

from __future__ import annotations

import logging
from typing import TypedDict
from langgraph.graph import StateGraph, END

from ai_engine.agents.market import MarketAgent
from ai_engine.agents.strategy import StrategyAgent
from ai_engine.agents.finance import FinanceAgent
from ai_engine.agents.technical import TechnicalAgent
from ai_engine.agents.legal import LegalAgent
from ai_engine.agents.moderator import ModeratorAgent

logger = logging.getLogger(__name__)


# ── State Definition ────────────────────────────────────

class DebateState(TypedDict):
    """State chứa toàn bộ thông tin của 1 phiên tranh luận."""
    idea: str
    industry: str | None
    responses: list[dict]      # Kết quả từ mỗi agent
    summary: dict | None       # Tổng kết từ Moderator
    total_tokens: int
    total_cost: float
    status: str                # running | completed | error
    error: str | None


# ── Agent Nodes ─────────────────────────────────────────

def run_market(state: DebateState) -> dict:
    """Node: Agent Thị Trường (agent đầu tiên — không có ý kiến trước)."""
    logger.info("🔄 Running: 📊 Thị Trường")
    agent = MarketAgent()
    # Agent đầu tiên → phân tích độc lập (không có previous_responses)
    result = agent.analyze(state["idea"], state["industry"])
    responses = state["responses"] + [result]
    return {
        "responses": responses,
        "total_tokens": state["total_tokens"] + result["tokens_used"],
        "total_cost": state["total_cost"] + result["cost_usd"],
    }


def run_strategy(state: DebateState) -> dict:
    """Node: Agent Chiến Lược — đọc ý kiến Thị Trường."""
    logger.info("🔄 Running: 🎯 Chiến Lược")
    agent = StrategyAgent()
    result = agent.analyze(
        state["idea"], state["industry"],
        previous_responses=state["responses"],
    )
    responses = state["responses"] + [result]
    return {
        "responses": responses,
        "total_tokens": state["total_tokens"] + result["tokens_used"],
        "total_cost": state["total_cost"] + result["cost_usd"],
    }


def run_finance(state: DebateState) -> dict:
    """Node: Agent Tài Chính — đọc ý kiến Thị Trường + Chiến Lược."""
    logger.info("🔄 Running: 💰 Tài Chính")
    agent = FinanceAgent()
    result = agent.analyze(
        state["idea"], state["industry"],
        previous_responses=state["responses"],
    )
    responses = state["responses"] + [result]
    return {
        "responses": responses,
        "total_tokens": state["total_tokens"] + result["tokens_used"],
        "total_cost": state["total_cost"] + result["cost_usd"],
    }


def run_technical(state: DebateState) -> dict:
    """Node: Agent Kỹ Thuật — đọc ý kiến Thị Trường + Chiến Lược + Tài Chính."""
    logger.info("🔄 Running: ⚙️ Kỹ Thuật")
    agent = TechnicalAgent()
    result = agent.analyze(
        state["idea"], state["industry"],
        previous_responses=state["responses"],
    )
    responses = state["responses"] + [result]
    return {
        "responses": responses,
        "total_tokens": state["total_tokens"] + result["tokens_used"],
        "total_cost": state["total_cost"] + result["cost_usd"],
    }


def run_legal(state: DebateState) -> dict:
    """Node: Agent Pháp Lý — đọc ý kiến cả 4 agent trước."""
    logger.info("🔄 Running: ⚖️ Pháp Lý")
    agent = LegalAgent()
    result = agent.analyze(
        state["idea"], state["industry"],
        previous_responses=state["responses"],
    )
    responses = state["responses"] + [result]
    return {
        "responses": responses,
        "total_tokens": state["total_tokens"] + result["tokens_used"],
        "total_cost": state["total_cost"] + result["cost_usd"],
    }


def run_moderator(state: DebateState) -> dict:
    """Node: Moderator tổng hợp."""
    logger.info("🔄 Running: 🏛️ Moderator")
    agent = ModeratorAgent()
    result = agent.summarize(
        idea=state["idea"],
        industry=state["industry"],
        agent_responses=state["responses"],
    )
    return {
        "summary": result,
        "total_tokens": state["total_tokens"] + result["tokens_used"],
        "total_cost": state["total_cost"] + result["cost_usd"],
        "status": "completed",
    }


# ── Build Graph ─────────────────────────────────────────

def build_debate_graph() -> StateGraph:
    """
    Xây dựng LangGraph debate chain.

    Flow: market → strategy → finance → technical → legal → moderator → END
    """
    graph = StateGraph(DebateState)

    # Thêm nodes
    graph.add_node("market", run_market)
    graph.add_node("strategy", run_strategy)
    graph.add_node("finance", run_finance)
    graph.add_node("technical", run_technical)
    graph.add_node("legal", run_legal)
    graph.add_node("moderator", run_moderator)

    # Thêm edges (tuần tự)
    graph.set_entry_point("market")
    graph.add_edge("market", "strategy")
    graph.add_edge("strategy", "finance")
    graph.add_edge("finance", "technical")
    graph.add_edge("technical", "legal")
    graph.add_edge("legal", "moderator")
    graph.add_edge("moderator", END)

    return graph.compile()


# ── Public API ──────────────────────────────────────────

# Compiled graph (singleton)
debate_chain = build_debate_graph()


def run_debate(idea: str, industry: str | None = None) -> DebateState:
    """
    Chạy toàn bộ debate chain cho 1 ý tưởng.

    Args:
        idea: Ý tưởng kinh doanh
        industry: Ngành nghề (optional)

    Returns:
        DebateState: Kết quả hoàn chỉnh
    """
    initial_state: DebateState = {
        "idea": idea,
        "industry": industry,
        "responses": [],
        "summary": None,
        "total_tokens": 0,
        "total_cost": 0.0,
        "status": "running",
        "error": None,
    }

    try:
        result = debate_chain.invoke(initial_state)
        return result
    except Exception as e:
        logger.error(f"Debate chain error: {e}")
        initial_state["status"] = "error"
        initial_state["error"] = str(e)
        return initial_state


# ── Test ────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("=== DEBATE CHAIN TEST ===\n")

    result = run_debate(
        idea="Mở quán trà sữa healthy cho gymer tại TP.HCM",
        industry="F&B",
    )

    print(f"\nStatus: {result['status']}")
    print(f"Total tokens: {result['total_tokens']}")
    print(f"Total cost: ${result['total_cost']:.4f}")
    print(f"Responses: {len(result['responses'])} agents")

    for r in result["responses"]:
        print(f"\n{'='*60}")
        print(f"{r['agent_display']} ({r['agent_name']})")
        print(f"Tokens: {r['tokens_used']} | Cost: ${r['cost_usd']}")
        print(f"{'='*60}")
        print(r["content"][:300] + "...")

    if result["summary"]:
        print(f"\n{'='*60}")
        print(f"{result['summary']['agent_display']}")
        print(f"{'='*60}")
        print(result["summary"]["content"])
