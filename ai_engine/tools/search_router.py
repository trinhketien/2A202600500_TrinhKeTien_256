"""
Search Router — Waterfall tự chọn tool tốt nhất.

Thứ tự ưu tiên:
  Search:  SerpAPI → Tavily → DuckDuckGo (luôn có)
  Trends:  SerpAPI Trends → PyTrends (miễn phí)

Pluggable: thêm tool mới = thêm adapter + sửa waterfall.
"""

import logging

logger = logging.getLogger(__name__)


def smart_search(query: str, max_results: int = 5) -> tuple[list[dict], str]:
    """
    Waterfall search: SerpAPI → Tavily → DuckDuckGo.

    Returns:
        tuple: (results, tool_used)
        tool_used: "serpapi" | "tavily" | "duckduckgo" | "none"
    """
    # 1. SerpAPI (nếu SERP_API_KEY có)
    try:
        from ai_engine.tools.serp_search import search_serp
        results = search_serp(query, max_results)
        if results:
            logger.info(f"[Router] Using SerpAPI — {len(results)} results")
            return results, "serpapi"
    except Exception as e:
        logger.warning(f"[Router] SerpAPI failed: {e}")

    # 2. Tavily (nếu TAVILY_API_KEY có)
    try:
        from ai_engine.tools.tavily_search import search_tavily
        results = search_tavily(query, max_results)
        if results:
            logger.info(f"[Router] Using Tavily — {len(results)} results")
            return results, "tavily"
    except Exception as e:
        logger.warning(f"[Router] Tavily failed: {e}")

    # 3. DuckDuckGo (luôn có — miễn phí)
    try:
        from ai_engine.tools.web_search import search_web
        results = search_web(query, max_results)
        if results:
            logger.info(f"[Router] Using DuckDuckGo — {len(results)} results")
            return results, "duckduckgo"
    except Exception as e:
        logger.warning(f"[Router] DuckDuckGo failed: {e}")

    logger.warning("[Router] All search tools failed")
    return [], "none"


def smart_trends(keywords: list[str]) -> tuple[dict, str]:
    """
    Waterfall trends: SerpAPI Trends → PyTrends.

    Returns:
        tuple: (trends_data, tool_used)
        tool_used: "serpapi" | "pytrends" | "none"
    """
    # 1. SerpAPI Trends (trả phí, ổn định)
    try:
        from ai_engine.tools.serp_search import search_trends_serp
        result = search_trends_serp(keywords)
        if result and result.get("has_data"):
            logger.info(f"[Router] Trends via SerpAPI")
            return result, "serpapi"
    except Exception as e:
        logger.warning(f"[Router] SerpAPI Trends failed: {e}")

    # 2. PyTrends (miễn phí, có thể bị block)
    try:
        from ai_engine.tools.google_trends import get_trends
        result = get_trends(keywords)
        if result and result.get("has_data"):
            logger.info(f"[Router] Trends via PyTrends")
            return result, "pytrends"
    except Exception as e:
        logger.warning(f"[Router] PyTrends failed: {e}")

    logger.info("[Router] No trends data available")
    return {}, "none"
