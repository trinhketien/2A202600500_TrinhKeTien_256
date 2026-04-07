"""
Pydantic schemas cho Auth — kiểm tra dữ liệu đầu vào/đầu ra.
"""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from backend.app.models.user import UserRole


# ── Request schemas (client gửi lên) ───────────────────

class UserRegister(BaseModel):
    """Dữ liệu đăng ký tài khoản."""
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    full_name: str = Field(default="", max_length=100)


class UserLogin(BaseModel):
    """Dữ liệu đăng nhập."""
    email: EmailStr
    password: str


# ── Response schemas (server trả về) ───────────────────

class UserResponse(BaseModel):
    """Thông tin user trả về client — KHÔNG bao giờ trả password."""
    id: str
    email: str
    full_name: str | None
    role: UserRole
    is_active: bool
    tier: str = "free"
    auth_provider: str = "email"
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """JWT token trả về sau khi đăng nhập thành công."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
