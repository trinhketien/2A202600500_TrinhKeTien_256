# Weekly Journal

Ghi lại hành trình xây dựng sản phẩm mỗi tuần — những gì đã làm, học được gì, AI giúp như thế nào.

> **Cập nhật mỗi cuối tuần** (trước khi tạo PR). Không cần dài, chỉ cần thật.

---

## Tuần 1 — 03/04/2026

**Thành viên:** Trịnh Kế Tiến (2A202600500) — 1 người (2 thành viên team cũ 167 đã rời nhóm)

#### Đã làm
- Hoàn thành lab Day 01 — LLM API Foundation: kết nối OpenAI API, implement streaming chatbot, so sánh GPT-4o-mini vs GPT-4o
- Tự kiểm tra bài làm, đóng gói nộp `2A202600500_lab_1.zip`
- Tham gia Workshop buổi tối Day 01
- Hoàn thành lab Day 02 — AI Opportunity Discovery Sprint: Problem Scan, Quick Problem Cards, Pitch-Challenge-Vote, Phase 4 Deep-dive, Phase 5 Evaluate
- Viết AI Support Log, đóng gói nộp `2A202600500-TrinhKeTien-day02.zip`
- Tạo tài liệu tổng hợp bài giảng Day 01 & Day 02 (MD + HTML)
- Đóng gói tổng quan tài liệu học sau mỗi buổi

#### Khó nhất tuần này
- Nhóm khi học xếp ngẫu nhiên và đồng (9 người)→ kéo chậm việc chốt đề tài, mất tập trung vì phải lo tìm nhóm phù hợp
- 2 thành viên xin rời sang nhóm khác 

#### AI tool đã dùng
| Tool | Dùng để làm gì | Kết quả |
|---|---|---|
| Antigravity (Gemini) | Hỗ trợ viết code Python cho lab Day 01, debug test failures | Pass toàn bộ test suite |
| Antigravity (Gemini) | Research AIOps tools, tìm case study, digitize workflow vẽ tay | Tìm được Datadog/PagerDuty/Moogsoft. AI bịa 1 case study — phải tự verify |
| Antigravity (Gemini) | Phản biện Problem Statement, chỉ ra metric yếu | Phát hiện metric mơ hồ → sửa thành số cụ thể |

#### Học được
- Problem-first, not AI-first: bắt đầu từ nỗi đau thật, kết luận "không cần AI" vẫn tốt nếu justify được
- Metric phải có số: "nhanh hơn" = 0 điểm, "90 phút → 30 phút" mới đo được
- AI hay bịa: case study, tên công ty, số liệu — luôn verify bằng nguồn chính thức
- Linh hoạt nghĩ mọi cách, tìm mọi phương án để đạt mục tiêu — quan trọng là mục tiêu đúng

#### Nếu làm lại, sẽ làm khác
- Tự brainstorm hết trước, rồi mới nhờ AI mở rộng — tránh phụ thuộc AI từ đầu

#### Kế hoạch tuần tới
- Tìm và chốt thành viên nhóm mới (3 người)
- Brainstorm + chốt đề tài dự án cuối khóa cùng team
- Deep Research phân tích ngân hàng 250 đề tài
- Viết đề xuất dự án chi tiết: problem statement, kiến trúc, phân công
- Thiết kế hệ thống: DB schema, API contract, LangGraph flow
- Clone repo nhóm, setup môi trường phát triển


**Thành viên:** Phạm Hữu Hoàng Hiệp 

#### Đã làm
- Setup project TypeScript + cấu hình `.env`
- Lên ý tưởng và thiết kế hệ thống

#### Khó nhất tuần này
- Tìm được ý tưởng phù hợp 

#### AI tool đã dùng
Dùng Gemini , Antigravity để deep research để lên ý tưởng và thiết kế hệ thống

#### Học được
- Cách phân tích dự án một cách chuyên nghiệp từ ý tưởng ban đầu


#### Nếu làm lại, sẽ làm khác

#### Kế hoạch tuần tới

Frontend: Landing (hero, tính năng, CTA, responsive, PWA manifest); khung UI debate + form + sidebar với mock JSON; màn đăng nhập/đăng ký + nút OAuth.

Backend: Supabase Auth + JWT + Google OAuth; tạo bảng DB, migration, seed; API stub trả dữ liệu giả đúng OpenAPI.

AI: Cài LangGraph (orchestrator + state machine); 2 agent đầu (Chiến lược + Kỹ Thuật) — prompt + test; spike Mem0 (lưu/recall); chuẩn bị RAG: chunk + index NĐ/Luật vào ChromaDB.

Kết quả cần có: User đăng nhập được · 2 agent chạy test được · UI hiển thị response


