"""
API Dependencies — dùng chung giữa các routes.
Fix #6: JWT middleware bảo vệ endpoint
Fix #7: Phân quyền role-based (require_admin)
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.app.database import SessionLocal
from backend.app.services.auth import decode_access_token
from backend.app.models.user import User, UserRole


# ── Database session per request ────────────────────────

def get_db():
    """
    Mỗi API request nhận 1 DB session riêng.
    Tự đóng sau khi request xong (yield pattern).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── JWT Authentication ──────────────────────────────────

security = HTTPBearer()
# HTTPBearer: FastAPI tự trích xuất token từ header "Authorization: Bearer <token>"


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Middleware xác thực — chạy trước mọi endpoint được bảo vệ.
    Giải mã JWT → tìm user trong DB → trả về User object.
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token thiếu thông tin người dùng",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy tài khoản",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị khóa",
        )

    return user


# ── Role-based Access — Fix #7 ──────────────────────────

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Middleware phân quyền — chỉ admin mới được truy cập.
    Dùng cho: quản lý user, xem thống kê toàn hệ thống.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ admin mới có quyền truy cập",
        )
    return current_user


# ── SSE/WebSocket Auth (query param) ────────────────────

def get_current_user_from_token(
    token: str,
    db: Session,
) -> User:
    """
    Xác thực bằng JWT token truyền qua query parameter.
    Dùng cho SSE endpoint (EventSource không gửi được header Authorization).
    """
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token thiếu thông tin người dùng",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy tài khoản",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị khóa",
        )

    return user
