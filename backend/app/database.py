"""
Kết nối Database — SQLAlchemy async-compatible engine + session factory.
Dùng pattern:  with get_db() as db:  ...
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from backend.app.config import settings

# Engine — kết nối tới PostgreSQL
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,       # Kiểm tra kết nối còn sống trước khi dùng
    pool_size=20,             # Số kết nối giữ sẵn (scale 10K+ users)
    max_overflow=30,          # Số kết nối tạo thêm khi cần
    pool_timeout=30,          # Timeout chờ kết nối (giây)
    pool_recycle=1800,        # Recycle kết nối sau 30 phút (tránh stale)
    echo=False,               # True = in SQL ra console (debug)
)

# Session factory — tạo session cho mỗi request
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class cho tất cả SQLAlchemy models."""
    pass
