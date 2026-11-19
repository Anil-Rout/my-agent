from fastapi.encoders import jsonable_encoder
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "")


def _error_payload(
    request: Request,
    *,
    code: str,
    message: str,
    detail=None,
    extra: dict | None = None,
) -> dict:
    payload = {
        "success": False,
        "detail": message,
        "error": {
            "code": code,
            "message": message,
        },
        "request_id": _request_id(request),
    }
    if detail is not None:
        payload["error"]["detail"] = detail
    if extra:
        payload.update(extra)
    return payload


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        payload = _error_payload(
            request,
            code=f"http_{exc.status_code}",
            message=str(exc.detail),
        )
        headers = dict(exc.headers or {})
        if payload["request_id"]:
            headers.setdefault("X-Request-ID", payload["request_id"])
        return JSONResponse(
            status_code=exc.status_code,
            content=payload,
            headers=headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ):
        payload = _error_payload(
            request,
            code="validation_error",
            message="Request validation failed.",
            detail=jsonable_encoder(exc.errors()),
        )
        return JSONResponse(
            status_code=422,
            content=payload,
            headers={"X-Request-ID": payload["request_id"]},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        payload = _error_payload(
            request,
            code="internal_server_error",
            message="Internal server error.",
        )
        return JSONResponse(
            status_code=500,
            content=payload,
            headers={"X-Request-ID": payload["request_id"]},
        )
