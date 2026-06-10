"""Shared slowapi limiter.

Auth-write endpoints (login/signup/forgot/reset) get a tight per-IP limit
to blunt credential stuffing and reset-email abuse; everything else falls
under a looser default. Disabled in tests via RATE_LIMIT_ENABLED=false so
the suite can fire many requests without tripping 429s.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.config import settings

# Tight limit applied by decorator to auth-write routes.
AUTH_WRITE_LIMIT = "5/minute"

limiter = Limiter(
    key_func=get_remote_address,
    enabled=settings.rate_limit_enabled,
    default_limits=["60/minute"],
)
