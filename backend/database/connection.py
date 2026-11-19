from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from config.paths import ensure_runtime_dirs, resolve_sqlite_url
from config.settings import DATABASE_URL
from database.models import Base


SQLITE_FALLBACK_URL = resolve_sqlite_url("sqlite:///database/agent.db")
ACTIVE_DATABASE_URL = DATABASE_URL


def _is_sqlite_url(database_url: str) -> bool:
    return database_url.startswith("sqlite:///")


def _build_engine(database_url: str):
    return create_engine(
        database_url,
        connect_args={"check_same_thread": False} if _is_sqlite_url(database_url) else {},
    )


engine = _build_engine(ACTIVE_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def _switch_to_sqlite_fallback(reason: Exception) -> None:
    global engine, ACTIVE_DATABASE_URL

    if ACTIVE_DATABASE_URL == SQLITE_FALLBACK_URL:
        raise reason

    print(
        "Database init failed for configured DATABASE_URL; "
        "falling back to local SQLite."
    )
    ACTIVE_DATABASE_URL = SQLITE_FALLBACK_URL
    engine = _build_engine(ACTIVE_DATABASE_URL)
    SessionLocal.configure(bind=engine)


def _apply_sqlite_migrations() -> None:
    if not _is_sqlite_url(ACTIVE_DATABASE_URL):
        return

    inspector = inspect(engine)
    if "messages" not in inspector.get_table_names():
        return

    message_columns = {column["name"] for column in inspector.get_columns("messages")}

    with engine.begin() as connection:
        if "user_id" not in message_columns:
            connection.execute(
                text(
                    "ALTER TABLE messages "
                    "ADD COLUMN user_id VARCHAR(100) DEFAULT 'local-owner'"
                )
            )


def init_database():
    """Create tables and apply lightweight local migrations."""
    ensure_runtime_dirs()
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as exc:
        _switch_to_sqlite_fallback(exc)
        Base.metadata.create_all(bind=engine)

    _apply_sqlite_migrations()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
