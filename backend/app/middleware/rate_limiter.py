"""
Rate Limiter — SlowAPI + Redis (fallback in-memory).

Limits per tier:
  Free:    5 req/min cho /stream
  Pro:     15 req/min
  Premium: 30 req/min
"""

import logging
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.app.config import settings

logger = logging.getLogger(__name__)

# Chọn storage backend
storage_uri = settings.REDIS_URL if settings.REDIS_URL else "memory://"
logger.info(f"[RateLimit] Storage: {storage_uri}")

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=storage_uri,
    default_limits=["60/minute"],  # Global default
)


async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler cho rate limit exceeded."""
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Bạn đã gửi quá nhiều request. Vui lòng thử lại sau.",
            "retry_after": str(exc.detail),
        },
    )
