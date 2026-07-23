import jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from app.core.config import get_settings
from app.core.constants import ALLOWED_ROLES


def verify_analytics_role(credentials: HTTPAuthorizationCredentials | None) -> dict:
    """Verify authorization token and ensure the user possesses an authorized role."""
    settings = get_settings()
    if not settings.require_auth:
        return {"role": "admin", "auth_disabled": True}

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is required.",
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=["HS256"],
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        ) from exc

    role = str(payload.get("role") or payload.get("user_role") or "").lower()
    if role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions.",
        )

    return payload
