"""
Web Search Tool — DuckDuckGo (miễn phí, không cần API key).

Dùng cho Market Agent để lấy dữ liệu thị trường thực tế.
Timeout 5 giây max — nếu fail thì fallback GPT-only.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Timeout tối đa cho DuckDuckGo (giây)
SEARCH_TIMEOUT = 5


def search_web(query: str, max_results: int = 5) -> list[dict]:
    """
    DuckDuckGo search — miễn phí, không cần API key.

    Args:
        query: Từ khóa tìm kiếm
        max_results: Số kết quả tối đa (default 5)

    Returns:
        list[dict]: Mỗi dict có {title, url, snippet}
        Trả [] nếu lỗi (graceful degradation).
    """
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS  # fallback

        results = []
        with DDGS(timeout=SEARCH_TIMEOUT) as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", r.get("link", "")),
                    "snippet": r.get("body", r.get("snippet", "")),
                })

        logger.info(f"[WebSearch] Query: '{query[:50]}...' → {len(results)} results")
        return results

    except ImportError:
        logger.warning("[WebSearch] duckduckgo-search not installed — skip")
        return []
    except Exception as e:
        logger.warning(f"[WebSearch] Search failed (fallback GPT-only): {e}")
        return []


def format_search_context(results: list[dict]) -> str:
    """
    Format kết quả search → text inject vào prompt agent.

    Returns:
        str: "" nếu results rỗng.
    """
    if not results:
        return ""

    lines = ["## 🔍 Dữ liệu thị trường thực tế (web search):"]
    for i, r in enumerate(results, 1):
        title = r.get("title", "N/A")
        snippet = r.get("snippet", "")
        url = r.get("url", "")
        lines.append(f"{i}. **{title}**")
        if snippet:
            lines.append(f"   {snippet[:200]}")
        if url:
            lines.append(f"   Nguồn: {url}")
        lines.append("")

    lines.append(
        "Hãy tham khảo dữ liệu trên để phân tích chính xác hơn. "
        "Nếu dữ liệu không liên quan, bỏ qua."
    )
    return "\n".join(lines)
