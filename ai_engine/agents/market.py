"""
Agent Thị Trường — Phân tích quy mô thị trường, khách hàng, kênh phân phối.
Chạy GPT-4o-mini + Web Search (waterfall: SerpAPI → Tavily → DuckDuckGo) + Google Trends.

Override analyze() giống pattern legal.py:
1. Smart search + trends → lấy dữ liệu thực tế
2. Inject vào prompt
3. Gọi LLM
4. Return kết quả + search tool info
"""

import logging
from ai_engine.agents.base import BaseAgent
from ai_engine.tools.search_router import smart_search, smart_trends
from ai_engine.tools.web_search import format_search_context
from ai_engine.tools.google_trends import format_trends_context

logger = logging.getLogger(__name__)


MARKET_PROMPT = """Bạn là **Chuyên gia Thị trường** — một thành viên trong hội đồng cố vấn AI gồm 5 chuyên gia phản biện ý tưởng khởi nghiệp.

## Vai trò của bạn
Phân tích ý tưởng kinh doanh từ góc nhìn THỊ TRƯỜNG:
- Quy mô thị trường (TAM/SAM/SOM) ước tính?
- Khách hàng mục tiêu (target customer) là ai? Persona cụ thể?
- Pain point của khách hàng có đủ lớn để trả tiền?
- Kênh phân phối (distribution channel) nào hiệu quả nhất?
- Đối thủ cạnh tranh (competitors) trực tiếp và gián tiếp?
- Xu hướng thị trường (market trend) có thuận lợi?
- Go-to-market strategy nên là gì?

## Quy tắc bắt buộc
1. **Phản biện thật sự** — Không nịnh. Nếu thị trường quá nhỏ hoặc bão hòa, nói thẳng.
2. **Cụ thể** — Đưa số liệu thị trường VN khi có thể, so sánh với đối thủ thực tế.
3. **Ngắn gọn** — Tối đa 500 từ.
4. **Cấu trúc rõ ràng** — Dùng tiêu đề, bullet points.
5. **Tiếng Việt** — Phân tích bằng tiếng Việt, thuật ngữ chuyên ngành giữ tiếng Anh kèm giải thích.
6. **Kết thúc bằng 1 câu hỏi** dành cho các chuyên gia khác để thúc đẩy tranh luận.

## Format output
### 📊 Phân tích Thị trường
**Đánh giá tổng quan:** (1-2 câu)

**Quy mô thị trường:**
- TAM: ...
- SAM: ...
- SOM: ...

**Khách hàng mục tiêu:**
- Persona: ...
- Pain point: ...

**Cạnh tranh:**
- Đối thủ trực tiếp: ...
- Đối thủ gián tiếp: ...

**Go-to-market:**
- ...

**❓ Câu hỏi cho hội đồng:** ...
"""


class MarketAgent(BaseAgent):
    """Agent Thị Trường — GPT-4o-mini + DuckDuckGo web search."""

    AGENT_NAME = "market"
    AGENT_DISPLAY = "📊 Thị Trường"
    MODEL = "gpt-4o-mini"
    SYSTEM_PROMPT = MARKET_PROMPT
    MAX_TOKENS = 1500

    def analyze(
        self,
        idea: str,
        industry: str | None = None,
        previous_responses: list[dict] | None = None,
    ) -> dict:
        """
        Override analyze() — thêm web search trước khi gọi LLM.

        Flow:
        1. DuckDuckGo search (5s timeout, fallback GPT-only)
        2. Build prompt: idea + search results + previous_responses
        3. Gọi OpenAI API
        4. Return kết quả + search_results count
        """
        # ── 1. Smart search (waterfall: SerpAPI → Tavily → DuckDuckGo) ──
        search_results = []
        search_count = 0
        search_tool = "none"
        try:
            query = f"{idea} {industry or ''} thị trường Việt Nam 2024 2025"
            search_results, search_tool = smart_search(query, max_results=5)
            search_count = len(search_results)
            logger.info(f"[Market] Search: {search_count} results via {search_tool}")
        except Exception as e:
            logger.warning(f"[Market] Search failed — GPT-only: {e}")

        # ── 1b. Google Trends ────────────────────────────
        trends_data = {}
        trends_tool = "none"
        try:
            # Lấy 3 từ khóa chính từ idea
            kw_parts = [w for w in idea.split() if len(w) > 2][:3]
            if kw_parts:
                trends_data, trends_tool = smart_trends(kw_parts)
                logger.info(f"[Market] Trends: has_data={trends_data.get('has_data')} via {trends_tool}")
        except Exception as e:
            logger.warning(f"[Market] Trends failed: {e}")

        # ── 2. Build prompt ────────────────────────────────
        user_content = f"Ý tưởng kinh doanh: {idea}"
        if industry:
            user_content += f"\nNgành: {industry}"

        # Inject search results
        if search_results:
            search_context = format_search_context(search_results)
            user_content += f"\n\n{search_context}"

        # Inject trends data
        if trends_data and trends_data.get("has_data"):
            trends_context = format_trends_context(trends_data)
            if trends_context:
                user_content += f"\n\n{trends_context}"

        # Inject previous_responses (giống base.py — phân biệt agent/user)
        if previous_responses:
            user_content += "\n\n## Lịch sử thảo luận:\n"
            for r in previous_responses:
                if r.get("agent_name") == "user":
                    user_content += f"\n--- 💬 PHẢN BIỆN CỦA NGƯỜI DÙNG ---\n{r['content']}\n"
                else:
                    user_content += f"\n--- {r['agent_display']} ---\n{r['content']}\n"
            user_content += (
                "\n---\n"
                "Hãy phân tích từ góc nhìn chuyên môn của bạn. "
                "ĐỌC KỸ toàn bộ lịch sử trên.\n"
                "- Nếu người dùng phản biện → trả lời CỤ THỂ phản biện đó.\n"
                "- Đồng ý điểm nào? Nêu ngắn gọn.\n"
                "- Phản biện điểm nào? Giải thích vì sao.\n"
                "- Bổ sung góc nhìn mới dựa trên phản biện.\n"
                "- KHÔNG lặp lại những gì đã nói."
            )

        # ── 3. Gọi OpenAI API ──────────────────────────────
        response = self.client.chat.completions.create(
            model=self.MODEL,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            max_tokens=self.MAX_TOKENS,
            temperature=0.7,
        )

        message = response.choices[0].message
        usage = response.usage

        # Tính chi phí
        pricing = self.PRICING.get(self.MODEL, self.PRICING["gpt-4o-mini"])
        cost = (
            (usage.prompt_tokens * pricing["input"] / 1_000_000)
            + (usage.completion_tokens * pricing["output"] / 1_000_000)
        )

        return {
            "content": message.content,
            "tokens_used": usage.total_tokens,
            "cost_usd": round(cost, 6),
            "agent_name": self.AGENT_NAME,
            "agent_display": self.AGENT_DISPLAY,
            "search_results": search_count,
            "search_tool": search_tool,
            "trends_available": bool(trends_data.get("has_data")),
        }


# ── Hàm convenience ─────────────────────────────────────

def run_market_agent(idea: str, industry: str | None = None) -> dict:
    """
    Chạy Agent Thị Trường.

    Returns:
        dict: {content, tokens_used, cost_usd, agent_name, agent_display, search_results}
    """
    agent = MarketAgent()
    return agent.analyze(idea, industry)


# ── Test nhanh ───────────────────────────────────────────

if __name__ == "__main__":
    result = run_market_agent(
        idea="Mở quán trà sữa healthy cho gymer tại TP.HCM",
        industry="F&B",
    )
    print(f"\n{'='*60}")
    print(f"Agent: {result['agent_display']}")
    print(f"Tokens: {result['tokens_used']} | Cost: ${result['cost_usd']}")
    print(f"Web search: {result['search_results']} sources")
    print(f"{'='*60}")
    print(result["content"])
