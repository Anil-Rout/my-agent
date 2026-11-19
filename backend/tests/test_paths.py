from config import paths


def test_resolve_relative_sqlite_url_uses_backend_directory():
    url = paths.resolve_sqlite_url("sqlite:///database/agent.db")

    assert url.startswith("sqlite:///")
    assert url.replace("\\", "/").endswith("/backend/database/agent.db")


def test_resolve_absolute_sqlite_url_is_unchanged():
    raw = "sqlite:///C:/temp/agent.db"

    assert paths.resolve_sqlite_url(raw) == raw


def test_runtime_log_paths_are_under_backend_logs():
    assert paths.ACTIVITY_LOG_PATH.parent == paths.LOGS_DIR
    assert paths.TOOL_ACTIVITY_LOG_PATH.parent == paths.LOGS_DIR
