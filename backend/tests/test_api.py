import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.rate_limit import reset_rate_limits
from api.routes import chat as chat_route
from database.connection import SessionLocal, init_database
from database.models import Message, SessionRecord, TaskRecord


init_database()
client = TestClient(app)


def _clear_chat_tables():
    db = SessionLocal()
    try:
        db.query(Message).delete()
        db.query(TaskRecord).delete()
        db.query(SessionRecord).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture
def auth_headers(monkeypatch):
    reset_rate_limits()
    monkeypatch.setenv("AGENT_PASSWORD", "test-password")
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("JWT_EXPIRE_MINUTES", "60")

    response = client.post("/auth/login", json={"password": "test-password"})

    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]

    data = response.json()
    assert data["status"] == "Agent is running"
    assert data["version"] == "1.0.0"


def test_login_success(monkeypatch):
    reset_rate_limits()
    monkeypatch.setenv("AGENT_PASSWORD", "test-password")
    monkeypatch.setenv("SECRET_KEY", "test-secret")

    response = client.post("/auth/login", json={"password": "test-password"})

    assert response.status_code == 200

    data = response.json()
    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)
    assert data["access_token"]
    assert data["expires_in"] > 0
    assert response.headers["X-Request-ID"]


def test_login_rejects_invalid_password(monkeypatch):
    reset_rate_limits()
    monkeypatch.setenv("AGENT_PASSWORD", "test-password")
    monkeypatch.setenv("SECRET_KEY", "test-secret")

    response = client.post("/auth/login", json={"password": "wrong-password"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid password."
    assert response.json()["success"] is False


def test_protected_route_requires_auth():
    response = client.get("/tools/list")

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing bearer token."


def test_tools_list(auth_headers):
    response = client.get("/tools/list", headers=auth_headers)

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

    first_tool = data[0]
    assert "name" in first_tool
    assert "description" in first_tool


def test_tools_capabilities(auth_headers):
    response = client.get("/tools/capabilities", headers=auth_headers)

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "category" in data[0]
    assert "features" in data[0]


def test_system_info(auth_headers):
    response = client.get("/system/info", headers=auth_headers)

    assert response.status_code == 200

    data = response.json()
    assert "success" in data
    assert "summary" in data
    assert "message" in data


def test_system_activity(auth_headers):
    response = client.get("/system/activity", headers=auth_headers)

    assert response.status_code == 200

    data = response.json()
    assert "activity" in data
    assert isinstance(data["activity"], list)


def test_chat(auth_headers, monkeypatch):
    _clear_chat_tables()
    monkeypatch.setattr(
        chat_route,
        "run_agent_chat",
        lambda message, history, agent_name, session_id="default": (
            "hello from agent",
            agent_name or "ARIA",
        ),
    )
    monkeypatch.setattr(
        chat_route,
        "search_memory",
        lambda message, top_k=5: [{"text": "memory"}],
    )

    response = client.post("/chat/", json={"message": "hello"}, headers=auth_headers)

    assert response.status_code == 200

    data = response.json()
    assert data["response"] == "hello from agent"
    assert data["memories_used"] == 1
    assert isinstance(data["agent_name"], str)


def test_chat_with_history(auth_headers, monkeypatch):
    _clear_chat_tables()

    def fake_run_agent_chat(message, history, agent_name, session_id="default"):
        assert len(history) == 2
        return "history ok", agent_name or "ARIA"

    monkeypatch.setattr(chat_route, "run_agent_chat", fake_run_agent_chat)
    monkeypatch.setattr(chat_route, "search_memory", lambda message, top_k=5: [])

    response = client.post(
        "/chat/",
        json={
            "message": "hello again",
            "history": [
                {"role": "user", "content": "hello"},
                {"role": "assistant", "content": "Hi, how can I help you?"},
            ],
        },
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()
    assert data["response"] == "history ok"
    assert data["memories_used"] == 0


def test_chat_passes_session_id(auth_headers, monkeypatch):
    _clear_chat_tables()

    def fake_run_agent_chat(message, history, agent_name, session_id="default"):
        assert session_id == "session-123"
        return "session ok", agent_name or "ARIA"

    monkeypatch.setattr(chat_route, "run_agent_chat", fake_run_agent_chat)
    monkeypatch.setattr(chat_route, "search_memory", lambda message, top_k=5: [])

    response = client.post(
        "/chat/",
        json={"message": "hello", "session_id": "session-123"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["response"] == "session ok"


def test_chat_with_invalid_history_role(auth_headers):
    response = client.post(
        "/chat/",
        json={
            "message": "hello",
            "history": [
                {"role": "banana", "content": "test"},
            ],
        },
        headers=auth_headers,
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Request validation failed."


def test_chat_hides_internal_errors(auth_headers, monkeypatch):
    _clear_chat_tables()

    def boom(*args, **kwargs):
        raise RuntimeError("provider exploded")

    monkeypatch.setattr(chat_route, "run_agent_chat", boom)

    response = client.post("/chat/", json={"message": "hello"}, headers=auth_headers)

    assert response.status_code == 500
    assert response.json()["detail"] == (
        "Agent execution failed. Please try again in a moment."
    )


def test_chat_persists_history_tasks_and_sessions(auth_headers, monkeypatch):
    _clear_chat_tables()
    monkeypatch.setattr(
        chat_route,
        "run_agent_chat",
        lambda message, history, agent_name, session_id="default": (
            "saved reply",
            agent_name or "ARIA",
        ),
    )
    monkeypatch.setattr(chat_route, "search_memory", lambda message, top_k=5: [])

    response = client.post(
        "/chat/",
        json={"message": "save this", "session_id": "persist-1"},
        headers=auth_headers,
    )

    assert response.status_code == 200

    history_response = client.get(
        "/chat/history",
        params={"session_id": "persist-1"},
        headers=auth_headers,
    )
    assert history_response.status_code == 200
    history_data = history_response.json()
    assert history_data["count"] == 2
    assert history_data["history"][0]["role"] == "user"
    assert history_data["history"][1]["role"] == "assistant"

    tasks_response = client.get(
        "/chat/tasks",
        params={"session_id": "persist-1"},
        headers=auth_headers,
    )
    assert tasks_response.status_code == 200
    task = tasks_response.json()["tasks"][0]
    assert task["status"] == "completed"
    assert task["input_text"] == "save this"

    sessions_response = client.get("/chat/sessions", headers=auth_headers)
    assert sessions_response.status_code == 200
    session = sessions_response.json()["sessions"][0]
    assert session["session_id"] == "persist-1"
    assert session["status"] == "active"


def test_login_rate_limit(monkeypatch):
    reset_rate_limits()
    monkeypatch.setenv("AGENT_PASSWORD", "test-password")
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("RATE_LIMIT_AUTH_PER_MINUTE", "1")

    first = client.post("/auth/login", json={"password": "test-password"})
    second = client.post("/auth/login", json={"password": "test-password"})

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json()["detail"] == "Rate limit exceeded. Please wait and try again."
    assert second.headers["Retry-After"]
