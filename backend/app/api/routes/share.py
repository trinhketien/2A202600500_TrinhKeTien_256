"""
Share Routes — tạo/xóa/xem link chia sẻ debate session.

POST /api/share           → Tạo share link (auth required)
GET  /api/share/{share_id} → Xem shared session (public, NO auth)
DELETE /api/share/{share_id} → Xóa share link (auth, owner only)
"""

import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.api.deps import get_db, get_current_user
from backend.app.models.shared_link import SharedLink
from backend.app.models.session import DebateSession
from backend.app.models.message import Message
from backend.app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/share", tags=["Share"])


# ── Schemas ──────────────────────────────────────────────

class ShareCreateRequest(BaseModel):
    session_id: str


class ShareCreateResponse(BaseModel):
    share_id: str
    url: str


class SharedSessionResponse(BaseModel):
    idea: str
    industry: str | None
    messages: list[dict]
    report_card: dict | None
    shared_by: str
    created_at: str

    model_config = {"from_attributes": True}


# ── Endpoints ────────────────────────────────────────────

@router.post(
    "",
    response_model=ShareCreateResponse,
    summary="Tạo link chia sẻ",
)
def create_share_link(
    body: ShareCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Tạo shared link cho debate session (owner only)."""
    # Tier check: can_share
    from ai_engine.tier_config import get_tier_limits
    limits = get_tier_limits(getattr(current_user, "tier", "free") or "free")
    if not limits["can_share"]:
        raise HTTPException(
            status_code=403,
            detail="Nâng cấp Pro hoặc Premium để sử dụng tính năng chia sẻ",
        )

    # Verify session belongs to user
    session = db.query(DebateSession).filter(
        DebateSession.id == body.session_id,
        DebateSession.user_id == current_user.id,
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên")

    if session.status != "completed":
        raise HTTPException(status_code=400, detail="Phiên chưa hoàn thành")

    # Check existing share link
    existing = db.query(SharedLink).filter(
        SharedLink.session_id == body.session_id,
        SharedLink.created_by == current_user.id,
        SharedLink.is_active == True,
    ).first()

    if existing:
        return ShareCreateResponse(
            share_id=existing.id,
            url=f"/shared/{existing.id}",
        )

    # Create new
    link = SharedLink(
        session_id=body.session_id,
        created_by=current_user.id,
    )
    db.add(link)
    db.commit()
    db.refresh(link)

    logger.info(f"[Share] Created link {link.id} for session {body.session_id[:8]}")

    return ShareCreateResponse(
        share_id=link.id,
        url=f"/shared/{link.id}",
    )


@router.get(
    "/{share_id}",
    response_model=SharedSessionResponse,
    summary="Xem shared session (public)",
)
def get_shared_session(
    share_id: str,
    db: Session = Depends(get_db),
):
    """Xem debate session qua share link — KHÔNG cần đăng nhập."""
    link = db.query(SharedLink).filter(
        SharedLink.id == share_id,
        SharedLink.is_active == True,
    ).first()

    if not link:
        raise HTTPException(status_code=404, detail="Link không tồn tại hoặc đã hết hạn")

    # Increment view count
    link.view_count = (link.view_count or 0) + 1
    db.commit()

    # Get session data
    session = db.query(DebateSession).filter(
        DebateSession.id == link.session_id,
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Phiên đã bị xóa")

    # Get messages
    messages = db.query(Message).filter(
        Message.session_id == link.session_id,
    ).order_by(Message.created_at).all()

    msg_list = [{
        "agent_name": m.agent_name,
        "agent_display": m.agent_display or m.agent_name,
        "content": m.content,
        "round_number": m.round_number,
    } for m in messages]

    # Get creator name
    creator = db.query(User).filter(User.id == link.created_by).first()
    shared_by = creator.full_name or creator.email if creator else "Anonymous"

    # Parse report card
    report_card = None
    if session.report_card:
        try:
            report_card = json.loads(session.report_card)
        except Exception:
            pass

    return SharedSessionResponse(
        idea=session.idea,
        industry=session.industry,
        messages=msg_list,
        report_card=report_card,
        shared_by=shared_by,
        created_at=session.created_at.isoformat() if session.created_at else "",
    )


@router.delete(
    "/{share_id}",
    summary="Xóa share link",
)
def delete_share_link(
    share_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Xóa share link (chỉ owner)."""
    link = db.query(SharedLink).filter(
        SharedLink.id == share_id,
        SharedLink.created_by == current_user.id,
    ).first()

    if not link:
        raise HTTPException(status_code=404, detail="Không tìm thấy link")

    link.is_active = False
    db.commit()

    return {"message": "Đã xóa link chia sẻ"}
