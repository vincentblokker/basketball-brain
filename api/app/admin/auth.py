"""Admin auth — single shared bearer token via ADMIN_TOKEN env var."""
import secrets

from fastapi import Header, HTTPException, status

from app.config import settings


def require_admin(authorization: str = Header(default="")) -> None:
    """Dependency that validates Authorization: Bearer <ADMIN_TOKEN>.

    Uses constant-time compare to mitigate timing attacks. Returns None on
    success; raises 401 otherwise.
    """
    if not settings.admin_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin endpoints disabled — server is missing ADMIN_TOKEN.",
        )
    expected = f"Bearer {settings.admin_token}"
    # constant-time compare
    if not secrets.compare_digest(authorization, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin token.",
        )
