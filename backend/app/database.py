"""
Kết nối Database — SQLAlchemy async-compatible engine + session factory.
Dùng pattern:  with get_db() as db:  ...
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from backend.app.config import settings

# Engine — kết nối tới PostgreSQL (local hoặc Neon/Supabase cloud)
_db_url = settings.DATABASE_URL
_is_local = "localhost" in _db_url or "127.0.0.1" in _db_url

# Neon/Supabase cần sslmode=require
_connect_args = {}
if "neon.tech" in _db_url or "supabase" in _db_url:
    _connect_args = {"sslmode": "require"}

engine = create_engine(
    _db_url,
    pool_pre_ping=True,              # Kiểm tra kết nối còn sống trước khi dùng
    pool_size=20 if _is_local else 5,        # Free tier cloud: ít connection
    max_overflow=30 if _is_local else 5,
    pool_timeout=30,                 # Timeout chờ kết nối (giây)
    pool_recycle=1800,               # Recycle kết nối sau 30 phút (tránh stale)
    echo=False,                      # True = in SQL ra console (debug)
    connect_args=_connect_args,
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
