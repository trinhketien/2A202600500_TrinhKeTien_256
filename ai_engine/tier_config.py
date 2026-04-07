"""
Tier Config — phân quyền Free / Pro / Premium.

Tất cả limits tập trung ở đây, enforce bởi các endpoints.
"""

TIER_LIMITS = {
    "free": {
        "max_rounds": 1,
        "max_sessions_per_month": 5,
        "max_memories": 10,
        "rag_top_k": 3,
        "search_tool": "duckduckgo",
        "llm_strategy": "mini_all",       # GPT-4o-mini cho tất cả
        "max_tokens_per_agent": 1000,
        "can_export_pdf": False,
        "can_share": False,
    },
    "pro": {
        "max_rounds": 2,
        "max_sessions_per_month": 30,
        "max_memories": 50,
        "rag_top_k": 10,
        "search_tool": "tavily",
        "llm_strategy": "mixed",          # GPT-4o (strategy+legal), mini (others)
        "max_tokens_per_agent": 1500,
        "can_export_pdf": False,
        "can_share": True,
    },
    "premium": {
        "max_rounds": 3,
        "max_sessions_per_month": 100,
        "max_memories": 200,
        "rag_top_k": 10,
        "search_tool": "serpapi",
        "llm_strategy": "full",           # GPT-4o cho tất cả
        "max_tokens_per_agent": 2000,
        "can_export_pdf": True,
        "can_share": True,
    },
}


def get_tier_limits(tier: str) -> dict:
    """Lấy limits cho tier. Default: free nếu tier không hợp lệ."""
    return TIER_LIMITS.get(tier, TIER_LIMITS["free"])


# ── LLM Model Override ──────────────────────────────────

def get_model_for_agent(agent_name: str, llm_strategy: str) -> str:
    """Chọn LLM model theo strategy."""
    if llm_strategy == "full":
        return "gpt-4o"
    elif llm_strategy == "mixed":
        # Strategy + Legal dùng GPT-4o, còn lại mini
        if agent_name in ("strategy", "legal", "moderator"):
            return "gpt-4o"
        return "gpt-4o-mini"
    else:  # "mini_all"
        return "gpt-4o-mini"
