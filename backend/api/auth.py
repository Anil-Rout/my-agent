import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, Field


ALGORITHM = "HS256"
bearer_scheme = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    password: str = Field(..., min_length=1, max_length=256)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


def _secret_key() -> str:
    return os.getenv("SECRET_KEY", "changeme").strip() or "changeme"


def _access_token_expiry_seconds() -> int:
    minutes = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))
    return max(minutes, 1) * 60


def _agent_password() -> str:
    return os.getenv("AGENT_PASSWORD", "agent123")


def authenticate_password(password: str) -> bool:
    expected_password = _agent_password()
    if not expected_password:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent password is not configured.",
        )

    return secrets.compare_digest(password, expected_password)


def create_access_token(subject: str = "local-owner") -> tuple[str, int]:
    expires_in = _access_token_expiry_seconds()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=expires_in)
    payload = {
        "sub": subject,
        "iat": now,
        "exp": expires_at,
    }

    token = jwt.encode(payload, _secret_key(), algorithm=ALGORITHM)
    return token, expires_in


def require_authenticated_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            _secret_key(),
            algorithms=[ALGORITHM],
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    subject = (payload.get("sub") or "").strip()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    request.state.user_id = subject
    return subject


def require_api_token(user: str = Depends(require_authenticated_user)) -> str:
    return user
