"""
Mem0 Client — Singleton kết nối Mem0 (bộ nhớ dài hạn).

Hỗ trợ 2 provider:
  - "local": lưu trên máy, dùng SQLite + embeddings local
  - "cloud": gọi Mem0 API (cần MEM0_API_KEY)

Mọi hàm đều try/except → graceful degradation (không block debate nếu memory fail).
"""

import logging
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)

# Cache Mem0 client (singleton — không tạo mới mỗi request)
_mem0_client = None


def get_mem0_client():
    """
    Singleton Mem0 client — tạo 1 lần, dùng lại.
    Provider "local": lưu trong thư mục dự án, dùng OpenAI embeddings.
    Provider "cloud": gọi Mem0 API.
    """
    global _mem0_client
    if _mem0_client is not None:
        return _mem0_client

    try:
        from backend.app.config import settings

        if settings.MEM0_PROVIDER == "cloud" and settings.MEM0_API_KEY:
            from mem0 import MemoryClient
            _mem0_client = MemoryClient(api_key=settings.MEM0_API_KEY)
            logger.info("[Mem0] Connected — cloud provider")
        else:
            from mem0 import Memory
            config = {
                "llm": {
                    "provider": "openai",
                    "config": {
                        "model": "gpt-4o-mini",
                        "api_key": settings.OPENAI_API_KEY,
                        "max_tokens": 500,
                    },
                },
                "embedder": {
                    "provider": "openai",
                    "config": {
                        "model": "text-embedding-3-small",
                        "api_key": settings.OPENAI_API_KEY,
                    },
                },
                "vector_store": {
                    "provider": "chroma",
                    "config": {
                        "collection_name": "mem0_memories",
                        "host": settings.CHROMA_HOST,
                        "port": settings.CHROMA_PORT,
                    },
                },
            }
            _mem0_client = Memory.from_config(config)
            logger.info("[Mem0] Connected — local provider (ChromaDB)")

        return _mem0_client

    except Exception as e:
        logger.error(f"[Mem0] Init failed: {e}")
        return None


# ── CRUD operations ─────────────────────────────────────

def add_memory(
    user_id: str,
    content: str,
    metadata: dict | None = None,
) -> dict | None:
    """
    Lưu 1 memory cho user.
    Returns: memory object hoặc None nếu lỗi.
    """
    client = get_mem0_client()
    if not client:
        return None

    try:
        result = client.add(
            content,
            user_id=user_id,
            metadata=metadata or {},
        )
        logger.info(f"[Mem0] Added memory for user {user_id[:8]}...")
        return result
    except Exception as e:
        logger.warning(f"[Mem0] add_memory failed: {e}")
        return None


def search_memories(
    user_id: str,
    query: str,
    limit: int = 10,
) -> list[dict]:
    """
    Tìm memories liên quan đến query.
    Returns: list[dict] — mỗi dict có {memory, score, ...} hoặc [] nếu lỗi.
    """
    client = get_mem0_client()
    if not client:
        return []

    try:
        results = client.search(
            query,
            user_id=user_id,
            limit=limit,
        )
        # Mem0 trả về list hoặc dict tùy version
        if isinstance(results, dict):
            return results.get("results", results.get("memories", []))
        return results if isinstance(results, list) else []
    except Exception as e:
        logger.warning(f"[Mem0] search_memories failed: {e}")
        return []


def get_all_memories(user_id: str) -> list[dict]:
    """Lấy tất cả memories của user."""
    client = get_mem0_client()
    if not client:
        return []

    try:
        results = client.get_all(user_id=user_id)
        if isinstance(results, dict):
            return results.get("results", results.get("memories", []))
        return results if isinstance(results, list) else []
    except Exception as e:
        logger.warning(f"[Mem0] get_all_memories failed: {e}")
        return []


def delete_memory(memory_id: str) -> bool:
    """Xóa 1 memory theo ID."""
    client = get_mem0_client()
    if not client:
        return False

    try:
        client.delete(memory_id)
        return True
    except Exception as e:
        logger.warning(f"[Mem0] delete_memory failed: {e}")
        return False


def count_memories(user_id: str) -> int:
    """Đếm số memories hiện tại của user."""
    try:
        all_mem = get_all_memories(user_id)
        return len(all_mem)
    except Exception:
        return 0


# ── Format cho injection vào prompt ─────────────────────

def format_memory_context(memories: list[dict]) -> str:
    """
    Format memories → text để inject vào agent prompt.
    Returns: "" nếu memories rỗng (tránh inject rỗng).
    """
    if not memories:
        return ""

    lines = ["## 🧠 Bộ nhớ từ các phiên trước:"]
    for i, mem in enumerate(memories, 1):
        # Mem0 trả memory ở key "memory" hoặc "content"
        text = ""
        if isinstance(mem, dict):
            text = mem.get("memory", mem.get("content", mem.get("text", "")))
        elif isinstance(mem, str):
            text = mem

        if text:
            lines.append(f"- {text}")

    if len(lines) <= 1:
        return ""

    lines.append(
        "\nHãy tham khảo bộ nhớ trên để cho lời khuyên liên quan và nhất quán."
    )
    return "\n".join(lines)
