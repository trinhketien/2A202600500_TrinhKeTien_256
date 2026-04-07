"""
Debate Stream — Generator chạy từng agent tuần tự, yield kết quả sau mỗi agent.

Dùng cho SSE endpoint: mỗi agent chạy xong → yield dict → frontend hiển thị realtime.
KHÔNG thay thế debate_chain.py (giữ nguyên POST /api/debate hoạt động).

Thứ tự: Thị Trường → Chiến Lược → Tài Chính → Kỹ Thuật → Pháp Lý → Moderator
"""

from __future__ import annotations

import logging
from typing import Generator

from ai_engine.agents.market import MarketAgent
from ai_engine.agents.strategy import StrategyAgent
from ai_engine.agents.finance import FinanceAgent
from ai_engine.agents.technical import TechnicalAgent
from ai_engine.agents.legal import LegalAgent
from ai_engine.agents.moderator import ModeratorAgent

logger = logging.getLogger(__name__)

# Thứ tự agents (trừ Moderator — xử lý riêng)
AGENT_SEQUENCE = [
    ("market", MarketAgent),
    ("strategy", StrategyAgent),
    ("finance", FinanceAgent),
    ("technical", TechnicalAgent),
    ("legal", LegalAgent),
]


def run_debate_streaming(
    idea: str,
    industry: str | None = None,
    user_id: str | None = None,
    user_tier: str = "free",
) -> Generator[dict, None, None]:
    """
    Generator chạy debate tuần tự — yield kết quả sau mỗi agent.

    Args:
        idea: Ý tưởng kinh doanh
        industry: Ngành nghề
        user_id: ID user — dùng để query/save Mem0. None = skip memory.

    Yields:
        dict: agent/error/summary/memory events
    """
    responses = []    # Tích lũy ý kiến các agent
    total_tokens = 0
    total_cost = 0.0
    memory_context = ""
    memories_found = 0
    total_memories = 0

    # ── Mem0: tìm memories liên quan ─────────────────────
    if user_id:
        try:
            from ai_engine.memory.mem0_client import search_memories, count_memories, format_memory_context
            memories = search_memories(user_id, idea, limit=10)
            memories_found = len(memories)
            total_memories = count_memories(user_id)
            memory_context = format_memory_context(memories)
            logger.info(f"[stream] Mem0: found {memories_found} memories for user {user_id[:8]}...")
        except Exception as e:
            logger.warning(f"[stream] Mem0 search failed (skip): {e}")

    # ── Yield memory event cho frontend ──────────────────
    if user_id:
        yield {
            "type": "memory",
            "memories_found": memories_found,
            "total_memories": total_memories,
            "done": False,
        }

    # ── Chạy 5 agents tuần tự ────────────────────────────
    for agent_name, AgentClass in AGENT_SEQUENCE:
        try:
            logger.info(f"[stream] Running: {agent_name}")
            agent = AgentClass()

            # Tier override: model + max_tokens
            from ai_engine.tier_config import get_tier_limits, get_model_for_agent
            limits = get_tier_limits(user_tier)
            agent.MODEL = get_model_for_agent(agent_name, limits["llm_strategy"])
            agent.MAX_TOKENS = limits["max_tokens_per_agent"]

            # Inject memory context vào idea cho agent đầu tiên
            enriched_idea = idea
            if memory_context and agent_name == "market":
                enriched_idea = f"{idea}\n\n{memory_context}"

            # Agent đầu tiên (Market) → không có previous_responses
            if agent_name == "market":
                result = agent.analyze(enriched_idea, industry)
            else:
                result = agent.analyze(idea, industry, previous_responses=responses)

            responses.append(result)
            total_tokens += result["tokens_used"]
            total_cost += result["cost_usd"]

            # Yield event cho frontend
            yield {
                "type": "agent",
                "agent_name": result["agent_name"],
                "agent_display": result["agent_display"],
                "content": result["content"],
                "tokens_used": result["tokens_used"],
                "cost_usd": result["cost_usd"],
                "rag_sources": result.get("rag_sources", 0),
                "search_results": result.get("search_results", 0),
                "search_tool": result.get("search_tool", ""),
                "trends_available": result.get("trends_available", False),
                "done": False,
            }

        except Exception as e:
            logger.error(f"[stream] Agent {agent_name} failed: {e}")
            # Graceful degradation: gửi error event + tiếp tục agents còn lại
            yield {
                "type": "error",
                "agent_name": agent_name,
                "error": str(e),
                "done": False,
            }

    # ── Moderator tổng kết ───────────────────────────────
    try:
        logger.info("[stream] Running: moderator")
        moderator = ModeratorAgent()
        summary = moderator.summarize(
            idea=idea,
            industry=industry,
            agent_responses=responses,
        )
        total_tokens += summary["tokens_used"]
        total_cost += summary["cost_usd"]

        yield {
            "type": "summary",
            "agent_name": summary["agent_name"],
            "agent_display": summary["agent_display"],
            "content": summary["content"],
            "tokens_used": summary["tokens_used"],
            "cost_usd": summary["cost_usd"],
            "total_tokens": total_tokens,
            "total_cost": round(total_cost, 6),
            "done": True,
        }

    except Exception as e:
        logger.error(f"[stream] Moderator failed: {e}")
        yield {
            "type": "error",
            "agent_name": "moderator",
            "error": str(e),
            "done": True,
        }

    # ── Mem0: lưu memory SAU debate xong ─────────────────
    if user_id:
        try:
            from ai_engine.memory.mem0_client import add_memory
            from ai_engine.memory.lifecycle import prune_if_over_limit
            from backend.app.config import settings

            summary_text = ""
            # summary variable đã có từ moderator.summarize() ở trên
            try:
                summary_text = summary.get("content", "")[:300]
            except Exception:
                pass

            mem_content = (
                f"Ý tưởng: {idea[:100]}. "
                f"Ngành: {industry or 'N/A'}. "
                f"Tóm tắt: {summary_text}"
            )
            add_memory(user_id, mem_content, metadata={"industry": industry or "", "type": "debate"})
            prune_if_over_limit(user_id, max_memories=settings.MEM0_MAX_MEMORIES)
            logger.info(f"[stream] Mem0: saved memory for user {user_id[:8]}...")
        except Exception as e:
            logger.warning(f"[stream] Mem0 save failed (non-blocking): {e}")


# ── Multi-round: User reply → agents respond again ─────

def run_reply_streaming(
    idea: str,
    industry: str | None,
    previous_messages: list[dict],
    user_reply: str,
    round_number: int,
    user_id: str | None = None,
    user_tier: str = "free",
) -> Generator[dict, None, None]:
    """
    Generator cho vòng phản biện (round 2, 3).
    Nhận toàn bộ lịch sử + phản biện user → chạy lại 5 agents + moderator.

    Args:
        idea: Ý tưởng gốc
        industry: Ngành
        previous_messages: Toàn bộ messages từ vòng trước [{agent_name, agent_display, content}, ...]
        user_reply: Nội dung phản biện của user
        round_number: Vòng hiện tại (2 hoặc 3)

    Yields:
        dict: Giống run_debate_streaming — agent/error/summary events
    """
    # Gộp lịch sử + user reply thành danh sách context
    full_context = list(previous_messages)
    full_context.append({
        "agent_name": "user",
        "agent_display": "💬 Phản biện",
        "content": user_reply,
    })

    responses = []
    total_tokens = 0
    total_cost = 0.0

    # ── Chạy 5 agents (tất cả đều nhận full context) ─────
    for agent_name, AgentClass in AGENT_SEQUENCE:
        try:
            logger.info(f"[reply-r{round_number}] Running: {agent_name}")
            agent = AgentClass()

            # Tier override
            from ai_engine.tier_config import get_tier_limits, get_model_for_agent
            limits = get_tier_limits(user_tier)
            agent.MODEL = get_model_for_agent(agent_name, limits["llm_strategy"])
            agent.MAX_TOKENS = limits["max_tokens_per_agent"]

            # Mỗi agent nhận full_context + responses vòng hiện tại
            agent_context = full_context + responses
            result = agent.analyze(idea, industry, previous_responses=agent_context)

            responses.append(result)
            total_tokens += result["tokens_used"]
            total_cost += result["cost_usd"]

            yield {
                "type": "agent",
                "agent_name": result["agent_name"],
                "agent_display": result["agent_display"],
                "content": result["content"],
                "tokens_used": result["tokens_used"],
                "cost_usd": result["cost_usd"],
                "rag_sources": result.get("rag_sources", 0),
                "search_results": result.get("search_results", 0),
                "search_tool": result.get("search_tool", ""),
                "trends_available": result.get("trends_available", False),
                "round_number": round_number,
                "done": False,
            }

        except Exception as e:
            logger.error(f"[reply-r{round_number}] Agent {agent_name} failed: {e}")
            yield {
                "type": "error",
                "agent_name": agent_name,
                "error": str(e),
                "done": False,
            }

    # ── Moderator tổng kết vòng mới ─────────────────────
    try:
        logger.info(f"[reply-r{round_number}] Running: moderator")
        moderator = ModeratorAgent()
        # Moderator nhận all agent responses (vòng hiện tại)
        summary = moderator.summarize(
            idea=idea,
            industry=industry,
            agent_responses=responses,
        )
        total_tokens += summary["tokens_used"]
        total_cost += summary["cost_usd"]

        yield {
            "type": "summary",
            "agent_name": summary["agent_name"],
            "agent_display": summary["agent_display"],
            "content": summary["content"],
            "tokens_used": summary["tokens_used"],
            "cost_usd": summary["cost_usd"],
            "total_tokens": total_tokens,
            "total_cost": round(total_cost, 6),
            "round_number": round_number,
            "done": True,
        }

    except Exception as e:
        logger.error(f"[reply-r{round_number}] Moderator failed: {e}")
        yield {
            "type": "error",
            "agent_name": "moderator",
            "error": str(e),
            "done": True,
        }
