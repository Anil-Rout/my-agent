from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Callable


DESKTOP = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")
DOCUMENTS = os.path.join(os.path.expanduser("~"), "Documents")
DOWNLOADS = os.path.join(os.path.expanduser("~"), "Downloads")
PICTURES = os.path.join(os.path.expanduser("~"), "Pictures")
VIDEOS = os.path.join(os.path.expanduser("~"), "Videos")
MUSIC = os.path.join(os.path.expanduser("~"), "Music")
ONEDRIVE = os.path.join(os.path.expanduser("~"), "OneDrive")
HOME = os.path.expanduser("~")

SAFE_ROOTS = [
    os.path.abspath(path)
    for path in [DESKTOP, DOCUMENTS, DOWNLOADS, PICTURES, VIDEOS, MUSIC, ONEDRIVE, HOME]
]

BLOCKED_ROOTS = [
    os.path.abspath(path)
    for path in [
        r"C:\Windows",
        r"C:\Program Files",
        r"C:\Program Files (x86)",
        r"C:\ProgramData",
        os.path.join(HOME, "AppData"),
        os.path.join(HOME, ".ssh"),
    ]
]


@dataclass(frozen=True)
class ToolPolicy:
    retryable: bool = False
    retry_attempts: int = 0
    retry_delay_seconds: float = 0.0
    requires_confirmation: bool = False
    verify_result: bool = True
    path_args: tuple[str, ...] = ()
    restrict_to_safe_roots: bool = False


DEFAULT_POLICY = ToolPolicy()


TOOL_POLICIES: dict[str, ToolPolicy] = {
    "tool_create_folder": ToolPolicy(
        retryable=True,
        retry_attempts=2,
        retry_delay_seconds=0.1,
        path_args=("folder_name",),
        restrict_to_safe_roots=True,
    ),
    "tool_create_file": ToolPolicy(
        retryable=True,
        retry_attempts=2,
        retry_delay_seconds=0.1,
        path_args=("filename", "filepath", "path"),
        restrict_to_safe_roots=True,
    ),
    "tool_read_file": ToolPolicy(
        retryable=True,
        retry_attempts=1,
        retry_delay_seconds=0.1,
        path_args=("filepath", "filename", "path"),
        restrict_to_safe_roots=True,
    ),
    "tool_delete_file": ToolPolicy(
        requires_confirmation=True,
        path_args=("filepath", "filename", "path"),
        restrict_to_safe_roots=True,
    ),
    "tool_open_folder": ToolPolicy(
        retryable=True,
        retry_attempts=1,
        retry_delay_seconds=0.1,
        path_args=("folder_path", "path"),
        restrict_to_safe_roots=True,
    ),
    "tool_write_code": ToolPolicy(
        retryable=True,
        retry_attempts=1,
        retry_delay_seconds=0.1,
        path_args=("filename", "folder_path", "path"),
        restrict_to_safe_roots=True,
    ),
    "tool_write_and_run": ToolPolicy(
        path_args=("filename", "folder_path", "path"),
        restrict_to_safe_roots=True,
    ),
    "tool_run_file": ToolPolicy(
        path_args=("path", "filepath", "filename"),
        restrict_to_safe_roots=True,
    ),
    "tool_kill_process": ToolPolicy(requires_confirmation=True),
    "tool_shutdown": ToolPolicy(requires_confirmation=True),
    "tool_restart": ToolPolicy(requires_confirmation=True),
    "tool_install_package": ToolPolicy(requires_confirmation=True),
    "tool_search_web": ToolPolicy(
        retryable=True,
        retry_attempts=2,
        retry_delay_seconds=0.2,
    ),
    "tool_get_weather": ToolPolicy(
        retryable=True,
        retry_attempts=2,
        retry_delay_seconds=0.2,
    ),
    "tool_get_news": ToolPolicy(
        retryable=True,
        retry_attempts=2,
        retry_delay_seconds=0.2,
    ),
    "tool_search_google": ToolPolicy(
        retryable=True,
        retry_attempts=1,
        retry_delay_seconds=0.1,
    ),
    "tool_search_youtube": ToolPolicy(
        retryable=True,
        retry_attempts=1,
        retry_delay_seconds=0.1,
    ),
    "tool_open_website": ToolPolicy(
        retryable=True,
        retry_attempts=1,
        retry_delay_seconds=0.1,
    ),
    "tool_find_folder": ToolPolicy(
        retryable=True,
        retry_attempts=1,
        retry_delay_seconds=0.1,
        path_args=("folder_path", "path"),
        restrict_to_safe_roots=True,
    ),
}


DANGEROUS_TOOLS = {
    tool_name
    for tool_name, policy in TOOL_POLICIES.items()
    if policy.requires_confirmation
}


def get_tool_policy(tool_name: str) -> ToolPolicy:
    return TOOL_POLICIES.get(tool_name, DEFAULT_POLICY)


def make_tool_result(action: str, success: bool, message: str, data: dict | None = None) -> dict:
    return {
        "success": success,
        "action": action,
        "message": message,
        "data": data or {},
    }


def _action_name(tool_name: str) -> str:
    return tool_name.removeprefix("tool_")


def _normalize_path(path: str) -> str:
    return os.path.abspath(os.path.expandvars(os.path.expanduser(path.strip().strip('"').strip("'"))))


def _is_relative_token(path_value: str) -> bool:
    cleaned = path_value.strip().strip('"').strip("'")
    if not cleaned:
        return True
    return not os.path.isabs(os.path.expandvars(os.path.expanduser(cleaned)))


def _path_is_under(path: str, root: str) -> bool:
    try:
        return os.path.commonpath([path, root]) == root
    except ValueError:
        return False


def is_blocked_path(path_value: str, restrict_to_safe_roots: bool) -> bool:
    normalized = _normalize_path(path_value)

    for blocked_root in BLOCKED_ROOTS:
        if _path_is_under(normalized, blocked_root):
            return True

    if not restrict_to_safe_roots:
        return False

    return not any(_path_is_under(normalized, safe_root) for safe_root in SAFE_ROOTS)


def precheck_tool_call(tool_name: str, tool_args: dict | None) -> dict | None:
    policy = get_tool_policy(tool_name)
    tool_args = tool_args or {}

    for arg_name in policy.path_args:
        raw_value = tool_args.get(arg_name)
        if not isinstance(raw_value, str) or not raw_value.strip():
            continue

        if _is_relative_token(raw_value):
            continue

        if is_blocked_path(raw_value, policy.restrict_to_safe_roots):
            return make_tool_result(
                action=_action_name(tool_name),
                success=False,
                message=(
                    "Blocked for safety: that path is outside the allowed workspace "
                    "or points to a protected system location."
                ),
                data={"path": raw_value, "argument": arg_name},
            )

    return None


def tool_succeeded(tool_result: Any) -> bool:
    if isinstance(tool_result, dict):
        return bool(tool_result.get("success", False))

    if tool_result is None:
        return False

    if not isinstance(tool_result, str):
        return True

    cleaned = tool_result.strip().lower()
    if not cleaned:
        return False

    failure_prefixes = (
        "error",
        "tool error",
        "failed",
        "timed out",
        "code timed out",
        "file not found",
        "folder not found",
        "❌",
    )
    return not cleaned.startswith(failure_prefixes)


def _verify_dict_result(tool_name: str, tool_result: dict) -> tuple[bool, str | None]:
    if not tool_result.get("success", False):
        return False, tool_result.get("message") or "Tool reported failure."

    action = tool_result.get("action", "")
    data = tool_result.get("data", {}) or {}

    if action in {"create_folder", "open_folder"}:
        path = data.get("path")
        if path and not os.path.isdir(path):
            return False, f"Verification failed: folder was not found at {path}"

    if action in {"create_file", "write_code", "write_and_run_code"}:
        path = data.get("path")
        if path and not os.path.isfile(path):
            return False, f"Verification failed: file was not found at {path}"

    if action == "delete_file":
        path = data.get("filepath") or data.get("path")
        if path and os.path.exists(path):
            return False, f"Verification failed: target still exists at {path}"

    if action == "read_file":
        path = data.get("filepath") or data.get("path")
        if path and not os.path.exists(path):
            return False, f"Verification failed: file was not found at {path}"

    if tool_name == "tool_run_file":
        path = data.get("path")
        if path and not os.path.isfile(path):
            return False, f"Verification failed: script file was not found at {path}"

    return True, None


def verify_tool_result(tool_name: str, tool_result: Any) -> tuple[bool, str | None]:
    if isinstance(tool_result, dict):
        return _verify_dict_result(tool_name, tool_result)

    if tool_succeeded(tool_result):
        return True, None

    if isinstance(tool_result, str):
        return False, tool_result

    return False, "Tool returned an invalid result."


def _with_execution_meta(tool_result: Any, attempts: int, verified: bool) -> Any:
    if not isinstance(tool_result, dict):
        return tool_result

    data = dict(tool_result.get("data", {}) or {})
    data.setdefault("attempts", attempts)
    data.setdefault("verified", verified)
    enriched = dict(tool_result)
    enriched["data"] = data
    return enriched


def execute_tool_call(
    tool_name: str,
    tool_args: dict | None,
    invoker: Callable[[], Any],
) -> Any:
    policy = get_tool_policy(tool_name)
    tool_args = tool_args or {}

    precheck_result = precheck_tool_call(tool_name, tool_args)
    if precheck_result is not None:
        return _with_execution_meta(precheck_result, attempts=0, verified=False)

    max_attempts = 1 + (policy.retry_attempts if policy.retryable else 0)
    last_result: Any = None

    for attempt in range(1, max_attempts + 1):
        try:
            raw_result = invoker()
        except Exception as exc:
            raw_result = make_tool_result(
                action=_action_name(tool_name),
                success=False,
                message=f"Tool raised an exception: {exc}",
                data={"error_type": type(exc).__name__},
            )

        if not policy.verify_result:
            return _with_execution_meta(raw_result, attempts=attempt, verified=False)

        verified, verification_message = verify_tool_result(tool_name, raw_result)
        if verified:
            return _with_execution_meta(raw_result, attempts=attempt, verified=True)

        if isinstance(raw_result, dict):
            raw_result = dict(raw_result)
            raw_result["success"] = False
            message = raw_result.get("message") or ""
            if verification_message and verification_message not in message:
                raw_result["message"] = (
                    f"{message} | {verification_message}" if message else verification_message
                )
        else:
            raw_result = make_tool_result(
                action=_action_name(tool_name),
                success=False,
                message=verification_message or str(raw_result),
                data={},
            )

        last_result = raw_result

        if attempt < max_attempts and policy.retryable:
            if policy.retry_delay_seconds > 0:
                time.sleep(policy.retry_delay_seconds)
            continue

    return _with_execution_meta(
        last_result
        or make_tool_result(
            action=_action_name(tool_name),
            success=False,
            message="Tool failed without returning a result.",
            data={},
        ),
        attempts=max_attempts,
        verified=False,
    )


def format_tool_result(tool_result: Any) -> str:
    if isinstance(tool_result, dict):
        action = tool_result.get("action", "")
        message = tool_result.get("message", "")
        data = tool_result.get("data", {}) or {}

        if action == "read_file" and data.get("content"):
            return f"{message}\n\n{data['content']}"

        if action == "get_system_summary" and data.get("summary"):
            return data["summary"]

        if action in {"create_folder", "create_file", "delete_file", "open_application", "open_folder"}:
            return message

        if action == "write_code":
            return message

        if action == "write_and_run_code":
            output = data.get("output")
            error = data.get("error")
            if output:
                return f"{message}\n\nOutput:\n{output}"
            if error:
                return f"{message}\n\nError:\n{error}"
            return message

        return message or str(tool_result)

    return str(tool_result)
