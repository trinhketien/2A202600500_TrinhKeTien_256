"""
Seed script — Tạo admin mặc định.
Fix #7: Admin mặc định tạo bằng script seed.
Bonus A: Đọc email/password từ biến môi trường (không hardcode).

Chạy: python -m backend.seed_admin
"""

import os
from dotenv import load_dotenv

# Load .env trước khi import config
load_dotenv()

from backend.app.database import SessionLocal, engine, Base
from backend.app.models.user import User, UserRole
from backend.app.services.auth import hash_password

# Import tất cả models để Base.metadata biết
import backend.app.models  # noqa: F401


def seed():
    """Tạo tất cả bảng + admin mặc định nếu chưa có."""

    # Tạo bảng (an toàn — không xóa bảng đã có)
    Base.metadata.create_all(bind=engine)
    print("[seed] Tables created/verified.")

    # Đọc từ biến môi trường — không hardcode password
    admin_email = os.getenv("ADMIN_EMAIL", "admin@covankn.ai")
    admin_password = os.getenv("ADMIN_PASSWORD", "Admin@2026!")

    db = SessionLocal()
    try:
        # Kiểm tra admin đã tồn tại chưa
        admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
        if admin:
            print(f"[seed] Admin already exists: {admin.email}")
            return

        # Tạo admin mới
        admin_user = User(
            email=admin_email,
            hashed_password=hash_password(admin_password),
            full_name="Admin He Thong",
            role=UserRole.ADMIN,
        )
        db.add(admin_user)
        db.commit()
        print("[seed] Admin created:")
        print(f"  Email:    {admin_email}")
        print(f"  Password: (from ADMIN_PASSWORD in .env)")
        print(f"  Role:     admin")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
