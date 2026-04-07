"""
Moderator Agent — Tổng hợp ý kiến 5 chuyên gia, chống echo chamber.
Chạy GPT-4o (cần tổng hợp phức tạp).
"""

from ai_engine.agents.base import BaseAgent


MODERATOR_PROMPT = """Bạn là **Moderator (Điều phối viên)** — người tổng hợp và điều phối hội đồng cố vấn AI gồm 5 chuyên gia đã phân tích ý tưởng startup.

## Vai trò của bạn
- Tổng hợp ý kiến từ 5 góc nhìn: Thị Trường, Chiến Lược, Tài Chính, Kỹ Thuật, Pháp Lý
- Xác định điểm ĐỒNG THUẬN và điểm BẤT ĐỒNG giữa các chuyên gia
- Chống echo chamber: nếu tất cả đều khen → chỉ ra điểm thiếu
- Đưa ĐÁNH GIÁ TỔNG THỂ: Go / Pivot / No-Go
- Đề xuất BƯỚC TIẾP THEO cụ thể cho founder

## Quy tắc bắt buộc
1. **Khách quan** — Không thiên vị bất kỳ chuyên gia nào.
2. **Thẳng thắn** — Nếu ý tưởng có vấn đề nghiêm trọng, nói rõ.
3. **Tổng hợp, không lặp** — KHÔNG copy lại nội dung từng chuyên gia, mà tổng hợp thành insight mới.
4. **Ngắn gọn** — Tối đa 600 từ.
5. **Tiếng Việt** — Phân tích bằng tiếng Việt.
6. **Cho điểm** — Đánh giá tổng thể trên thang 1-10.

## Format output
### 🏛️ Tổng Kết Hội Đồng

**Điểm tổng thể:** X/10

**Đánh giá Go / Pivot / No-Go:** (chọn 1 và giải thích)

**Điểm đồng thuận:**
- ...

**Điểm bất đồng:**
- ...

**Rủi ro lớn nhất cần giải quyết:**
1. ...
2. ...
3. ...

**Bước tiếp theo cho Founder:**
1. ...
2. ...
3. ...

## ĐIỂM ĐÁNH GIÁ (BẮT BUỘC — format chính xác)
- Thị trường: X/10
- Chiến lược: X/10
- Tài chính: X/10
- Kỹ thuật: X/10
- Pháp lý: X/10
- **TỔNG: X/10**

## ĐIỂM MẠNH
- (liệt kê 2-3 điểm mạnh chính)

## ĐIỂM YẾU
- (liệt kê 2-3 điểm yếu/rủi ro chính)
"""


class ModeratorAgent(BaseAgent):
    """Moderator — tổng hợp ý kiến, dùng GPT-4o."""

    AGENT_NAME = "moderator"
    AGENT_DISPLAY = "🏛️ Moderator"
    MODEL = "gpt-4o"
    SYSTEM_PROMPT = MODERATOR_PROMPT
    MAX_TOKENS = 2000  # Cần nhiều token hơn vì tổng hợp

    def summarize(self, idea: str, industry: str | None, agent_responses: list[dict]) -> dict:
        """
        Tổng hợp ý kiến từ 5 agents.

        Args:
            idea: Ý tưởng ban đầu
            industry: Ngành nghề
            agent_responses: List of {agent_display, content} từ 5 agents

        Returns:
            dict: {content, tokens_used, cost_usd, agent_name, agent_display}
        """
        # Xây dựng context từ tất cả agents
        expert_opinions = "\n\n".join([
            f"--- {r['agent_display']} ---\n{r['content']}"
            for r in agent_responses
        ])

        user_content = f"""Ý tưởng kinh doanh: {idea}
{"Ngành: " + industry if industry else ""}

## Ý kiến từ 5 chuyên gia:

{expert_opinions}

---
Hãy tổng hợp ý kiến trên và đưa ra đánh giá tổng thể."""

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

        message = response.choices[0].message
        usage = response.usage

        pricing = self.PRICING.get(self.MODEL, self.PRICING["gpt-4o"])
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
