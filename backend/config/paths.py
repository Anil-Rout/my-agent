from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
ENV_FILE = BACKEND_DIR / ".env"
LOGS_DIR = BACKEND_DIR / "logs"
DATABASE_DIR = BACKEND_DIR / "database"
ACTIVITY_LOG_PATH = LOGS_DIR / "activity.log"
TOOL_ACTIVITY_LOG_PATH = LOGS_DIR / "tool_activity.log"


def load_backend_env(override: bool = False) -> None:
    load_dotenv(ENV_FILE, override=override)


def ensure_runtime_dirs() -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)


def resolve_sqlite_url(database_url: str) -> str:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return database_url

    raw_path = database_url[len(prefix):]
    if raw_path == ":memory:":
        return database_url

    sqlite_path = Path(raw_path)
    if sqlite_path.is_absolute():
        return database_url

    resolved = (BACKEND_DIR / sqlite_path).resolve()
    return f"{prefix}{resolved.as_posix()}"
