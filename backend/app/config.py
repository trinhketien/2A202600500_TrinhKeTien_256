"""
Cấu hình ứng dụng — đọc từ file .env
Mọi giá trị cấu hình tập trung ở đây, không scatter (phân tán) ra các file khác.
"""

from pydantic_settings import BaseSettings
from pathlib import Path

# Tìm file .env ở thư mục gốc dự án (A20-App-021/.env)
ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    """Tất cả cấu hình đọc từ .env — tự động map theo tên biến."""

    # ── LLM ──────────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    DEFAULT_MODEL: str = "gpt-4o"

    # ── Database ─────────────────────────────────────────
    DATABASE_URL: str = "postgresql://covan_user:covan_local_2026@localhost:5432/covan_db"

    # ── ChromaDB ─────────────────────────────────────────
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8100

    # ── Mem0 (bộ nhớ dài hạn) ────────────────────────────
    MEM0_API_KEY: str = ""
    MEM0_PROVIDER: str = "local"       # "local" | "cloud"
    MEM0_MAX_MEMORIES: int = 200       # Premium tier limit

    # ── Search Tools (trả phí — hoạt động khi có key) ────
    TAVILY_API_KEY: str = ""           # https://tavily.com
    SERP_API_KEY: str = ""             # https://serpapi.com

    # ── Auth (JWT) ───────────────────────────────────────
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── Logging ──────────────────────────────────────────
    LOG_LEVEL: str = "INFO"

    # ── Redis (cache + rate limiting) ─────────────────────
    REDIS_URL: str = ""                # redis://localhost:6379/0

    # ── Stripe (payment — kích hoạt khi có key) ──────────
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # ── S3/R2 (file storage — optional) ──────────────────
    S3_ENDPOINT: str = ""
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_BUCKET: str = "covankn-files"

    # ── Email (Resend — kích hoạt khi có key) ────────────
    RESEND_API_KEY: str = ""

    # ── Frontend ─────────────────────────────────────────
    FRONTEND_URL: str = "http://localhost:3000"

    # ── Google OAuth 2.0 ─────────────────────────────────
    GOOGLE_CLIENT_ID: str = ""  # Từ Google Cloud Console

    model_config = {
        "env_file": str(ENV_FILE),
        "env_file_encoding": "utf-8",
        "extra": "ignore",         # Bỏ qua biến .env không khai báo ở đây
    }


# Singleton (dùng chung 1 instance toàn app)
settings = Settings()
