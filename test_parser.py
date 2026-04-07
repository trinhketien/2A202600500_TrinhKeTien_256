"""Test report_card parser robustness."""
import sys
sys.path.insert(0, ".")
from ai_engine.report_card import _parse_scores, _parse_recommendation, _parse_list_section

# Test 1: Format chuẩn
t1 = """- Thị trường: 7/10
- Chiến lược: 6/10
- Tài chính: 5/10
- Kỹ thuật: 8/10
- Pháp lý: 6.5/10
- **TỔNG: 7/10**"""
s1 = _parse_scores(t1)
print(f"T1 (chuan): {len(s1)} scores -> {s1}")

# Test 2: GPT emoji + bold
t2 = """- **Thị trường:** 7/10
- **Chiến lược:** 6/10
- **Tài chính:** 5/10
- **Kỹ thuật:** 8/10
- **Pháp lý:** 6/10
- **TỔNG:** 7/10"""
s2 = _parse_scores(t2)
print(f"T2 (bold):  {len(s2)} scores -> {s2}")

# Test 3: Numbered list
t3 = """1. Thị trường: 7/10
2. Chiến lược: 6/10
3. Tài chính: 5/10
4. Kỹ thuật: 8/10
5. Pháp lý: 6/10"""
s3 = _parse_scores(t3)
print(f"T3 (numbered): {len(s3)} scores -> {s3}")

# Test 4: Diem prefix
t4 = """Diem thi truong: 7/10
Diem chien luoc: 6/10
Diem tong the: 7.5/10"""
s4 = _parse_scores(t4)
print(f"T4 (no diacritics): {len(s4)} scores -> {s4}")

# Test 5: Real GPT output pattern
t5 = """## DIEM DANH GIA (BAT BUOC)
- **Thị trường**: 7/10
- **Chiến lược**: 6/10  
- **Tài chính**: 5.5/10
- **Kỹ thuật**: 8/10
- **Pháp lý**: 6/10
- **TỔNG: 6.5/10**"""
s5 = _parse_scores(t5)
print(f"T5 (real GPT): {len(s5)} scores -> {s5}")

# Test 6: recommendation
r1 = _parse_recommendation("Go / Pivot / No-Go: **Go** — nen trien khai")
r2 = _parse_recommendation("Khuyen nghi: Pivot")
r3 = _parse_recommendation("khong nen trien khai")
print(f"Rec: '{r1}' '{r2}' '{r3}'")

# Summary
total = 0
for name, s in [("T1",s1),("T2",s2),("T3",s3),("T5",s5)]:
    expected = 6 if name != "T3" else 5
    total += len(s)
    status = "PASS" if len(s) >= expected else "FAIL"
    print(f"  {name}: {status} ({len(s)}/{expected})")

print(f"\nTotal scores parsed: {total}/23")
