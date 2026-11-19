# Usage Guide

This guide explains how to use the project as it exists today, not just as it is planned to work later.

The repository currently has two usage paths:

- a newer backend-oriented path under `backend/`
- a legacy desktop-first path from the repo root

For ongoing development, the backend path is the better reference point. The API is now connected to the real agent flow, but it still depends on correct environment setup and provider availability.

## Recommended usage path

If you are actively building on the project, use:

- `backend/` for API and agent work
- `frontend/` for Flutter UI work

If you are exploring the older implementation, use:

- `run.py`
- `desktop/`
- `agent/`
- `actions/`

## 1. Start the backend

From the `backend/` directory:

```bash
python run.py
```

If startup succeeds, the API should be available at:

- `http://localhost:8000`
- `http://localhost:8000/docs`

## 2. Use the current API

### Health check

Request:

```http
GET /
```

Expected response:

```json
{"status":"Agent is running","version":"1.0.0"}
```

### Chat endpoint

Request:

```http
POST /chat/
Content-Type: application/json
```

Body:

```json
{"message":"Hello agent"}
```

Current response shape:

```json
{
  "response": "Hello! How can I help you today?",
  "memories_used": 3,
  "agent_name": "ARIA"
}
```

Important note:

- the API route now calls the real agent in `backend/brain/agent.py`
- the agent loads relevant memory before generating a response
- the response may include tool-driven behavior depending on your provider setup

This means the chat API is now much closer to the intended assistant experience than the earlier placeholder implementation.

### System info endpoint

Request:

```http
GET /system/info
```

This returns a JSON object containing system summary text from the backend system tool layer.

### Tools endpoint

Request:

```http
GET /tools/list
```

This returns the currently registered agent tools, including each tool name and description.

## 3. Test the API from the command line

### PowerShell example

```powershell
Invoke-RestMethod -Method Get -Uri http://localhost:8000/
```

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://localhost:8000/chat/ `
  -ContentType "application/json" `
  -Body '{"message":"Open calculator"}'
```

### cURL example

```bash
curl http://localhost:8000/
```

```bash
curl -X POST http://localhost:8000/chat/ \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"What is my system status?\"}"
```

## 4. Use the LangGraph agent directly

The full tool-calling agent logic currently lives in `backend/brain/agent.py`.

If you want to exercise the agent logic directly from Python, use this from inside `backend/`:

```python
from brain.agent import chat

response, agent_name = chat("Open calculator")
print(response)
print(agent_name)
```

This path is closer to the intended assistant behavior because it:

- loads memory
- invokes the configured model
- allows tool selection
- runs tool calls
- saves the interaction back to memory

## 5. Example prompts the agent is designed to handle

Based on the registered tools in `backend/brain/agent.py`, the assistant is designed for prompts like:

- "Create a folder named Projects"
- "Read the file at this path"
- "Show my CPU and RAM usage"
- "Open Notepad"
- "Take a screenshot"
- "Search the web for LangGraph tutorials"
- "What is the weather in Chennai?"
- "Set a reminder for 7:30 PM"
- "Run this Python code"
- "Install pandas"

Whether each prompt works in practice depends on:

- your environment variables
- provider availability
- Windows environment behavior
- whether you are using the direct agent path or the FastAPI route

## 6. Legacy desktop usage

The root launcher starts the older desktop-first version:

```bash
python run.py
```

This path uses the legacy modules under:

- `desktop/`
- `agent/`
- `actions/`
- `database/`

Use this path only if you are intentionally working with the older desktop UI flow.

## 7. Current limitations

The most important limitations to know before testing are:

- the repo contains both old and new architecture at the same time
- some docs and app flows are still being aligned
- the agent depends on external services and local environment configuration
- some backend and frontend integration pieces are still minimal

## 8. Best way to work right now

For the smoothest development workflow:

- use `backend/` as the main backend codebase
- use either the API route or direct agent testing for the tool-calling flow
- verify environment variables before debugging agent behavior
- update frontend integrations against the current response shape

## 9. Suggested next improvements

- connect the Flutter app to the finalized backend API
- remove or archive the duplicate legacy paths once the newer flow is stable
- add tests for the new chat and tools routes
