"""
Pydantic schemas cho Debate — phiên tranh luận.
"""

from pydantic import BaseModel, Field
from datetime import datetime


# ── Request ─────────────────────────────────────────────

class DebateCreate(BaseModel):
    """Tạo phiên tranh luận mới."""
    idea: str = Field(
        min_length=10,
        max_length=2000,
        description="Ý tưởng kinh doanh cần phản biện",
    )
    industry: str | None = Field(
        default=None,
        max_length=100,
        description="Ngành nghề (F&B, tech, giáo dục...)",
    )


# ── Response ────────────────────────────────────────────

class MessageResponse(BaseModel):
    """Một phát biểu của agent."""
    id: str
    agent_name: str
    agent_display: str | None
    content: str
    round_number: int
    tokens_used: int | None
    cost_usd: float | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DebateSessionResponse(BaseModel):
    """Thông tin phiên tranh luận."""
    id: str
    idea: str
    industry: str | None
    status: str
    round_count: int
    created_at: datetime
    messages: list[MessageResponse] = []
    report_card: dict | None = None

    model_config = {"from_attributes": True}
