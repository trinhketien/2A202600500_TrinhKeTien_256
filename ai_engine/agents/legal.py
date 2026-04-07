"""
Agent Pháp Lý — Phân tích rủi ro pháp lý, giấy phép, tuân thủ luật VN.
Chạy GPT-4o (model mạnh — pháp lý cần độ chính xác cao).
Tích hợp RAG: query ChromaDB → cite NĐ/Luật VN cụ thể.
"""

import logging
from ai_engine.agents.base import BaseAgent
from ai_engine.rag.retriever import retrieve_legal_context, format_legal_context

logger = logging.getLogger(__name__)


LEGAL_PROMPT = """Bạn là **Chuyên gia Pháp lý** — một thành viên trong hội đồng cố vấn AI gồm 5 chuyên gia phản biện ý tưởng khởi nghiệp.

## Vai trò của bạn
Phân tích ý tưởng kinh doanh từ góc nhìn PHÁP LÝ tại Việt Nam:
- Loại hình doanh nghiệp phù hợp (hộ kinh doanh / công ty TNHH / cổ phần)?
- Giấy phép kinh doanh cần thiết? Thời gian và chi phí đăng ký?
- Ngành nghề có điều kiện (conditional business) không? Cần chứng chỉ gì?
- Quy định về thuế: VAT, thuế TNDN, thuế TNCN?
- Rủi ro pháp lý lớn nhất (legal risk)?
- Quy định bảo vệ người tiêu dùng, VSATTP (nếu F&B)?
- Quy định về dữ liệu cá nhân (PDPA / Luật An ninh mạng VN)?
- Sở hữu trí tuệ (IP): thương hiệu, bằng sáng chế?

## Quy tắc bắt buộc
1. **Phản biện thật sự** — Nếu ý tưởng vi phạm quy định hoặc nằm trong vùng xám pháp lý, cảnh báo rõ.
2. **Cite cụ thể** — BẮT BUỘC nêu tên luật, nghị định (VD: NĐ 15/2018/NĐ-CP, Luật DN 2020). Ưu tiên cite từ "Văn bản pháp lý VN liên quan" được cung cấp bên dưới.
3. **Nêu mức phạt** — Nếu có thông tin mức phạt vi phạm → nêu cụ thể số tiền.
4. **Ngắn gọn** — Tối đa 500 từ.
5. **Cấu trúc rõ ràng** — Dùng tiêu đề, bullet points.
6. **Tiếng Việt** — Phân tích bằng tiếng Việt, thuật ngữ pháp lý giữ nguyên.
7. **Kết thúc bằng 1 câu hỏi** dành cho các chuyên gia khác để thúc đẩy tranh luận.
8. **Lưu ý** — Phân tích dựa trên cơ sở dữ liệu pháp lý được cung cấp + kiến thức chung. KHÔNG thay thế tư vấn pháp lý chuyên nghiệp.

## Quy tắc tranh luận (nếu có ý kiến chuyên gia trước)
- Bạn là chuyên gia CUỐI CÙNG — đọc KỸ ý kiến cả 4 chuyên gia trước.
- Nếu Chiến Lược/Tài Chính/Kỹ Thuật bỏ sót **rủi ro pháp lý** → cảnh báo mạnh + cite NĐ cụ thể.
- Nếu agent Tài Chính chưa tính **chi phí tuân thủ pháp lý** (giấy phép, thuế, PCCC) → bổ sung + nêu mức phạt.
- Nếu agent Kỹ Thuật đề xuất thu thập dữ liệu người dùng → kiểm tra **Luật An ninh mạng + NĐ 13/2023**.
- Nếu đồng ý → xác nhận + cite luật cụ thể để củng cố.
- KHÔNG lặp lại nội dung agent trước đã nói.

## Format output
### ⚖️ Phân tích Pháp lý
**Đánh giá tổng quan:** (1-2 câu)

**Phản hồi chuyên gia trước:** (cảnh báo rủi ro pháp lý nào bị bỏ sót? chi phí tuân thủ chưa tính?)

**Loại hình doanh nghiệp đề xuất:**
- ...

**Giấy phép & Thủ tục:**
- ... (cite NĐ/Luật cụ thể)

**Rủi ro pháp lý & Mức phạt:**
- ... (nêu cụ thể NĐ + mức phạt VND)

**Thuế & Nghĩa vụ tài chính:**
- ...

**Đề xuất:**
- ...

**❓ Câu hỏi cho hội đồng:** ...
"""


class LegalAgent(BaseAgent):
    """
    Agent Pháp Lý — dùng GPT-4o + RAG (ChromaDB).
    Override analyze() để query RAG trước khi gọi LLM.
    """

    AGENT_NAME = "legal"
    AGENT_DISPLAY = "⚖️ Pháp Lý"
    MODEL = "gpt-4o"
    SYSTEM_PROMPT = LEGAL_PROMPT
    MAX_TOKENS = 1500

    def analyze(
        self,
        idea: str,
        industry: str | None = None,
        previous_responses: list[dict] | None = None,
    ) -> dict:
        """
        Phân tích pháp lý với RAG: query ChromaDB → inject vào prompt → gọi LLM.
        Fallback: nếu ChromaDB lỗi hoặc rỗng → chạy như cũ (GPT-only).
        """
        # ── RAG: Query ChromaDB ──────────────────────────
        legal_context = ""
        rag_source_count = 0

        try:
            legal_docs = retrieve_legal_context(idea, industry, top_k=5)
            if legal_docs:
                legal_context = format_legal_context(legal_docs)
                rag_source_count = len(legal_docs)
                logger.info(f"[Legal RAG] Retrieved {rag_source_count} documents")
            else:
                logger.warning("[Legal RAG] No documents found — using GPT-only")
        except Exception as e:
            # Fallback: ChromaDB lỗi → chạy GPT-only (graceful degradation)
            logger.warning(f"[Legal RAG] ChromaDB error — fallback to GPT-only: {e}")

        # ── Xây dựng prompt ──────────────────────────────
        user_content = f"Ý tưởng kinh doanh: {idea}"
        if industry:
            user_content += f"\nNgành: {industry}"

        # Inject RAG context (trước ý kiến agents trước)
        if legal_context:
            user_content += f"\n\n{legal_context}"

        # Context từ agents trước (tranh luận)
        if previous_responses:
            user_content += "\n\n## Ý kiến các chuyên gia trước bạn:\n"
            for r in previous_responses:
                user_content += f"\n--- {r['agent_display']} ---\n{r['content']}\n"
            user_content += (
                "\n---\n"
                "Hãy phân tích từ góc nhìn PHÁP LÝ. "
                "ĐỌC KỸ ý kiến trên + văn bản pháp lý được cung cấp, sau đó:\n"
                "- Cite NĐ/Luật cụ thể từ cơ sở dữ liệu.\n"
                "- Cảnh báo rủi ro pháp lý mà agent trước bỏ sót.\n"
                "- Nêu mức phạt cụ thể (VND) nếu vi phạm.\n"
                "- KHÔNG lặp lại những gì đã nói."
            )

        # ── Gọi LLM ─────────────────────────────────────
        response = self.client.chat.completions.create(
            model=self.MODEL,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            max_tokens=self.MAX_TOKENS,
            temperature=0.7,
        )

        # ── Trích xuất kết quả ───────────────────────────
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
            "rag_sources": rag_source_count,  # Thêm: số nguồn RAG đã dùng
        }


# ── Hàm convenience ─────────────────────────────────────

def run_legal_agent(idea: str, industry: str | None = None) -> dict:
    """
    Chạy Agent Pháp Lý (có RAG).

    Returns:
        dict: {content, tokens_used, cost_usd, agent_name, agent_display, rag_sources}
    """
    agent = LegalAgent()
    return agent.analyze(idea, industry)


# ── Test nhanh ───────────────────────────────────────────

if __name__ == "__main__":
    result = run_legal_agent(
        idea="Mở quán trà sữa healthy cho gymer tại TP.HCM",
        industry="F&B",
    )
    print(f"\n{'='*60}")
    print(f"Agent: {result['agent_display']}")
    print(f"Tokens: {result['tokens_used']} | Cost: ${result['cost_usd']}")
    print(f"RAG sources: {result.get('rag_sources', 0)}")
    print(f"{'='*60}")
    print(result["content"])
