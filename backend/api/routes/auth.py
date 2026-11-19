from fastapi import APIRouter, Depends, HTTPException, status

from api.auth import (
    LoginRequest,
    TokenResponse,
    authenticate_password,
    create_access_token,
)
from api.rate_limit import limit_requests


router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(
    request: LoginRequest,
    _: None = Depends(
        limit_requests(
            bucket="auth_login",
            env_name="RATE_LIMIT_AUTH_PER_MINUTE",
            default_limit=10,
        )
    ),
):
    if not authenticate_password(request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password.",
        )

    token, expires_in = create_access_token()
    return TokenResponse(access_token=token, expires_in=expires_in)
