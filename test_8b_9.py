"""Test Bước 8B + 9: Search adapters, router, report card."""
import sys
sys.path.insert(0, ".")

print("=" * 55)
print("TEST 1: Module imports")

from ai_engine.tools.tavily_search import search_tavily
from ai_engine.tools.serp_search import search_serp, search_trends_serp
from ai_engine.tools.google_trends import get_trends, format_trends_context
from ai_engine.tools.search_router import smart_search, smart_trends
from ai_engine.report_card import generate_report_card
print("  All imports: OK")

# Test 2: Config has new keys
print("\n" + "=" * 55)
print("TEST 2: Config keys")
from backend.app.config import settings
assert hasattr(settings, "TAVILY_API_KEY"), "Missing TAVILY_API_KEY"
assert hasattr(settings, "SERP_API_KEY"), "Missing SERP_API_KEY"
print(f"  TAVILY_API_KEY: {'set' if settings.TAVILY_API_KEY else 'empty (OK for dev)'}")
print(f"  SERP_API_KEY: {'set' if settings.SERP_API_KEY else 'empty (OK for dev)'}")
print("  [PASS] Config OK")

# Test 3: Adapters return [] when no key
print("\n" + "=" * 55)
print("TEST 3: Adapters graceful fallback")
r1 = search_tavily("test")
r2 = search_serp("test")
r3 = search_trends_serp(["test"])
assert r1 == [], f"Tavily should return [] without key: {r1}"
assert r2 == [], f"SerpAPI should return [] without key: {r2}"
assert r3 == {}, f"SerpAPI Trends should return {{}} without key: {r3}"
print("  Tavily (no key): [] OK")
print("  SerpAPI (no key): [] OK")
print("  SerpAPI Trends (no key): {} OK")
print("  [PASS] Graceful fallback OK")

# Test 4: Search router waterfall → DuckDuckGo
print("\n" + "=" * 55)
print("TEST 4: Search router waterfall")
results, tool = smart_search("tra sua Viet Nam 2024", max_results=2)
print(f"  Results: {len(results)}, Tool: {tool}")
assert tool in ("serpapi", "tavily", "duckduckgo", "none")
# Without API keys, should fall through to duckduckgo
if not settings.SERP_API_KEY and not settings.TAVILY_API_KEY:
    assert tool in ("duckduckgo", "none"), f"Expected duckduckgo, got {tool}"
print("  [PASS] Router OK")

# Test 5: Report card parser
print("\n" + "=" * 55)
print("TEST 5: Report card parser")

mock_moderator = """## ĐIỂM ĐÁNH GIÁ
- Thị trường: 8/10
- Chiến lược: 7/10
- Tài chính: 6.5/10
- Kỹ thuật: 8.5/10
- Pháp lý: 7/10
- **TỔNG: 7.5/10**

**Đánh giá Go / Pivot / No-Go:** Go — nên triển khai

## ĐIỂM MẠNH
- Thị trường rất lớn và tăng trưởng mạnh
- Công nghệ khả thi với chi phí hợp lý

## ĐIỂM YẾU
- Chi phí ban đầu cao
- Rủi ro pháp lý cần xử lý
"""

mock_legal = {
    "agent_name": "legal",
    "agent_display": "Pháp Lý",
    "content": "Cần tuân thủ NĐ 15/2018/NĐ-CP về ATTP. Theo Luật Bảo vệ quyền lợi người tiêu dùng 2023, cần GPKD và PCCC.",
}

report = generate_report_card(
    idea="Quán trà sữa",
    industry="F&B",
    agent_responses=[mock_legal],
    moderator_summary=mock_moderator,
)

print(f"  Overall: {report['overall_score']}")
print(f"  Categories: {report['category_scores']}")
print(f"  Recommendation: {report['recommendation']}")
print(f"  Strengths: {len(report['strengths'])} items")
print(f"  Weaknesses: {len(report['weaknesses'])} items")
print(f"  Legal checklist: {len(report['legal_checklist'])} items")

assert report["overall_score"] == 7.5, f"Expected 7.5, got {report['overall_score']}"
assert report["category_scores"]["market"] == 8.0
assert report["category_scores"]["technical"] == 8.5
assert report["recommendation"] == "Go"
assert len(report["strengths"]) >= 2
assert len(report["weaknesses"]) >= 2
assert len(report["legal_checklist"]) > 0
print("  [PASS] Report card parser OK")

# Test 6: Trends format
print("\n" + "=" * 55)
print("TEST 6: Trends format")
mock_trends = {
    "has_data": True,
    "tra sua": {"average": 75, "current": 80, "trend": "📈"},
}
ctx = format_trends_context(mock_trends)
assert "tra sua" in ctx
assert "📈" in ctx
assert format_trends_context({}) == ""
assert format_trends_context({"has_data": False}) == ""
print("  [PASS] Trends format OK")

print("\n" + "=" * 55)
print("ALL TESTS PASSED ✅")
