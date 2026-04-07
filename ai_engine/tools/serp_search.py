"""
SerpAPI Search Adapter — SDK chính thức google-search-results (by SerpAPI LLC).

Trả phí: ~$50/tháng. Bao gồm Google Search + Google Trends endpoint.
Chỉ hoạt động khi SERP_API_KEY có giá trị trong .env.
"""

import logging

logger = logging.getLogger(__name__)


def search_serp(query: str, max_results: int = 5) -> list[dict]:
    """
    SerpAPI Google Search — SDK chính thức.

    Returns:
        list[dict]: [{title, url, snippet}] hoặc [] nếu lỗi/không có key.
    """
    try:
        from backend.app.config import settings
        if not settings.SERP_API_KEY:
            return []

        from serpapi import GoogleSearch

        params = {
            "q": query,
            "api_key": settings.SERP_API_KEY,
            "num": max_results,
            "gl": "vn",       # Khu vực: Việt Nam
            "hl": "vi",       # Ngôn ngữ: tiếng Việt
        }

        search = GoogleSearch(params)
        data = search.get_dict()

        results = []
        for r in data.get("organic_results", [])[:max_results]:
            results.append({
                "title": r.get("title", ""),
                "url": r.get("link", ""),
                "snippet": r.get("snippet", ""),
            })

        logger.info(f"[SerpAPI] Query: '{query[:50]}...' → {len(results)} results")
        return results

    except ImportError:
        logger.warning("[SerpAPI] google-search-results not installed — skip")
        return []
    except Exception as e:
        logger.warning(f"[SerpAPI] Search failed: {e}")
        return []


def search_trends_serp(keywords: list[str]) -> dict:
    """
    SerpAPI Google Trends endpoint (trả phí, ổn định hơn pytrends).

    Returns:
        dict: {keyword: {average, current, trend}, has_data: bool} hoặc {} nếu lỗi.
    """
    try:
        from backend.app.config import settings
        if not settings.SERP_API_KEY:
            return {}

        from serpapi import GoogleSearch

        params = {
            "engine": "google_trends",
            "q": ",".join(keywords[:5]),
            "api_key": settings.SERP_API_KEY,
            "data_type": "TIMESERIES",
            "geo": "VN",
        }

        search = GoogleSearch(params)
        data = search.get_dict()

        result = {"has_data": False}
        interest = data.get("interest_over_time", {})
        timeline = interest.get("timeline_data", [])

        if timeline:
            result["has_data"] = True
            for kw in keywords[:5]:
                values = []
                for point in timeline:
                    for val in point.get("values", []):
                        if val.get("query", "").lower() == kw.lower():
                            try:
                                values.append(int(val.get("extracted_value", 0)))
                            except (ValueError, TypeError):
                                pass

                if values:
                    avg = sum(values) // len(values)
                    current = values[-1] if values else 0
                    trend = "📈" if current > avg else "📉" if current < avg else "➡️"
                    result[kw] = {"average": avg, "current": current, "trend": trend}

        logger.info(f"[SerpAPI-Trends] Keywords: {keywords[:3]} → has_data={result.get('has_data')}")
        return result

    except ImportError:
        logger.warning("[SerpAPI-Trends] google-search-results not installed — skip")
        return {}
    except Exception as e:
        logger.warning(f"[SerpAPI-Trends] Failed: {e}")
        return {}
