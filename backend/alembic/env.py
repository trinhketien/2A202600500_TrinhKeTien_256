"""
Alembic env.py — Cấu hình để tự động detect models + đọc DATABASE_URL từ .env.
"""

import sys
from pathlib import Path
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Thêm thư mục gốc dự án vào sys.path để import backend.app.*
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load .env
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

# Import config + tất cả models
from backend.app.config import settings
from backend.app.database import Base
import backend.app.models  # noqa: F401 — cần import để Base biết models

# Alembic Config
config = context.config

# Override (ghi đè) sqlalchemy.url bằng giá trị từ .env
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Setup logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata cho autogenerate — Alembic so sánh DB thật vs models để tạo migration
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Chạy migrations offline (không cần kết nối DB thật)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Chạy migrations online (kết nối DB thật)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
