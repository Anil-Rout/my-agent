import os
import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, Request, status


_RATE_LIMIT_STORE: dict[str, deque[float]] = defaultdict(deque)
_RATE_LIMIT_LOCK = Lock()


def reset_rate_limits() -> None:
    with _RATE_LIMIT_LOCK:
        _RATE_LIMIT_STORE.clear()


def _get_limit(env_name: str, default: int) -> int:
    try:
        return max(int(os.getenv(env_name, str(default))), 1)
    except ValueError:
        return default


def _build_key(request: Request, bucket: str) -> str:
    user_id = getattr(request.state, "user_id", "")
    client_host = getattr(request.client, "host", "") or "anonymous"
    identifier = user_id or client_host
    return f"{bucket}:{identifier}"


def limit_requests(
    *,
    bucket: str,
    env_name: str,
    default_limit: int,
    window_seconds: int = 60,
):
    def dependency(request: Request) -> None:
        limit = _get_limit(env_name, default_limit)
        key = _build_key(request, bucket)
        now = time.time()

        with _RATE_LIMIT_LOCK:
            attempts = _RATE_LIMIT_STORE[key]
            while attempts and attempts[0] <= now - window_seconds:
                attempts.popleft()

            if len(attempts) >= limit:
                retry_after = max(1, int(window_seconds - (now - attempts[0])))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please wait and try again.",
                    headers={"Retry-After": str(retry_after)},
                )

            attempts.append(now)

    return dependency
