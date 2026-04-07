"""
Tavily Search Adapter — SDK chính thức tavily-python (by Tavily Inc.).

Trả phí: ~$5/tháng. Chất lượng cao hơn DuckDuckGo.
Chỉ hoạt động khi TAVILY_API_KEY có giá trị trong .env.
"""

import logging

logger = logging.getLogger(__name__)


def search_tavily(query: str, max_results: int = 5) -> list[dict]:
    """
    Tavily search — SDK chính thức.

    Args:
        query: Từ khóa tìm kiếm
        max_results: Số kết quả tối đa

    Returns:
        list[dict]: [{title, url, snippet}] hoặc [] nếu lỗi/không có key.
    """
    try:
        from backend.app.config import settings
        if not settings.TAVILY_API_KEY:
            return []

        from tavily import TavilyClient
        client = TavilyClient(api_key=settings.TAVILY_API_KEY)

        response = client.search(
            query=query,
            max_results=max_results,
            search_depth="basic",
        )

        results = []
        for r in response.get("results", []):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("content", ""),
            })

        logger.info(f"[Tavily] Query: '{query[:50]}...' → {len(results)} results")
        return results

    except ImportError:
        logger.warning("[Tavily] tavily-python not installed — skip")
        return []
    except Exception as e:
        logger.warning(f"[Tavily] Search failed: {e}")
        return []
