# settings.py — reads ALL config from .env
# Change .env file to switch any technology

import os

from config.paths import load_backend_env, resolve_sqlite_url


load_backend_env()


def _parse_csv_env(name: str, default: str) -> list[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]

# AI Settings
GROQ_API_KEY    = os.getenv("GROQ_API_KEY")
AI_MODEL        = os.getenv("AI_MODEL", "llama-3.3-70b-versatile")

# Memory Settings
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX   = os.getenv("PINECONE_INDEX", "agent-memory")
MEMORY_BACKEND   = os.getenv("MEMORY_BACKEND", "pinecone")

# Database Settings
SUPABASE_URL    = os.getenv("SUPABASE_URL")
SUPABASE_KEY    = os.getenv("SUPABASE_KEY")
DATABASE_URL    = resolve_sqlite_url(os.getenv("DATABASE_URL", "sqlite:///database/agent.db"))

_declared_db_backend = os.getenv("DB_BACKEND", "").strip().lower()
if DATABASE_URL.startswith("sqlite:///"):
    DB_BACKEND = "sqlite"
elif DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://"):
    DB_BACKEND = "postgresql"
else:
    DB_BACKEND = _declared_db_backend or "postgresql"

# Cache Settings
REDIS_URL       = os.getenv("UPSTASH_REDIS_URL")
REDIS_TOKEN     = os.getenv("UPSTASH_REDIS_TOKEN")

# Security
SECRET_KEY      = os.getenv("SECRET_KEY", "changeme")
JWT_EXPIRE      = int(os.getenv("JWT_EXPIRE_MINUTES", 1440))
AGENT_PASSWORD  = os.getenv("AGENT_PASSWORD", "agent123")

# Server
SERVER_HOST     = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT     = int(os.getenv("SERVER_PORT", 8000))
DEBUG           = os.getenv("DEBUG", "False") == "True"
CORS_ALLOWED_ORIGINS = _parse_csv_env(
    "CORS_ALLOWED_ORIGINS",
    ",".join(
        [
            "http://localhost",
            "http://localhost:3000",
            "http://localhost:8000",
            "http://127.0.0.1",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8000",
            "http://10.0.2.2:8000",
        ]
    ),
)
