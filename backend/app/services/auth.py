"""
Auth service — hash password + tạo/verify JWT token.
Fix #6: Auth nền tảng | Fix #7: Phân quyền role-based
"""

from datetime import datetime, timedelta, timezone
import bcrypt
from jose import jwt, JWTError

from backend.app.config import settings


# ── Password hashing (bcrypt trực tiếp) ─────────────────
# bcrypt: thuật toán hash 1 chiều — không thể giải ngược password


def hash_password(password: str) -> str:
    """Mã hóa password thành hash — lưu vào DB."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """So sánh password người dùng nhập với hash trong DB."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


# ── JWT Token ───────────────────────────────────────────

def create_access_token(user_id: str, role: str) -> str:
    """
    Tạo JWT token chứa user_id và role.
    Token có thời hạn (mặc định 60 phút).
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": user_id,       # subject — ai sở hữu token
        "role": role,         # admin / user
        "exp": expire,        # hết hạn lúc nào
    }
    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict | None:
    """
    Giải mã JWT token → trả về payload.
    Trả None nếu token hết hạn hoặc bị sửa (tampered).
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        return None
