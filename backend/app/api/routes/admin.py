"""
Admin routes — Quản lý user + thống kê hệ thống.
Fix #8: Admin panel quản lý user.
Tất cả endpoint trong file này yêu cầu role=admin.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.api.deps import get_db, require_admin
from backend.app.models.user import User, UserRole
from backend.app.models.session import DebateSession
from backend.app.models.message import Message
from backend.app.schemas.auth import UserResponse

router = APIRouter(
    prefix="/admin",
    tags=["Admin — Quản trị"],
    dependencies=[Depends(require_admin)],  # Mọi route đều cần admin
)


@router.get(
    "/users",
    response_model=list[UserResponse],
    summary="Danh sách tất cả user",
)
def list_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
):
    """Admin xem danh sách user — phân trang."""
    users = (
        db.query(User)
        .order_by(User.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [UserResponse.model_validate(u) for u in users]


@router.patch(
    "/users/{user_id}/toggle-active",
    response_model=UserResponse,
    summary="Khóa / mở khóa tài khoản",
)
def toggle_user_active(
    user_id: str,
    db: Session = Depends(get_db),
):
    """
    Toggle (đảo ngược) trạng thái is_active của user.
    Active → Bị khóa | Bị khóa → Active.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy user",
        )
    if user.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Không thể khóa tài khoản admin",
        )

    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa tài khoản user",
)
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
):
    """Xóa user + tất cả sessions/messages của user (CASCADE)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy user",
        )
    if user.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Không thể xóa tài khoản admin",
        )

    db.delete(user)
    db.commit()


@router.get(
    "/stats",
    summary="Thống kê tổng quan hệ thống",
)
def get_stats(db: Session = Depends(get_db)):
    """
    Trả về thống kê: tổng user, tổng phiên, tổng token đã dùng.
    Dùng cho trang Admin Dashboard.
    """
    total_users = db.query(func.count(User.id)).scalar()
    total_sessions = db.query(func.count(DebateSession.id)).scalar()
    total_messages = db.query(func.count(Message.id)).scalar()
    total_tokens = db.query(func.coalesce(func.sum(Message.tokens_used), 0)).scalar()
    total_cost = db.query(func.coalesce(func.sum(Message.cost_usd), 0.0)).scalar()

    return {
        "total_users": total_users,
        "total_sessions": total_sessions,
        "total_messages": total_messages,
        "total_tokens_used": total_tokens,
        "total_cost_usd": round(float(total_cost), 4),
    }
