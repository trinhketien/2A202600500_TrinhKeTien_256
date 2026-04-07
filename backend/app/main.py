"""
FastAPI main — Điểm khởi động ứng dụng.
Fix #3: CORS middleware cho phép frontend truy cập.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import settings
from backend.app.api.routes import auth, debate, admin, share, billing

# ── Khởi tạo FastAPI ────────────────────────────────────

app = FastAPI(
    title="Cố Vấn Khởi Nghiệp AI",
    description=(
        "Hệ thống 5 AI agents phản biện ý tưởng kinh doanh. "
        "Mỗi agent phân tích từ 1 góc nhìn: Chiến Lược, Tài Chính, "
        "Thị Trường, Kỹ Thuật, Pháp Lý."
    ),
    version="0.1.0",
)


# ── Fix #3: CORS Middleware ─────────────────────────────
# CORS (Cross-Origin Resource Sharing): cho phép frontend
# chạy trên domain khác (localhost:3000, Vercel) gọi API.
import os
_frontend = os.getenv("FRONTEND_URL", "http://localhost:3000")
ALLOWED_ORIGINS = [
    _frontend,
    "http://localhost:3000",        # Dev
    "http://localhost:5173",        # Vite dev
]
# Nếu dev mode (không có FRONTEND_URL custom) → allow all
if _frontend == "http://localhost:3000":
    ALLOWED_ORIGINS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,        # Cho phép gửi cookie/auth header
    allow_methods=["*"],           # GET, POST, PUT, DELETE, ...
    allow_headers=["*"],           # Authorization, Content-Type, ...
)


# ── Đăng ký routes ──────────────────────────────────────

app.include_router(auth.router, prefix="/api")
app.include_router(debate.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(share.router, prefix="/api")
app.include_router(billing.router, prefix="/api")

# ── Rate Limiter (SlowAPI) ──────────────────────────────
from slowapi.errors import RateLimitExceeded
from backend.app.middleware.rate_limiter import limiter, rate_limit_handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)


# ── Health check ────────────────────────────────────────

@app.get("/", tags=["Health"])
def health_check():
    """Kiểm tra server đang chạy."""
    return {
        "status": "ok",
        "service": "Cố Vấn Khởi Nghiệp AI",
        "version": "0.1.0",
    }


@app.get("/api/health", tags=["Health"])
def api_health():
    """Kiểm tra API endpoint."""
    return {"status": "ok"}
