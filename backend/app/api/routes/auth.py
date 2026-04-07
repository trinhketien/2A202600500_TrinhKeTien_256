"""
Auth routes — Đăng ký + Đăng nhập + Google OAuth + Xem profile.
Fix #6: Auth là nền tảng, xây ngay từ đầu.
Enhancement: Google OAuth 2.0 (Option B — Frontend sends id_token).
Security: Rate limit login/register.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.api.deps import get_db, get_current_user
from backend.app.config import settings
from backend.app.models.user import User
from backend.app.schemas.auth import UserRegister, UserLogin, UserResponse, TokenResponse
from backend.app.services.auth import hash_password, verify_password, create_access_token
from backend.app.middleware.rate_limiter import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth — Xác thực"])


# ── Google OAuth Schema ──────────────────────────────────

class GoogleLoginRequest(BaseModel):
    id_token: str


# ── Register ─────────────────────────────────────────────

@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Đăng ký tài khoản mới",
)
@limiter.limit("3/minute")
def register(request: Request, data: UserRegister, db: Session = Depends(get_db)):
    """
    Tạo tài khoản mới → trả JWT token ngay (không cần đăng nhập lại).
    """
    # Kiểm tra email đã tồn tại chưa
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email đã được đăng ký",
        )

    # Tạo user mới
    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name or None,
        auth_provider="email",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Trả token ngay
    token = create_access_token(user.id, user.role.value)
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


# ── Login ────────────────────────────────────────────────

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Đăng nhập",
)
@limiter.limit("5/minute")
def login(request: Request, data: UserLogin, db: Session = Depends(get_db)):
    """
    Đăng nhập bằng email + password → trả JWT token.
    """
    user = db.query(User).filter(User.email == data.email).first()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không đúng",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị khóa",
        )

    # Block Google users from email login
    if getattr(user, "auth_provider", "email") == "google":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tài khoản này đăng nhập bằng Google. Vui lòng sử dụng nút Google.",
        )

    token = create_access_token(user.id, user.role.value)
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


# ── Google OAuth 2.0 ─────────────────────────────────────

@router.post(
    "/google",
    response_model=TokenResponse,
    summary="Đăng nhập bằng Google",
)
@limiter.limit("10/minute")
def google_login(request: Request, body: GoogleLoginRequest, db: Session = Depends(get_db)):
    """
    Frontend gửi Google id_token → Backend verify → tạo/lấy user → trả JWT.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=503,
            detail="Google OAuth chưa được cấu hình. Thêm GOOGLE_CLIENT_ID vào .env.",
        )

    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests

        # Verify Google token
        idinfo = id_token.verify_oauth2_token(
            body.id_token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )

        email = idinfo.get("email")
        name = idinfo.get("name", "")

        if not email:
            raise HTTPException(400, "Google token không có email")

        # Tìm hoặc tạo user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                hashed_password="",  # Google user không cần password
                full_name=name,
                auth_provider="google",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"[Auth] New Google user: {email}")

        token = create_access_token(user.id, user.role.value)
        return TokenResponse(
            access_token=token,
            user=UserResponse.model_validate(user),
        )

    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="google-auth SDK chưa install. Chạy: pip install google-auth",
        )
    except ValueError as e:
        logger.warning(f"[Auth] Google token invalid: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google token không hợp lệ",
        )


# ── Profile ──────────────────────────────────────────────

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Xem thông tin tài khoản hiện tại",
)
def get_profile(current_user: User = Depends(get_current_user)):
    """Trả về thông tin user đang đăng nhập (decode từ JWT token)."""
    return UserResponse.model_validate(current_user)
