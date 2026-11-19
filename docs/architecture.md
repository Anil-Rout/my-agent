# Architecture Overview

This project currently contains two overlapping architectures:

- a legacy desktop-first Python application
- a newer backend plus frontend structure built around FastAPI and Flutter

The newer `backend/` and `frontend/` trees are the clearest representation of where the project is heading, but the legacy modules still exist and are partly functional. Treat the repository as a codebase in transition.

## High-level view

### Preferred long-term flow

```text
Flutter frontend
    |
    v
FastAPI backend
    |
    v
LangGraph agent
    |
    +--> LLM providers
    |      - Groq
    |      - OpenRouter
    |      - Ollama fallback
    |
    +--> Memory
    |      - Pinecone
    |
    +--> Data and cache
    |      - Supabase / PostgreSQL
    |      - Upstash Redis
    |
    +--> Tool layer
           - files
           - apps
           - system info
           - browser/search
           - code execution
           - reminders
```

### Legacy flow still present in the repo

```text
run.py
    |
    v
desktop/
    |
    v
agent/
    |
    v
actions/
    |
    v
database/
```

## Main code areas

### Newer backend structure

- `backend/run.py`
  Starts the FastAPI server with Uvicorn.

- `backend/api/main.py`
  Creates the FastAPI app, enables CORS, and registers route groups.

- `backend/api/routes/`
  Contains route handlers for chat, tools, and system endpoints.

- `backend/brain/`
  Contains LLM setup, prompt logic, memory integration, and the LangGraph agent flow.

- `backend/tools/`
  Contains callable actions the agent can use for file management, system inspection, app control, browser actions, code execution, and reminders.

- `backend/database/`
  Contains database access code, cache support, and storage adapters.

- `backend/config/`
  Reads environment variables and centralizes configuration values.

### Frontend structure

- `frontend/lib/main.dart`
  Flutter app entry point.

- `frontend/lib/screens/`
  Main screens such as splash, login, chat, settings, and history.

- `frontend/lib/services/`
  API, auth, and local storage integrations.

- `frontend/lib/providers/`
  State management for auth, chat, and agent state.

### Legacy structure

- `desktop/`
  Older Python UI layer.

- `agent/`
  Older assistant and memory logic.

- `actions/`
  Older tool/action modules.

- `server/`
  Older FastAPI-style backend layer.

- `database/`
  Older database implementation.

## Backend request flow

In the newer design, the intended chat flow is:

```text
User sends a message
    |
    v
Frontend calls FastAPI
    |
    v
Route handler receives request
    |
    v
Agent loads relevant memory
    |
    v
LLM decides whether tools are needed
    |
    v
Selected tools execute
    |
    v
Response is returned and saved to memory
```

The LangGraph-based orchestration is defined in `backend/brain/agent.py`. That file wires together:

- memory loading
- model invocation
- tool execution
- memory saving

## Data and provider responsibilities

### AI providers

The backend is designed to support multiple model providers:

- Groq as the main cloud LLM
- OpenRouter as an alternate cloud provider
- Ollama as a local fallback when tool-capable cloud access is unavailable

### Memory

Pinecone is used for semantic memory retrieval in the newer backend flow.

### Database and cache

The configuration references:

- Supabase / PostgreSQL for persistent data
- Upstash Redis for caching
- SQLite as a local database fallback in some paths

## Important reality check

The architecture described above is the intended direction, but the implementation is not fully consolidated yet.

Current gaps or overlaps include:

- duplicate concepts between `agent/` and `backend/brain/`
- duplicate API/server concepts between `server/` and `backend/api/`
- documentation that previously described only the legacy structure
- newer API routes that are still partially stubbed

## Recommended source of truth

If you continue development, the safest modules to treat as the primary direction are:

- `backend/`
- `frontend/`
- `docs/`

The legacy folders are still useful for reference, but they should eventually be merged, archived, or removed once the preferred architecture is finalized.
