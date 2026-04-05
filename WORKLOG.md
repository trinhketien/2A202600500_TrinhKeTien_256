# Worklog

Ghi lại các quyết định kỹ thuật, phân công, và brainstorming của nhóm.

> Cập nhật **bất cứ khi nào** nhóm ra quyết định kỹ thuật quan trọng hoặc thay đổi hướng đi.

---

## Template

### Quyết định kỹ thuật


### [ADR-1] Thành lập nhóm mới 021 — 04/04/2026

**Bối cảnh:** Nhóm ban đầu của Tiến (A20-App-167) bị biến động — 2 thành viên xin rời sang nhóm khác sau buổi lab Day 01.

**Tình trạng:**
- Thành viên mới: Trịnh Kế Tiến, Hồ Xuân Phú, Phạm Hữu Hoàng Hiệp
- Chuyển sang repo nhóm 021 (A20-App-021)

**Quyết định:** Thành lập nhóm 021 với 3 thành viên mới, bắt đầu từ 04/04/2026.

**Hệ quả:** Cần chốt lại đề tài từ đầu vì mỗi người đã có đề xuất riêng. Mất 1-2 ngày để thống nhất phương án.

---

### [ADR-2] Chốt đề tài: Cố Vấn Khởi Nghiệp AI — 05/04/2026

**Bối cảnh:** Nhóm cần chọn 1 đề tài dự án cuối khóa từ 6 phương án do 3 thành viên đề xuất.

**Các lựa chọn đã xem xét:**
- **HX.Phú:** Đề xuất 078, 090
- **PHH.Hiệp:** Đề xuất 031, 134
- **TK.Tiến:** Đề xuất 066, 080, Cố Vấn Khởi Nghiệp AI

**Quá trình:**
1. Deep Research phân tích 250 dự án trong ngân hàng đề tài
2. Deep Research phân tích 28 dự án Multi-Agent
3. Phân tích và trao đổi sơ bộ 7 phương án
4. So sánh khả năng triển khai trong 5 tuần với 3 người
5. Đánh giá tính khác biệt so với 252 đề tài hiện có
6. Đề tài thống nhất 066 nhưng không còn chỗ trống.
7. Nhóm thống nhất cao, tìm phương án mới đề xuất.

**Quyết định:** Chọn đề tài mới — **Cố Vấn Khởi Nghiệp AI** (Multi-Agent Debate System).
Hệ thống 5 AI agents phản biện ý tưởng kinh doanh từ 5 góc nhìn (Chiến Lược, Kỹ Thuật, Thị Trường, Tài Chính, Pháp Lý) — người dùng chỉ cần nhập ý tưởng.
Lý do:
- **Vấn đề thật:** 57.400 DN mới/quý — phần lớn thất bại vì thiếu phản biện, bỏ qua rủi ro pháp lý và thiếu đánh giá tài chính
- **General AI chưa đủ:** Đòi hỏi biết viết prompt, biết hỏi đúng câu, tự tổng hợp — founder lần đầu thiếu hoàn toàn kỹ năng này
- **Không trùng:** Không đề nào trong 252 đề có agents tranh luận visible trên UI
- **Khác biệt kỹ thuật:** 5 agents phản biện chéo + Moderator chống echo chamber + Mem0 nhớ xuyên phiên + RAG pháp lý VN cite NĐ cụ thể
- **Scope phù hợp:** 3 người, 5 tuần, có số liệu thị trường và bản thiết kế hệ thống chi tiết

**Hệ quả:**
- Cần học LangGraph, Mem0 (công nghệ mới với team)
- Tech stack: LangGraph + Mem0 + FastAPI + Next.js + PostgreSQL + ChromaDB
- Phân công sơ bộ: Backend (1 người) / AI Agents (1 người) / Frontend (1 người)

---

### Sprint 0 — 03/04 → 05/04/2026

| Task | Người làm | Deadline | Trạng thái |
|---|---|---|---|
| Tìm và chốt thành viên nhóm mới | Cả nhóm | 04/04 | ✅ Xong — nhóm 021 |
| Deep Research phân tích 250 dự án | Cả nhóm | 04/04 | ✅ Xong |
| Deep Research phân tích 28 dự án Multi-Agent | Cả nhóm | 04/04 | ✅ Xong |
| Phân tích + trao đổi 6 phương án đề tài | Cả nhóm | 04/04 | ✅ Xong |
| Chốt đề tài dự án | Cả nhóm | 05/04 | ✅ Xong — Cố Vấn Khởi Nghiệp AI |
| Viết đề xuất dự án chi tiết | Cả nhóm | 05/04 | ✅ Xong |
| Lên kế hoạch triển khai 5 tuần | Cả nhóm | 05/04 | ✅ Xong |

---

### Brainstorm: Chọn đề tài dự án — 04/04–05/04/2026

**Câu hỏi:** Nên chọn đề tài nào cho dự án Multi-Agent?

**Các ý tưởng:**
- **HX.Phú:** Đề xuất 078, 090
- **PHH.Hiệp:** Đề xuất 031, 134
- **TK.Tiến:** Đề xuất 066, 080, Cố Vấn Khởi Nghiệp AI (phương án mới bổ sung)

**Phân tích:**
- Deep Research 250 đề tài → xác định 28 đề Multi-Agent → Lựa chọn 06 phương án, sau trao đổi thống nhất cao lựa chọn 066 nhưng hết slot nên nhóm thống nhất đề xuất phương án mới.

**Lý do chọn Cố Vấn Khởi Nghiệp AI:**
- **Vấn đề thật:** 57.400 DN mới/quý, phần lớn thất bại vì thiếu phản biện trước khi đầu tư — đặc biệt bỏ qua rủi ro pháp lý và thiếu đánh giá tài chính
- **General AI chưa đủ:** Đòi hỏi người dùng biết viết prompt, biết hỏi đúng câu, tự tổng hợp — founder lần đầu khởi nghiệp thiếu hoàn toàn kỹ năng này
- **Không trùng:** Không đề nào trong 252 đề có agents tranh luận visible trên UI
- **Khác biệt kỹ thuật:** 5 agents phản biện chéo + Moderator chống echo chamber + Mem0 nhớ xuyên phiên + RAG pháp lý VN (cite NĐ cụ thể)
- **Scope phù hợp:** 3 người, 5 tuần, có bản thiết kế hệ thống chi tiết

**Kết luận:** Chọn Cố Vấn Khởi Nghiệp AI. Đã viết đề xuất chi tiết + thiết kế hệ thống + kế hoạch 5 tuần.


---

<!-- Thêm entry mới xuống dưới -->

---

## Ví dụ

<details>
<summary>Xem ví dụ mẫu (click để mở)</summary>

### [ADR-1] Dùng TypeScript thay vì Python — 30/03/2026

**Bối cảnh:** Cả nhóm cần chọn 1 ngôn ngữ chính để xây dựng agent.

**Các lựa chọn đã xem xét:**
- **Python**: Ecosystem ML tốt hơn, syntax đơn giản.
- **TypeScript**: Type safety, dễ refactor khi project lớn.

**Quyết định:** Chọn TypeScript vì focus vào agent architecture, không cần ML library nặng.

**Hệ quả:** 2 thành viên Python cần học TypeScript cơ bản.

---

### Sprint 1 — 31/03 → 06/04/2026

| Task | Người làm | Deadline | Trạng thái |
|---|---|---|---|
| Setup TypeScript project + CI | Văn A | 01/04 | ✅ Xong |
| Implement agent loop cơ bản | Thị B | 02/04 | ✅ Xong |

---

### Brainstorm: Tính năng cho demo — 05/04/2026

**Câu hỏi:** Demo tuần tới nên show gì?

**Kết luận:** Chọn ý tưởng fix bug cho demo chính vì đảm bảo chạy được.

</details>
