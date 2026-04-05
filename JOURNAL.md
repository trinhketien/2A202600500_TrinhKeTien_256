# Weekly Journal

Ghi lại hành trình xây dựng sản phẩm mỗi tuần — những gì đã làm, học được gì, AI giúp như thế nào.

> **Cập nhật mỗi cuối tuần** (trước khi tạo PR). Không cần dài, chỉ cần thật.

---

## Template

```markdown
## Tuần N — DD/MM/YYYY

### Đã làm
-

### Khó nhất tuần này
-

### AI tool đã dùng
| Tool | Dùng để làm gì | Kết quả |
|---|---|---|
| Claude Code | | |

### Học được
-

### Nếu làm lại, sẽ làm khác
-

### Kế hoạch tuần tới
-
```

---


### Tuần 1 — 31/03/2026

**Thành viên:** Phạm Hữu Hoàng Hiệp ,...

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

Cuối tuần: FE chuyển từ mock sang gọi API thật.

Kết quả cần có: User đăng nhập được · 2 agent chạy test được · UI hiển thị response

---

### Tuần 2 — 07/04/2026

**Thành viên:** Nguyễn Văn A, Trần Thị B, Lê Văn C

#### Đã làm
- Thêm tool `read_file`, `write_file`, `list_dir`
- Agent có thể tự đọc file trong repo và đề xuất refactor
- Implement conversation memory: lưu 20 message gần nhất
- Thử nghiệm: cho agent tự fix 3 bug đơn giản → thành công 2/3

#### Khó nhất tuần này
- Memory bị lỗi khi conversation quá dài (vượt context window). Phải implement sliding window: chỉ giữ system prompt + 20 message gần nhất.
- Agent đôi khi loop vô hạn khi tool trả lỗi — chưa có stop condition tốt.

#### AI tool đã dùng
| Tool | Dùng để làm gì | Kết quả |
|---|---|---|
| Claude Code | Thiết kế sliding window memory, review code agent loop | Phát hiện thêm edge case khi tool throw exception |
| Gemini CLI | So sánh approach lưu memory: file JSON vs SQLite | Tư vấn dùng JSON cho prototype, SQLite khi cần query |

#### Học được
- Context window là resource có hạn — cần thiết kế memory strategy từ sớm.
- Stop condition quan trọng không kém gì agent logic: `max_iterations`, `no_new_tool_calls`, `explicit_done`.
- AI agent review code của mình rất có ích: Claude Code tìm ra 2 potential null pointer mà mình bỏ sót.

#### Nếu làm lại, sẽ làm khác
- Viết interface `Memory` trước, rồi implement sau — thay vì hard-code array từ đầu.
- Log tất cả tool call ra file ngay từ đầu để debug dễ hơn.

#### Kế hoạch tuần tới
- Fix vòng lặp vô hạn: thêm `max_iterations = 10`
- Thêm tool `run_tests` để agent tự kiểm tra code sau khi sửa
- Demo cho instructor cuối tuần
