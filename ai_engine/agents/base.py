"""
Base Agent — Lớp cơ sở cho tất cả 5 AI agents.
Mỗi agent kế thừa (inherit) từ đây, chỉ cần override:
  - AGENT_NAME: tên kỹ thuật
  - AGENT_DISPLAY: tên hiển thị trên UI
  - MODEL: GPT-4o hoặc GPT-4o-mini
  - SYSTEM_PROMPT: prompt chuyên biệt
"""

from openai import OpenAI
from backend.app.config import settings


class BaseAgent:
    """Lớp cơ sở — xử lý chung việc gọi OpenAI API."""

    AGENT_NAME: str = "base"
    AGENT_DISPLAY: str = "Base Agent"
    MODEL: str = "gpt-4o-mini"
    SYSTEM_PROMPT: str = "You are a helpful assistant."
    MAX_TOKENS: int = 1500

    # Giá token (USD per 1M tokens) — để tính chi phí
    PRICING = {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    }

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def analyze(
        self,
        idea: str,
        industry: str | None = None,
        previous_responses: list[dict] | None = None,
    ) -> dict:
        """
        Phân tích ý tưởng kinh doanh — có thể nhận context từ agents trước.

        Args:
            idea: Ý tưởng người dùng nhập
            industry: Ngành nghề (nếu có)
            previous_responses: Danh sách kết quả từ agents trước đó.
                Mỗi dict gồm {agent_display, content, agent_name, ...}.
                Nếu None → agent phân tích độc lập (agent đầu tiên).

        Returns:
            dict: {content, tokens_used, cost_usd, agent_name, agent_display}
        """
        # Xây dựng user prompt
        user_content = f"Ý tưởng kinh doanh: {idea}"
        if industry:
            user_content += f"\nNgành: {industry}"

        # TRANH LUẬN: Thêm context từ agents trước + user reply (nếu có)
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

        # Gọi OpenAI API
        response = self.client.chat.completions.create(
            model=self.MODEL,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            max_tokens=self.MAX_TOKENS,
            temperature=0.7,
        )

        # Trích xuất kết quả
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
        }
