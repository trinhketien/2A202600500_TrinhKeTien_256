"""
Index Legal Documents — Đưa dữ liệu pháp lý VN vào ChromaDB.

Dùng OpenAI text-embedding-3-small (rẻ: $0.02/1M tokens, dimension 1536).
ChromaDB lưu: embedding + document text + metadata.

Chạy: python -m ai_engine.rag.index_legal
Chạy lại an toàn: xóa collection cũ rồi tạo mới (idempotent).
"""

import sys
import os

# Thêm project root vào sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
from backend.app.config import settings
from ai_engine.rag.chroma_client import get_chroma_client, LEGAL_COLLECTION
from ai_engine.data.legal.vn_legal_docs import LEGAL_DOCUMENTS

# ── Embedding ───────────────────────────────────────────

EMBEDDING_MODEL = "text-embedding-3-small"


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Tạo embeddings cho danh sách text bằng OpenAI API.
    text-embedding-3-small: rẻ ($0.02/1M tokens), 1536 dimensions, đủ tốt cho RAG.
    """
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )
    return [item.embedding for item in response.data]


# ── Index ───────────────────────────────────────────────

def index_legal_documents():
    """
    Đưa toàn bộ văn bản pháp lý vào ChromaDB.
    Idempotent (chạy lại an toàn): xóa collection cũ → tạo lại.
    """
    print(f"[index] {len(LEGAL_DOCUMENTS)} documents to index")

    # 1. Kết nối ChromaDB
    client = get_chroma_client()
    print(f"[index] Connected to ChromaDB at {settings.CHROMA_HOST}:{settings.CHROMA_PORT}")

    # 2. Xóa collection cũ (nếu có) → tạo mới
    try:
        client.delete_collection(LEGAL_COLLECTION)
        print(f"[index] Deleted old collection: {LEGAL_COLLECTION}")
    except Exception:
        pass  # Collection chưa tồn tại — OK

    collection = client.create_collection(
        name=LEGAL_COLLECTION,
        metadata={"description": "Van ban phap ly Viet Nam — ND, Luat, TT"},
    )
    print(f"[index] Created collection: {LEGAL_COLLECTION}")

    # 3. Chuẩn bị dữ liệu
    ids = []
    documents = []
    metadatas = []

    for doc in LEGAL_DOCUMENTS:
        ids.append(doc["id"])
        documents.append(doc["text"])
        metadatas.append(doc["metadata"])

    # 4. Tạo embeddings (gọi OpenAI API 1 lần cho toàn bộ)
    print(f"[index] Generating embeddings with {EMBEDDING_MODEL}...")
    embeddings = get_embeddings(documents)
    print(f"[index] Generated {len(embeddings)} embeddings (dim={len(embeddings[0])})")

    # 5. Upsert vào ChromaDB
    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    print(f"[index] Indexed {len(ids)} documents into ChromaDB")

    # 6. Verify
    count = collection.count()
    print(f"[index] Verification: collection has {count} documents")
    assert count == len(ids), f"Expected {len(ids)} but got {count}"

    # 7. Test query nhanh
    print("\n[index] === Quick test query: 'thuc pham an toan' ===")
    test_embed = get_embeddings(["an toàn thực phẩm quán ăn"])[0]
    results = collection.query(
        query_embeddings=[test_embed],
        n_results=3,
    )
    for i, (doc_id, doc_text) in enumerate(zip(results["ids"][0], results["documents"][0])):
        print(f"  [{i+1}] {doc_id}: {doc_text[:80]}...")

    print("\n[index] DONE — Legal documents indexed successfully!")
    return True


if __name__ == "__main__":
    index_legal_documents()
