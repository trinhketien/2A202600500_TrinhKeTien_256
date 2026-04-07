"""
DebateSession model — một phiên tranh luận của người dùng.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base


class DebateSession(Base):
    __tablename__ = "debate_sessions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Ý tưởng kinh doanh người dùng nhập
    idea: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    # Ngành nghề (F&B, tech, giáo dục, ecom...)
    industry: Mapped[str] = mapped_column(
        String(100),
        nullable=True,
    )
    # Trạng thái phiên
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",  # pending → debating → completed → error
    )
    # Số vòng tranh luận
    round_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    # Report Card — JSON string từ report_card.py
    report_card: Mapped[str] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    user = relationship("User", back_populates="sessions")
    messages = relationship("Message", back_populates="session", order_by="Message.created_at")

    def __repr__(self) -> str:
        return f"<DebateSession {self.id[:8]}... status={self.status}>"
