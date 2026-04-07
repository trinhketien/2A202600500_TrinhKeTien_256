"""
User model — Fix #6 (Auth nền tảng) + Fix #7 (Phân quyền role-based)
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from backend.app.database import Base


class UserRole(str, enum.Enum):
    """Vai trò người dùng — Fix #7"""
    USER = "user"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(
        String(100),
        nullable=True,
    )
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole),
        default=UserRole.USER,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )
    # Gói dịch vụ (phân quyền ở Bước 12 — tier_config.py)
    tier: Mapped[str] = mapped_column(
        String(20),
        default="free",
    )
    # Phương thức đăng nhập: "email" | "google"
    auth_provider: Mapped[str] = mapped_column(
        String(20),
        default="email",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationship (quan hệ) — 1 user có nhiều debate sessions
    sessions = relationship("DebateSession", back_populates="user")

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role.value})>"
