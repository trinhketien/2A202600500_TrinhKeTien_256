"""
Memory Lifecycle — Quản lý vòng đời bộ nhớ dài hạn.

Quan trọng cho sản phẩm thương mại:
  - deduplicate: xóa memories trùng lặp
  - prune_if_over_limit: vượt quota → xóa mục ít giá trị
  - compress_old_memories: gom nhóm memories cũ
  - track_growth: lưu điểm ý tưởng theo thời gian
  - score_relevance: chấm điểm frequency × recency × relevance
"""

import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


def deduplicate(user_id: str) -> int:
    """
    Xóa memories trùng lặp (nội dung gần giống nhau).
    Dùng so sánh text đơn giản (exact match + substring).
    
    Returns: số memories đã xóa.
    """
    from ai_engine.memory.mem0_client import get_all_memories, delete_memory

    try:
        all_mem = get_all_memories(user_id)
        if len(all_mem) < 2:
            return 0

        # Thu thập text từ memories
        seen_texts = []
        to_delete = []

        for mem in all_mem:
            text = _extract_text(mem).strip().lower()
            if not text:
                continue

            # Kiểm tra trùng lặp (exact match hoặc substring > 80%)
            is_dup = False
            for seen in seen_texts:
                if text == seen:
                    is_dup = True
                    break
                # Substring match: text ngắn hơn là subset của text dài hơn
                shorter, longer = (text, seen) if len(text) < len(seen) else (seen, text)
                if shorter in longer and len(shorter) > 20:
                    is_dup = True
                    break

            if is_dup:
                mem_id = mem.get("id", mem.get("memory_id", ""))
                if mem_id:
                    to_delete.append(mem_id)
            else:
                seen_texts.append(text)

        # Xóa duplicates
        deleted = 0
        for mid in to_delete:
            if delete_memory(mid):
                deleted += 1

        if deleted > 0:
            logger.info(f"[Mem0-lifecycle] Deduplicated {deleted} memories for user {user_id[:8]}...")
        return deleted

    except Exception as e:
        logger.warning(f"[Mem0-lifecycle] deduplicate failed: {e}")
        return 0


def score_relevance(user_id: str) -> list[dict]:
    """
    Chấm điểm memories: frequency × recency.
    Memories gần đây + nhắc lại nhiều lần → điểm cao.
    
    Returns: list[{id, text, score}] sorted by score (thấp → cao).
    """
    from ai_engine.memory.mem0_client import get_all_memories

    try:
        all_mem = get_all_memories(user_id)
        scored = []
        now = datetime.now(timezone.utc)

        for mem in all_mem:
            text = _extract_text(mem)
            mem_id = mem.get("id", mem.get("memory_id", ""))
            
            # Recency score: memories mới hơn → điểm cao hơn
            created = mem.get("created_at", mem.get("created", ""))
            if created:
                try:
                    if isinstance(created, str):
                        dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    else:
                        dt = created
                    days_old = (now - dt).days
                    recency = max(0.1, 1.0 - (days_old / 365))  # 0.1 → 1.0
                except Exception:
                    recency = 0.5
            else:
                recency = 0.5

            # Length score: memories dài hơn = chi tiết hơn = giá trị hơn
            length_score = min(1.0, len(text) / 200) if text else 0.1

            # Combined score
            score = recency * 0.6 + length_score * 0.4

            scored.append({
                "id": mem_id,
                "text": text[:100],
                "score": round(score, 3),
            })

        # Sắp xếp thấp → cao (để pruning xóa từ thấp nhất)
        scored.sort(key=lambda x: x["score"])
        return scored

    except Exception as e:
        logger.warning(f"[Mem0-lifecycle] score_relevance failed: {e}")
        return []


def prune_if_over_limit(user_id: str, max_memories: int = 200) -> int:
    """
    Vượt limit → xóa memories điểm thấp nhất.
    Chạy SAU debate xong (không block SSE streaming).
    
    Returns: số memories đã xóa.
    """
    from ai_engine.memory.mem0_client import count_memories, delete_memory

    try:
        total = count_memories(user_id)
        if total <= max_memories:
            return 0

        # Bước 1: Deduplicate trước
        deduped = deduplicate(user_id)
        total -= deduped

        if total <= max_memories:
            return deduped

        # Bước 2: Xóa theo điểm thấp nhất
        scored = score_relevance(user_id)
        to_remove = total - max_memories
        deleted = deduped

        for item in scored[:to_remove]:
            if item["id"] and delete_memory(item["id"]):
                deleted += 1

        logger.info(
            f"[Mem0-lifecycle] Pruned {deleted} memories for user {user_id[:8]}... "
            f"({total} → {total - deleted + deduped})"
        )
        return deleted

    except Exception as e:
        logger.warning(f"[Mem0-lifecycle] prune failed: {e}")
        return 0


def compress_old_memories(user_id: str, threshold_days: int = 90) -> int:
    """
    Gom nhóm memories cũ (> threshold_days) thành 1 summary.
    Giảm số lượng mà vẫn giữ context.
    
    Returns: số memories đã gom.
    """
    from ai_engine.memory.mem0_client import get_all_memories, add_memory, delete_memory

    try:
        all_mem = get_all_memories(user_id)
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=threshold_days)

        old_memories = []
        for mem in all_mem:
            created = mem.get("created_at", mem.get("created", ""))
            if created:
                try:
                    if isinstance(created, str):
                        dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    else:
                        dt = created
                    if dt < cutoff:
                        old_memories.append(mem)
                except Exception:
                    pass

        if len(old_memories) < 3:
            return 0  # Không đủ để gom

        # Gom thành summary
        texts = [_extract_text(m) for m in old_memories if _extract_text(m)]
        if not texts:
            return 0

        summary = f"[Tóm tắt {len(texts)} phiên cũ] " + " | ".join(texts[:10])
        if len(summary) > 500:
            summary = summary[:497] + "..."

        # Lưu summary mới
        add_memory(user_id, summary, metadata={"type": "compressed", "count": len(texts)})

        # Xóa memories cũ
        deleted = 0
        for mem in old_memories:
            mid = mem.get("id", mem.get("memory_id", ""))
            if mid and delete_memory(mid):
                deleted += 1

        logger.info(f"[Mem0-lifecycle] Compressed {deleted} old memories for user {user_id[:8]}...")
        return deleted

    except Exception as e:
        logger.warning(f"[Mem0-lifecycle] compress failed: {e}")
        return 0


def track_growth(user_id: str, idea: str, score: float | None = None) -> dict | None:
    """
    Lưu điểm ý tưởng theo thời gian — theo dõi sự phát triển của user.
    
    Args:
        user_id: ID user
        idea: Ý tưởng (tóm tắt ngắn)
        score: Điểm từ Moderator (1-10), None nếu chưa có
    """
    from ai_engine.memory.mem0_client import add_memory

    try:
        content = f"Ý tưởng: {idea[:100]}"
        if score is not None:
            content += f" | Điểm: {score}/10"
        content += f" | Ngày: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"

        return add_memory(
            user_id,
            content,
            metadata={"type": "growth", "score": score or 0},
        )
    except Exception as e:
        logger.warning(f"[Mem0-lifecycle] track_growth failed: {e}")
        return None


# ── Helper ──────────────────────────────────────────────

def _extract_text(mem: dict) -> str:
    """Trích xuất text từ memory object (tương thích nhiều format Mem0)."""
    if isinstance(mem, str):
        return mem
    return mem.get("memory", mem.get("content", mem.get("text", ""))) or ""
