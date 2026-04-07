"""
SharedLink model — link chia sẻ public cho debate session.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base


class SharedLink(Base):
    __tablename__ = "shared_links"

    id: Mapped[str] = mapped_column(
        String(8),
        primary_key=True,
        default=lambda: uuid.uuid4().hex[:8],
    )
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("debate_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )
    view_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    session = relationship("DebateSession")
    creator = relationship("User")

    def __repr__(self) -> str:
        return f"<SharedLink {self.id} session={self.session_id[:8]}>"
