"""
Report Card Generator — Parse moderator summary → structured report.

Tạo Report Card từ kết quả debate:
- Overall score (1-10)
- Category scores (5 chiều)
- Strengths / Weaknesses
- Legal checklist (từ Legal Agent)
- Go / Pivot / No-Go recommendation
"""

import re
import logging

logger = logging.getLogger(__name__)


def generate_report_card(
    idea: str,
    industry: str | None,
    agent_responses: list[dict],
    moderator_summary: str,
) -> dict:
    """
    Parse moderator summary + legal response → structured report card.

    Returns:
        dict: {
            overall_score, category_scores, recommendation,
            strengths, weaknesses, legal_checklist
        }
    """
    # ── Parse điểm từ moderator ────────────────────────
    category_scores = _parse_scores(moderator_summary)
    overall_score = category_scores.pop("overall", 0)

    # Fallback: nếu không parse được → tính trung bình
    if not overall_score and category_scores:
        values = [v for v in category_scores.values() if v > 0]
        overall_score = round(sum(values) / len(values), 1) if values else 5.0

    # ── Parse Go/Pivot/No-Go ───────────────────────────
    recommendation = _parse_recommendation(moderator_summary)

    # ── Parse strengths + weaknesses ────────────────────
    strengths = _parse_list_section(moderator_summary, "ĐIỂM MẠNH")
    weaknesses = _parse_list_section(moderator_summary, "ĐIỂM YẾU")

    # Fallback strengths/weaknesses
    if not strengths:
        strengths = _parse_list_section(moderator_summary, "Điểm đồng thuận")
    if not weaknesses:
        weaknesses = _parse_list_section(moderator_summary, "Rủi ro lớn nhất")

    # ── Legal checklist (từ Legal Agent) ────────────────
    legal_checklist = _parse_legal_checklist(agent_responses)

    return {
        "overall_score": overall_score or 5.0,
        "category_scores": {
            "market": category_scores.get("market", 5.0),
            "strategy": category_scores.get("strategy", 5.0),
            "finance": category_scores.get("finance", 5.0),
            "technical": category_scores.get("technical", 5.0),
            "legal": category_scores.get("legal", 5.0),
        },
        "recommendation": recommendation,
        "strengths": strengths or ["Chưa xác định"],
        "weaknesses": weaknesses or ["Chưa xác định"],
        "legal_checklist": legal_checklist,
    }


# ── Parsers ─────────────────────────────────────────────

def _parse_scores(text: str) -> dict:
    """Parse điểm X/10 từ moderator summary — robust multi-pattern."""
    scores = {}

    # Mapping Vietnamese keywords → category
    mapping = {
        "thị trường": "market",
        "chiến lược": "strategy",
        "tài chính": "finance",
        "kỹ thuật": "technical",
        "pháp lý": "legal",
        "tổng": "overall",
    }

    # Multi-pattern: GPT trả về nhiều format khác nhau
    patterns = [
        # Pattern 1: "- Thị trường: 7/10" hoặc "- **TỔNG: 8/10**"
        r"(?:^|\n)\s*[-\*\d.]*\s*(?:\*\*)?([^:*\n]+?)(?:\*\*)?\s*:\s*(\d+(?:\.\d+)?)\s*/\s*10",
        # Pattern 2: "- **Thị trường:** 7/10" (colon INSIDE bold — GPT phổ biến nhất)
        r"(?:^|\n)\s*[-\*\d.]*\s*\*\*(.+?)\*\*:?\s*(\d+(?:\.\d+)?)\s*/\s*10",
        # Pattern 3: "| Thị trường | 7/10 |" (table format)
        r"\|\s*([^|]+?)\s*\|\s*(\d+(?:\.\d+)?)\s*/\s*10\s*\|",
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
            label = match.group(1).strip().lower()
            # Xóa emoji + ký tự đặc biệt
            label = re.sub(r"[📊🎯💰⚙️⚖️🏛️]", "", label).strip()
            score = float(match.group(2))

            for vn_key, en_key in mapping.items():
                if vn_key in label:
                    if en_key not in scores:  # Không ghi đè nếu đã có
                        scores[en_key] = min(10.0, max(0.0, score))
                    break

    logger.info(f"[ReportCard] Parsed scores: {scores}")
    return scores


def _parse_recommendation(text: str) -> str:
    """Parse Go / Pivot / No-Go — tìm dòng đánh giá thực tế, không phải template."""
    # Tìm dòng chứa "Go / Pivot / No-Go:" và giá trị sau nó
    # Pattern: "Đánh giá Go / Pivot / No-Go:** Go — nên triển khai"
    verdict_pattern = r"(?:Go\s*/\s*Pivot\s*/\s*No-Go|đánh giá|khuyến nghị)[^:]*:\s*\**\s*(Go|Pivot|No-Go|No Go)"
    match = re.search(verdict_pattern, text, re.IGNORECASE)
    if match:
        verdict = match.group(1).strip().lower()
        if "no" in verdict:
            return "No-Go"
        if "pivot" in verdict:
            return "Pivot"
        return "Go"

    # Fallback: tìm patterns cụ thể
    # "nên triển khai" → Go
    if re.search(r"nên\s+triển\s+khai|khuyến\s+nghị.*go\b|đánh giá.*\bgo\b", text, re.IGNORECASE):
        return "Go"
    # "cần pivot" → Pivot
    if re.search(r"cần\s+pivot|nên\s+pivot|pivot.*thay đổi", text, re.IGNORECASE):
        return "Pivot"
    # "không nên" → No-Go
    if re.search(r"không\s+nên|no-go|dừng lại", text, re.IGNORECASE):
        return "No-Go"

    return "Pivot"  # Default safe


def _parse_list_section(text: str, section_name: str) -> list[str]:
    """Parse bullet list sau section header."""
    # Tìm section header
    pattern = rf"(?:##?\s*)?{re.escape(section_name)}[^\n]*\n((?:\s*[-•*]\s*[^\n]+\n?)+)"
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return []

    items = []
    for line in match.group(1).strip().split("\n"):
        line = line.strip()
        line = re.sub(r"^[-•*\d.]+\s*", "", line).strip()
        if line and len(line) > 3:
            items.append(line)

    return items[:5]  # Max 5 items


def _parse_legal_checklist(agent_responses: list[dict]) -> list[dict]:
    """Parse NĐ/Luật từ Legal Agent response → checklist."""
    legal_content = ""
    for r in agent_responses:
        if r.get("agent_name") == "legal":
            legal_content = r.get("content", "")
            break

    if not legal_content:
        return []

    checklist = []

    # Tìm Nghị định, Luật, Thông tư
    patterns = [
        (r"(?:NĐ|Nghị định)\s*(\d+/\d+/NĐ-CP|\d+/\d+)", "Nghị định"),
        (r"(?:Luật)\s+([^\n,.]+?)(?:\s*\d{4})?(?=[,.\n])", "Luật"),
        (r"(?:TT|Thông tư)\s*(\d+/\d+)", "Thông tư"),
    ]

    seen = set()
    for pattern, doc_type in patterns:
        for match in re.finditer(pattern, legal_content):
            ref = match.group(0).strip()
            if ref not in seen:
                seen.add(ref)
                checklist.append({
                    "item": ref,
                    "type": doc_type,
                    "required": True,
                    "status": "pending",
                })

    # Tìm giấy phép thường gặp
    license_keywords = [
        ("GPKD", "Giấy phép kinh doanh"),
        ("ATTP", "An toàn thực phẩm"),
        ("PCCC", "Phòng cháy chữa cháy"),
        ("ĐKKD", "Đăng ký kinh doanh"),
        ("Giấy phép con", "Giấy phép con"),
    ]
    for kw, label in license_keywords:
        if kw.lower() in legal_content.lower():
            item = f"{label} ({kw})"
            if item not in seen:
                seen.add(item)
                checklist.append({
                    "item": item,
                    "type": "Giấy phép",
                    "required": True,
                    "status": "pending",
                })

    return checklist[:10]  # Max 10 items
