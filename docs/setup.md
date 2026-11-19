# Setup Guide

This repository currently supports more than one project layout. The recommended path is to run the newer backend in `backend/` and optionally connect the Flutter frontend in `frontend/`.

## Recommended path

- Run the backend from `backend/`
- Use the Flutter app from `frontend/` if you want the newer UI
- Treat the root desktop launcher as legacy code that still needs consolidation

## Prerequisites

- Windows PC
- Python 3.10 or newer
- pip
- Git
- Internet access for cloud providers

Optional:

- Flutter SDK if you want to run the frontend
- Ollama if you want local model fallback

## 1. Clone or open the project

Open the repository in your editor or terminal.

```bash
cd my-agent
```

## 2. Install backend dependencies

The backend has its own dependency list and should be installed separately.

```bash
cd backend
pip install -r requirements.txt
```

## 3. Create `backend/.env`

The backend reads configuration from `backend/.env`.

At minimum, create the file and add the values you plan to use:

```env
GROQ_API_KEY=your_groq_key
AI_MODEL=llama-3.3-70b-versatile

PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX=agent-memory
MEMORY_BACKEND=pinecone

SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
DATABASE_URL=sqlite:///database/agent.db
DB_BACKEND=postgresql

UPSTASH_REDIS_URL=your_redis_url
UPSTASH_REDIS_TOKEN=your_redis_token

OPENROUTER_API_KEY=your_openrouter_key

SECRET_KEY=change_me
JWT_EXPIRE_MINUTES=1440
AGENT_PASSWORD=agent123

SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DEBUG=True
```

Notes:

- Some values have defaults in code, but it is better to define them explicitly.
- If you are not using every service immediately, you can still start by configuring the ones required for the path you are testing first.

## 4. Run the backend

From the `backend/` directory:

```bash
python run.py
```

If startup succeeds, the API should be available at:

- `http://localhost:8000`
- `http://localhost:8000/docs`

## 5. Verify the backend

Open this URL in your browser:

```text
http://localhost:8000
```

Expected response:

```json
{"status":"Agent is running","version":"1.0.0"}
```

## 6. Run the Flutter frontend (optional)

If you want to use the newer frontend, open a new terminal and run:

```bash
cd frontend
flutter pub get
flutter run -d windows
```

Make sure the backend is already running before starting the frontend.

## 7. Optional Ollama setup

If you want local fallback support, install Ollama and pull a model.

Example:

```bash
ollama pull llama3.1:8b
```

## Legacy desktop path

The repo still contains a root `run.py`, plus `desktop/`, `agent/`, and `actions/` modules from an older desktop-first version of the app.

Those files are useful for reference, but the repo is not fully consolidated yet. For day-to-day development, prefer the newer `backend/` and `frontend/` path unless you are specifically working on the legacy flow.

## Common issues

### Missing environment variables

If the app fails during startup, check that:

- `backend/.env` exists
- API keys are set correctly
- service-specific values such as Pinecone, Supabase, and Redis are present when required

### Python dependency issues

If package installation fails, verify:

- Python 3.10+ is installed
- `pip` is up to date
- you are running commands from the correct folder

### Flutter setup issues

If the frontend does not start:

- run `flutter doctor`
- confirm Windows desktop support is enabled
- make sure backend API URLs match the running backend

## Suggested next steps

- update `docs/usage.md` to match the current architecture
- decide whether `backend/` is now the primary source of truth
- consolidate or archive duplicate legacy modules once the preferred path is stable
