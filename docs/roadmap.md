# Backend Roadmap

This roadmap turns the current backend assessment into a concrete implementation plan for the `backend/` architecture that already exists in the repo.

The goal is not to redesign the whole project from scratch. The goal is to harden the current FastAPI plus agent stack so it can safely support persistent chat, approvals, multi-step tasks, and private remote PC control.

## What exists today

The current backend already has the right major layers:

- API entrypoint and route groups in `backend/api/main.py` and `backend/api/routes/`
- JWT bearer auth in `backend/api/auth.py`
- Protected chat and tool discovery routes in `backend/api/routes/chat.py` and `backend/api/routes/tools.py`
- A tool-using agent in `backend/brain/agent.py`
- Provider fallback in `backend/brain/llm.py`
- Semantic memory in `backend/brain/memory.py`
- Central tool policy and verification helpers in `backend/tools/base_tool.py`
- Basic persistence for messages, action logs, and key-value state in `backend/database/models.py` and `backend/database/queries.py`

That is a strong starting point. The repo already has the shape we want. What is missing is durable orchestration, stronger identity and approval handling, and tighter control over tool execution.

## Current gaps

### API and auth

- Auth is still a single password from environment variables.
- JWTs only identify `sub=local-owner`; there is no real `User` record.
- CORS is fully open in `backend/api/main.py`.
- Requests do not consistently carry `user_id`, `device_id`, or `request_id`.
- There is no dedicated API for task status, approvals, or audit queries.

### Agent execution

- The agent is mostly single-turn even though it has some helper logic for direct actions and confirmation prompts.
- `backend/brain/agent.py` mixes routing, planning, tool execution, confirmation state, and session context in one module.
- `PENDING_CONFIRMATIONS` and `SESSION_CONTEXTS` are in-memory only.
- There is no durable `Task -> Step -> Action -> Retry -> Fallback` execution model.

### Tools and safety

- `backend/tools/base_tool.py` is the correct enforcement point, but not every dangerous behavior is modeled explicitly.
- The policy object does not yet capture risk level, timeout, or execution isolation.
- Confirmation exists as a prompt flow, but not as a persistent approval queue.
- Code execution still runs in the main backend context instead of a sandboxed worker.

### Persistence and recoverability

- SQL models currently cover `Message`, `ActionLog`, and `AgentState`, but not sessions, tasks, steps, or approvals.
- The database is not yet the source of truth for active agent execution.
- Memory retrieval exists, but it is not tied to durable session state or resumable task progress.

### Security and remote control

- There is no role model, device model, or multi-user support.
- CORS and auth are permissive for a prototype, not for a remote-control product.
- Remote access guidance exists in [docs/remote_access.md](remote_access.md), but the backend does not yet expose connection status, audit history, or approval APIs that a remote client should rely on.

## Target architecture

These are the principles the next implementation phases should follow:

1. The backend is the source of truth for identity, session state, task state, approvals, and audit logs.
2. Semantic memory stays in Pinecone, but durable execution state lives in SQL.
3. Every tool call goes through a single policy layer before execution.
4. Destructive or high-risk actions require persistent approval records, not just in-memory prompts.
5. Multi-step work is modeled as tasks and steps, not as one large chat response.
6. Remote access stays private-first, with Tailscale or another trusted network in front of the home PC backend.

## Phased roadmap

### Phase 1: Solidify the backend foundation

Outcome: move from a prototype chat API to a backend that can track identity, task state, and confirmations safely.

- Add SQL models for `User`, `Session`, `Task`, `TaskStep`, and `Approval`.
- Replace environment-only password auth with hashed user-backed auth.
- Extend chat requests to carry request metadata and persist it.
- Refactor chat handling so each request creates or updates a durable task record.
- Move confirmation state out of `PENDING_CONFIRMATIONS` and into the database.
- Expand tool policies so every tool has explicit safety metadata.
- Tighten CORS and require auth on all non-health endpoints.
- Add tests for auth, task creation, approval flow, and session isolation.

### Phase 2: Make execution reliable

Outcome: support longer-running and recoverable agent workflows.

- Split planning from execution in `backend/brain/agent.py`.
- Introduce a local executor or queue for multi-step tasks.
- Store step-by-step progress, retries, and failures in SQL.
- Add polling or streaming endpoints for task progress.
- Limit automatic retries to low-risk tools only.
- Summarize prior history for prompts while keeping full history in durable storage.

### Phase 3: Support safe remote PC control

Outcome: make the backend dependable when accessed from phone or another machine.

- Add backend status and heartbeat endpoints for remote clients.
- Add a backend config surface for trusted remote URL and instance metadata.
- Expose task status and approvals in a way the Flutter client can consume directly.
- Document the home-PC service model and recommend Tailscale as the default private network path.

### Phase 4: Harden safety and operations

Outcome: reduce blast radius and improve accountability.

- Add audit log query APIs.
- Add approval management endpoints for pending, approved, denied, and expired actions.
- Move code execution into a separate worker process or sandbox.
- Add roles or permission scopes for admin versus normal clients.
- Add more restrictive path and filesystem policies for destructive tools.
- Improve observability around provider failures, tool failures, and task recovery.

## Exact Phase 1 implementation backlog

This is the recommended order for the first real implementation sprint.

### 1. Expand the data model first

Files to start with:

- `backend/database/models.py`
- `backend/database/queries.py`
- `backend/database/connection.py`

Add:

- `User`
- `Session`
- `Task`
- `TaskStep`
- `Approval`

Minimum fields to include:

- `User`: `id`, `username`, `password_hash`, `is_active`, `created_at`
- `Session`: `id`, `user_id`, `device_id`, `status`, `last_seen_at`
- `Task`: `id`, `session_id`, `user_id`, `request_id`, `kind`, `status`, `input_text`, `result_text`, `error_text`, `created_at`, `updated_at`
- `TaskStep`: `id`, `task_id`, `step_index`, `kind`, `status`, `tool_name`, `input_json`, `output_json`, `error_text`, `attempt_count`
- `Approval`: `id`, `task_id`, `session_id`, `tool_name`, `tool_args_json`, `reason`, `status`, `requested_at`, `resolved_at`, `resolved_by`

Definition of done:

- queries exist to create and update each new record type
- chat and approval flows can stop depending on process memory for critical state

### 2. Replace prototype auth with user-backed auth

Files to start with:

- `backend/api/auth.py`
- `backend/api/routes/auth.py`
- `backend/database/models.py`
- `backend/tests/test_api.py`

Implement:

- hashed password verification
- default local owner bootstrap path
- JWT subject mapped to a real `User.id` or username
- helper to load the current user record instead of returning only a string

Definition of done:

- login validates against stored user data
- protected routes can derive `user_id` from the token
- tests cover success, failure, and invalid token cases

### 3. Standardize request context

Files to start with:

- `backend/api/routes/chat.py`
- `backend/api/auth.py`
- `backend/database/queries.py`

Add these fields to the chat contract:

- `session_id`
- `device_id`
- `request_id`

Behavior:

- `user_id` comes from JWT, not the request body
- every chat request persists enough metadata to trace who asked, from which device, in which session, and under which request id

Definition of done:

- every task and audit entry can be traced back to a user and request

### 4. Refactor chat into task creation plus execution tracking

Files to start with:

- `backend/api/routes/chat.py`
- `backend/brain/agent.py`
- `backend/database/queries.py`

Implement:

- create a `Task` row for every chat request
- create `TaskStep` rows for planner decisions and tool actions
- return task metadata in the API response
- keep synchronous execution initially if that is simpler, but persist the task lifecycle anyway

Definition of done:

- chat is no longer just "call agent and return text"
- failures and partial work are visible in task records

### 5. Replace in-memory confirmations with durable approvals

Files to start with:

- `backend/brain/agent.py`
- `backend/tools/base_tool.py`
- `backend/api/routes/tools.py` or a new approvals route module
- `backend/database/queries.py`

Implement:

- when a dangerous tool is selected, create an `Approval` record instead of only writing to `PENDING_CONFIRMATIONS`
- add API endpoints to list pending approvals and approve or deny them
- tie approval decisions back to the originating task and session

Definition of done:

- approval survives backend restarts
- remote clients can review and confirm actions explicitly

### 6. Tighten central tool policy coverage

Files to start with:

- `backend/tools/base_tool.py`
- `backend/brain/agent.py`

Add to `ToolPolicy`:

- `risk_level`
- `timeout_seconds`
- `requires_confirmation`
- `restrict_to_safe_roots`
- optional execution mode such as `inline` or `worker`

Implementation notes:

- all tool execution paths should pass through `execute_tool_call`
- direct helper shortcuts in `agent.py` should still use the same policy wrapper

Definition of done:

- no tool bypasses the central policy layer
- policy decisions are auditable and predictable

### 7. Lock down runtime configuration

Files to start with:

- `backend/api/main.py`
- `backend/config/settings.py`

Implement:

- environment-driven allowed origins instead of `["*"]`
- explicit production defaults for auth and CORS
- clearer startup validation for required secrets

Definition of done:

- local development still works
- production settings are no longer permissive by default

### 8. Add the missing tests before Phase 2

Files to start with:

- `backend/tests/test_api.py`
- `backend/tests/test_tools.py`
- new tests for task and approval behavior

Required coverage:

- login with stored user credentials
- protected routes reject missing or invalid bearer tokens
- session isolation across different `session_id` values
- dangerous tool calls create approvals instead of executing immediately
- blocked path policy still prevents unsafe file targets
- task status persists across agent execution errors

## Suggested first PR split

To keep the first phase manageable, use this PR order:

1. Database schema and query helpers for users, sessions, tasks, steps, and approvals
2. Auth refactor to user-backed login and request user loading
3. Chat route persistence changes with task creation and request metadata
4. Durable approval flow and approval endpoints
5. Tool policy expansion and config hardening
6. Test sweep covering the new lifecycle

## Files that should drive the next implementation work

Start in these files first:

- `backend/api/routes/chat.py`
- `backend/api/auth.py`
- `backend/brain/agent.py`
- `backend/tools/base_tool.py`
- `backend/database/models.py`
- `backend/database/queries.py`

Those files already hold the main execution path. Strengthening them will unlock the rest of the roadmap without forcing a large rewrite.
