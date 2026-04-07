"""
Message model — mỗi message là 1 phát biểu của 1 agent trong 1 phiên.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, Float, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_messages_session_round", "session_id", "round_number"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("debate_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Agent nào phát biểu: strategy | finance | market | technical | legal | moderator | user
    agent_name: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    # Vai trò hiển thị trên UI: 🎯 Chiến Lược, 💰 Tài Chính, ...
    agent_display: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
    )
    # Nội dung phát biểu
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    # Vòng tranh luận (round 1, 2, 3...)
    round_number: Mapped[int] = mapped_column(
        Integer,
        default=1,
    )
    # Token đã dùng (theo dõi chi phí)
    tokens_used: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
    )
    # Chi phí ước tính (USD)
    cost_usd: Mapped[float] = mapped_column(
        Float,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationship
    session = relationship("DebateSession", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message {self.agent_name} round={self.round_number}>"
