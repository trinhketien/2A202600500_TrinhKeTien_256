"""
ChromaDB Client — kết nối tới ChromaDB server (Docker).
Singleton pattern: toàn app dùng chung 1 client.
"""

import chromadb
from backend.app.config import settings

# Collection name cho dữ liệu pháp lý VN
LEGAL_COLLECTION = "vn_legal_documents"


def get_chroma_client() -> chromadb.HttpClient:
    """
    Tạo kết nối tới ChromaDB server.
    ChromaDB chạy trong Docker ở port 8100.
    """
    return chromadb.HttpClient(
        host=settings.CHROMA_HOST,
        port=settings.CHROMA_PORT,
    )


def get_legal_collection():
    """
    Lấy (hoặc tạo) collection chứa văn bản pháp lý VN.
    Dùng OpenAI embedding — text-embedding-3-small (rẻ, đủ tốt).
    """
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=LEGAL_COLLECTION,
        metadata={"description": "Van ban phap ly Viet Nam — ND, Luat, TT"},
    )
