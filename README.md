# My Agent

My Agent is a personal AI desktop assistant for Windows. It combines an LLM-powered agent, long-term memory, PC control tools, and multiple app surfaces so you can chat with an assistant that can both answer questions and take actions on your machine.

Start with this roadmap:

- [docs/roadmap.md](docs/roadmap.md) for the concrete backend plan and Phase 1 implementation backlog

Core chat agent
Make text chat solid first.
Learn:
FastAPI routes
request/response models
calling your brain.agent.chat(...)
basic testing with pytest
Goal:

user sends message
backend returns real AI reply reliably
Memory
Then improve memory.
Learn:
how memory.py works
embeddings
vector search
fallback behavior when Pinecone is unavailable
Goal:

assistant remembers useful context without breaking startup
Voice assistant
After text works well, add voice.
Learn:
speech-to-text
text-to-speech
microphone input flow
how frontend sends voice text to backend
Goal:

speak to agent and hear response
Online and offline modes
Then make provider switching clean.
Learn:
model routing
fallback logic
Ollama/local model usage
environment-based config
Goal:

cloud mode when internet is available
local mode when offline
Desktop and mobile clients
Then connect both apps.
Learn:
API integration from Flutter
auth/session handling
UI state management
syncing the same backend across devices
Goal:

same assistant accessible from desktop and mobile
Computer actions
Then expand tool power safely.
Learn:
file operations
app control
browser automation
permissions and safety checks
Goal:

assistant can do useful PC actions without being dangerous
Human-like workflow automation
This is the advanced stage.
Learn:
task planning
multi-step workflows
state tracking
confirmation before risky actions
Goal:

agent can handle bigger tasks, not just one command at a time
A very practical learning order for you right now:

understand chat.py
understand agent.py
understand memory.py
write backend API tests
then move to voice
then improve offline support
then connect frontend fully

## What the project is aiming for

- Understand natural language, not just fixed commands
- Remember past conversations with vector memory
- Control parts of a Windows PC such as files, apps, and system tasks
- Support multiple AI providers with fallback behavior
- Expose the assistant through desktop, backend, and frontend layers

## Current repo state

This repository contains two parallel structures:

- A desktop-first Python app under `desktop/`, `agent/`, `actions/`, and `server/`
- A newer backend/frontend structure under `backend/` and `frontend/`

The newer `backend/` tree is the clearest place to understand the intended long-term architecture, but some top-level modules still reflect an earlier implementation. If you are continuing development, it is worth treating this as a project in transition rather than a fully consolidated codebase.

## Main areas

### 1. Agent and tools

The assistant logic is implemented in Python and centers around:

- `backend/brain/agent.py` for the LangGraph agent flow
- `backend/brain/llm.py` for model/provider setup
- `backend/brain/memory.py` for memory retrieval and storage
- `backend/tools/` for file, system, app, browser, code, and reminder actions

The agent is designed to:

- load relevant memory
- send the conversation to the model
- let the model choose tools
- run the selected tools
- save the interaction back to memory

### 2. Backend API

The backend uses FastAPI and lives in `backend/api/`.

Important files:

- `backend/run.py` starts the backend server
- `backend/api/main.py` creates the FastAPI app
- `backend/api/routes/` contains chat, tools, and system routes

The API structure is present, but some routes are still stubbed or mid-implementation. For example, the chat route does not yet fully pass requests through the LangGraph agent.

### 3. Frontend

The Flutter app lives in `frontend/`.

Important files:

- `frontend/lib/main.dart` is the app entry point
- `frontend/lib/screens/` contains the main UI screens
- `frontend/lib/services/` contains API, auth, and storage services
- `frontend/lib/providers/` manages app state

This part of the repo appears to be intended as the modern user interface for the assistant.

### 4. Legacy desktop app

There is also a desktop-first Python UI flow:

- `run.py` launches the desktop app
- `desktop/` contains the desktop UI
- `agent/`, `actions/`, and `database/` support that older flow

This looks like an earlier implementation that still coexists with the newer backend/frontend layout.

## Folder overview

```text
my-agent/
|-- README.md
|-- run.py                    # Starts the older desktop app
|-- requirements.txt          # Root Python dependencies
|-- backend/                  # Newer FastAPI + LangGraph backend
|-- frontend/                 # Flutter frontend
|-- desktop/                  # Older desktop UI
|-- agent/                    # Older agent logic
|-- actions/                  # Older PC action modules
|-- server/                   # Older FastAPI-style server
|-- database/                 # Older database layer
|-- docs/                     # Project documentation
|-- tests/                    # Top-level tests
|-- logs/                     # Root logs
|-- mobile/                   # Mobile/web-related Python app pieces
```

## Tech stack

Based on the current code and dependency files:

- Python
- FastAPI
- LangGraph
- LangChain
- Groq
- Pinecone
- Supabase
- Upstash Redis
- Flutter
- psutil
- pyautogui

## Key capabilities in the codebase

The repository includes modules for:

- file and folder operations
- system information and process inspection
- app launching and window-related actions
- Python code writing and execution
- browser/web helpers
- reminders and scheduling
- memory-backed chat flows

## Quick start

### Option A: Run the older desktop app

Install root dependencies:

```bash
pip install -r requirements.txt
```

Configure `.env` with the keys required by your setup, then run:

```bash
python run.py
```

Note: this path depends on the older desktop-first structure.

### Option B: Run the newer backend

Install backend dependencies:

```bash
cd backend
pip install -r requirements.txt
```

Add your environment variables in `backend/.env`, then run:

```bash
python run.py
```

When the backend starts, the API is expected at:

- `http://localhost:8000`
- `http://localhost:8000/docs`

## Environment variables

The exact set depends on which flow you use, but the project references keys such as:

- `GROQ_API_KEY`
- `PINECONE_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `UPSTASH_REDIS_URL`
- `UPSTASH_REDIS_TOKEN`
- `OPENROUTER_API_KEY`

You may also need local configuration for Ollama if you plan to use offline fallback behavior.

## Development notes

- The repo currently mixes old and new architecture.
- Some documentation files still describe the older structure.
- There are duplicate concepts across `agent/` and `backend/brain/`, and across `server/` and `backend/api/`.
- Before adding major features, it would be smart to decide which architecture is the source of truth.

## Suggested next cleanup steps

- Align the README, docs, and actual code paths
- Choose either the legacy or newer architecture as the primary implementation
- Remove or archive duplicate modules once the preferred structure is confirmed
- Verify which tests still reflect current behavior

## Useful entry points

- `run.py`
- `backend/run.py`
- `backend/api/main.py`
- `backend/brain/agent.py`
- `frontend/lib/main.dart`
- `docs/architecture.md`
- `docs/setup.md`
