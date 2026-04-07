"""
Clarifier — Kiểm tra ý tưởng có đủ chi tiết để phân tích không.

Rule-based, KHÔNG gọi LLM → miễn phí, nhanh.
Nếu ý tưởng quá mơ hồ (< 15 từ, thiếu ngành) → trả danh sách câu hỏi bổ sung.
"""

import re

# Keywords nhận diện ngành nghề
INDUSTRY_KEYWORDS = {
    "F&B": ["quán", "nhà hàng", "café", "cafe", "trà sữa", "cơm", "ăn uống", "đồ ăn",
            "food", "drink", "bếp", "bar", "bia", "rượu", "bánh", "kem", "phở", "bún"],
    "Tech": ["app", "phần mềm", "SaaS", "website", "web", "AI", "chatbot", "platform",
            "nền tảng", "công nghệ", "software", "cloud", "api", "mobile"],
    "E-commerce": ["bán hàng online", "ecommerce", "thương mại điện tử", "shop",
                   "cửa hàng online", "marketplace", "sàn"],
    "Giáo dục": ["dạy học", "giáo dục", "edtech", "khóa học", "tutoring", "school",
                 "trường", "đào tạo", "coaching", "mentor"],
    "Tài chính": ["fintech", "tài chính", "thanh toán", "payment", "banking", "cho vay",
                  "đầu tư", "bảo hiểm", "insurance", "crypto"],
    "Y tế": ["healthtech", "y tế", "sức khỏe", "bệnh viện", "phòng khám", "dược",
             "health", "medical", "telemedicine"],
    "Bất động sản": ["bất động sản", "nhà đất", "real estate", "cho thuê phòng",
                     "căn hộ", "chung cư"],
}


def _count_words(text: str) -> int:
    """Đếm số từ (hỗ trợ tiếng Việt)."""
    return len(text.split())


def _detect_industry(text: str) -> str | None:
    """Tự nhận diện ngành từ keywords."""
    text_lower = text.lower()
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text_lower:
                return industry
    return None


def _has_scale_info(text: str) -> bool:
    """Kiểm tra có thông tin quy mô / vốn không."""
    patterns = [
        r"\d+\s*(triệu|tỷ|tr|t\b|k\b|usd|\$|vnd|vnđ|đồng)",
        r"vốn", r"quy mô", r"nhân viên", r"nhân sự",
        r"doanh thu", r"lợi nhuận", r"chi phí",
    ]
    text_lower = text.lower()
    return any(re.search(p, text_lower) for p in patterns)


def _has_location(text: str) -> bool:
    """Kiểm tra có địa điểm không."""
    locations = [
        "tp.hcm", "hcm", "sài gòn", "hà nội", "đà nẵng", "cần thơ",
        "hải phòng", "biên hòa", "vũng tàu", "nha trang", "huế",
        "quận", "huyện", "tỉnh", "thành phố", "online", "toàn quốc",
    ]
    text_lower = text.lower()
    return any(loc in text_lower for loc in locations)


def check_idea_clarity(idea: str) -> dict:
    """
    Kiểm tra ý tưởng có đủ rõ ràng không.

    Returns:
        dict: {
            "needs_clarification": bool,
            "questions": list[str]  — danh sách câu hỏi bổ sung
        }
    """
    questions = []
    word_count = _count_words(idea)

    # Quá ngắn
    if word_count < 15:
        if word_count < 8:
            questions.append("Mô tả chi tiết hơn về ý tưởng: bán gì / làm gì / phục vụ ai?")

    # Thiếu ngành
    detected = _detect_industry(idea)
    if not detected:
        questions.append("Ngành nghề kinh doanh? (VD: F&B, Tech, Giáo dục, E-commerce...)")

    # Thiếu vốn / quy mô
    if not _has_scale_info(idea):
        questions.append("Vốn dự kiến ban đầu? (VD: 50 triệu, 200 triệu, 1 tỷ)")

    # Thiếu địa điểm
    if not _has_location(idea):
        questions.append("Địa điểm kinh doanh? (VD: TP.HCM, Hà Nội, online toàn quốc)")

    # Nếu quá ngắn VÀ thiếu nhiều thông tin → clarify
    # Nếu chỉ thiếu 1-2 → vẫn chạy được (không block)
    needs = word_count < 15 and len(questions) >= 2

    return {
        "needs_clarification": needs,
        "questions": questions,
    }
