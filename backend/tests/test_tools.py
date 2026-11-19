import os

from tools.base_tool import DANGEROUS_TOOLS, execute_tool_call, precheck_tool_call


def test_precheck_blocks_protected_system_paths():
    result = precheck_tool_call(
        "tool_delete_file",
        {"filepath": r"C:\Windows\System32\drivers\etc\hosts"},
    )

    assert result is not None
    assert result["success"] is False
    assert "Blocked for safety" in result["message"]


def test_safe_tools_retry_before_failing_or_succeeding():
    attempts = {"count": 0}

    def flaky_search():
        attempts["count"] += 1
        if attempts["count"] < 3:
            return "Error: temporary network issue"
        return "Search results are ready"

    result = execute_tool_call(
        "tool_search_web",
        {"query": "ai"},
        flaky_search,
    )

    assert attempts["count"] == 3
    assert result == "Search results are ready"


def test_dangerous_tools_do_not_auto_retry():
    attempts = {"count": 0}

    def failing_install():
        attempts["count"] += 1
        return "Error: install failed"

    result = execute_tool_call(
        "tool_install_package",
        {"package_name": "demo-package"},
        failing_install,
    )

    assert attempts["count"] == 1
    assert isinstance(result, dict)
    assert result["success"] is False
    assert result["data"]["attempts"] == 1


def test_wrapper_verifies_file_results():
    missing_path = os.path.join(
        os.path.expanduser("~"),
        "Documents",
        "codex_missing_verification_test.txt",
    )

    result = execute_tool_call(
        "tool_create_file",
        {"filename": missing_path},
        lambda: {
            "success": True,
            "action": "create_file",
            "message": "File created successfully.",
            "data": {"path": missing_path},
        },
    )

    assert isinstance(result, dict)
    assert result["success"] is False
    assert "Verification failed" in result["message"]


def test_dangerous_tool_registry_matches_expected_tools():
    assert {
        "tool_delete_file",
        "tool_shutdown",
        "tool_restart",
        "tool_kill_process",
        "tool_install_package",
    }.issubset(DANGEROUS_TOOLS)
