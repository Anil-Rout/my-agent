from contextlib import asynccontextmanager
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from api.errors import register_exception_handlers
from api.routes import auth, chat, system, tools, web_ui
from config.paths import ACTIVITY_LOG_PATH, ensure_runtime_dirs
from config.settings import CORS_ALLOWED_ORIGINS
from database.connection import init_database


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_runtime_dirs()
    init_database()
    # Clear LLM cache to pick up new model settings
    try:
        from brain.llm import clear_llm_cache
        clear_llm_cache()
        print("LLM cache cleared.")
    except Exception:
        pass
    try:
        from tools.pc_profile import get_or_build_profile, format_profile_for_prompt
        profile = get_or_build_profile()
        print(f"PC Profile loaded: {profile.get('computer_name')} | {profile.get('ram_total_gb')}GB RAM")
    except Exception as e:
        print(f"PC Profile warning: {e}")
    yield


app = FastAPI(
    title="My Agent API",
    description="Personal AI Agent controls your PC via API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

register_exception_handlers(app)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    request_id = request.headers.get("X-Request-ID", "").strip() or uuid.uuid4().hex
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    duration = round(time.time() - start, 3)
    ensure_runtime_dirs()
    with ACTIVITY_LOG_PATH.open("a", encoding="utf-8") as file_handle:
        file_handle.write(
            f"[request_id={request_id}] "
            f"{time.strftime('%Y-%m-%d %H:%M:%S')} | "
            f"{request.method} {request.url.path} | "
            f"{response.status_code} | {duration}s\n"
        )
    return response


app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(system.router, prefix="/system", tags=["System"])
app.include_router(tools.router, prefix="/tools", tags=["Tools"])
app.include_router(web_ui.router, tags=["UI"])

@app.get("/")
def root():
    return {
        "status": "Agent is running",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": time.time()}
