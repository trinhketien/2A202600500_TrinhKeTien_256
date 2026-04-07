# Models package — import tất cả models ở đây để Alembic phát hiện
from backend.app.models.user import User
from backend.app.models.session import DebateSession
from backend.app.models.message import Message
from backend.app.models.shared_link import SharedLink

__all__ = ["User", "DebateSession", "Message", "SharedLink"]
