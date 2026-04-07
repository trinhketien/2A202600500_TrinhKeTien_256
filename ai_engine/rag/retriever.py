"""
Legal Retriever — Truy vấn ChromaDB lấy văn bản pháp lý liên quan.

Input: ý tưởng kinh doanh + ngành nghề
Output: danh sách văn bản pháp lý liên quan nhất (top K)

Dùng bởi: Legal Agent — inject vào prompt để cite NĐ/Luật cụ thể.
"""

from openai import OpenAI
from backend.app.config import settings
from ai_engine.rag.chroma_client import get_legal_collection

EMBEDDING_MODEL = "text-embedding-3-small"

# Số kết quả tối đa trả về
DEFAULT_TOP_K = 5


def _get_query_embedding(text: str) -> list[float]:
    """Tạo embedding cho câu query."""
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=[text],
    )
    return response.data[0].embedding


def retrieve_legal_context(
    idea: str,
    industry: str | None = None,
    top_k: int = DEFAULT_TOP_K,
) -> list[dict]:
    """
    Truy vấn ChromaDB — lấy văn bản pháp lý liên quan nhất.

    Args:
        idea: Ý tưởng kinh doanh
        industry: Ngành nghề (F&B, tech, giáo dục...)
        top_k: Số kết quả tối đa

    Returns:
        list[dict]: Mỗi dict gồm:
            - source: tên NĐ/Luật (VD: "NĐ 15/2018/NĐ-CP")
            - article_number: điều khoản
            - content: nội dung tóm tắt
            - penalty_amount: mức phạt (nếu có)
            - relevance_score: điểm tương đồng (similarity score, thấp = giống hơn)
    """
    # Xây dựng câu query — kết hợp ý tưởng + ngành
    query = f"Quy định pháp lý cho: {idea}"
    if industry:
        query += f". Ngành: {industry}"

    # Tạo embedding cho query
    query_embedding = _get_query_embedding(query)

    # Query ChromaDB
    collection = get_legal_collection()

    # Kiểm tra collection có dữ liệu không
    if collection.count() == 0:
        return []

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    # Parse kết quả
    legal_docs = []
    for i in range(len(results["ids"][0])):
        meta = results["metadatas"][0][i]
        legal_docs.append({
            "source": meta.get("source", ""),
            "article_number": meta.get("article_number", ""),
            "content": results["documents"][0][i],
            "penalty_amount": meta.get("penalty_amount", ""),
            "industry_tags": meta.get("industry_tags", ""),
            "relevance_score": round(results["distances"][0][i], 4),
        })

    return legal_docs


def format_legal_context(legal_docs: list[dict]) -> str:
    """
    Format kết quả RAG thành text — inject vào prompt của Legal Agent.

    Returns:
        str: Block text dạng markdown, sẵn sàng inject vào prompt.
              Trả "" nếu không có kết quả.
    """
    if not legal_docs:
        return ""

    lines = ["## Văn bản pháp lý VN liên quan (từ cơ sở dữ liệu):"]
    for i, doc in enumerate(legal_docs, 1):
        lines.append(f"\n### [{i}] {doc['source']}")
        if doc["article_number"]:
            lines.append(f"**Điều khoản:** {doc['article_number']}")
        if doc["penalty_amount"]:
            lines.append(f"**Mức phạt:** {doc['penalty_amount']}")
        lines.append(f"**Nội dung:** {doc['content']}")

    lines.append(
        "\n---\n"
        "Hãy cite cụ thể tên NĐ/Luật từ dữ liệu trên trong phân tích. "
        "Nếu có mức phạt → nêu rõ. Nếu văn bản không liên quan → bỏ qua."
    )
    return "\n".join(lines)
