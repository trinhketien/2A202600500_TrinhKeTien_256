"""
Google Trends Adapter — SDK pytrends (community, miễn phí).

CẢNH BÁO: Google hay block IP khi gọi nhiều → dùng làm fallback.
SerpAPI Trends ổn định hơn nếu có SERP_API_KEY.
"""

import logging

logger = logging.getLogger(__name__)

# Timeout cho pytrends (giây)
CONNECT_TIMEOUT = 5
READ_TIMEOUT = 10


def get_trends(
    keywords: list[str],
    geo: str = "VN",
    timeframe: str = "today 12-m",
) -> dict:
    """
    Google Trends qua pytrends (miễn phí).

    Args:
        keywords: Danh sách từ khóa (tối đa 5)
        geo: Quốc gia (default: VN = Việt Nam)
        timeframe: Khoảng thời gian (default: 12 tháng)

    Returns:
        dict: {keyword: {average, current, trend}, has_data: bool} hoặc {} nếu lỗi.
    """
    try:
        from pytrends.request import TrendReq

        pytrends = TrendReq(
            hl="vi",
            tz=420,  # UTC+7
            timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
        )

        kw_list = keywords[:5]  # Max 5 keywords
        pytrends.build_payload(kw_list, timeframe=timeframe, geo=geo)

        df = pytrends.interest_over_time()

        if df.empty:
            logger.info("[PyTrends] No data returned")
            return {"has_data": False}

        result = {"has_data": True}
        for kw in kw_list:
            if kw in df.columns:
                values = df[kw].tolist()
                avg = int(sum(values) / len(values)) if values else 0
                current = int(values[-1]) if values else 0
                trend = "📈" if current > avg else "📉" if current < avg else "➡️"
                result[kw] = {"average": avg, "current": current, "trend": trend}

        logger.info(f"[PyTrends] Keywords: {kw_list} → has_data=True")
        return result

    except ImportError:
        logger.warning("[PyTrends] pytrends not installed — skip")
        return {}
    except Exception as e:
        logger.warning(f"[PyTrends] Failed (Google may have blocked): {e}")
        return {}


def format_trends_context(trends_data: dict) -> str:
    """
    Format trends data → text để inject vào agent prompt.

    Returns:
        str: "" nếu không có data.
    """
    if not trends_data or not trends_data.get("has_data"):
        return ""

    lines = ["## 📈 Google Trends (12 tháng, Việt Nam):"]
    for key, val in trends_data.items():
        if key == "has_data":
            continue
        if isinstance(val, dict):
            trend = val.get("trend", "➡️")
            avg = val.get("average", 0)
            current = val.get("current", 0)
            lines.append(f"- **{key}**: {trend} Trung bình {avg}/100, Hiện tại {current}/100")

    if len(lines) <= 1:
        return ""

    lines.append("\nHãy tham khảo xu hướng trên để đánh giá tiềm năng thị trường.")
    return "\n".join(lines)
