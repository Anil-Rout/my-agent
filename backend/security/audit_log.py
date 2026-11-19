import re
from collections import Counter

from config.paths import TOOL_ACTIVITY_LOG_PATH

LOG_PATH = TOOL_ACTIVITY_LOG_PATH


SESSION_RE = re.compile(r"\[session=(.*?)\]")
TOOL_RE = re.compile(r"\[tool=(.*?)\]")
SUCCESS_RE = re.compile(r"\[success=(.*?)\]")
ARGS_RE = re.compile(r"\[args=(.*?)\]")
RESULT_RE = re.compile(r"\[result=(.*)\]$")


def _read_lines() -> list[str]:
    if not LOG_PATH.exists():
        return []

    with LOG_PATH.open("r", encoding="utf-8") as file_handle:
        return [line.strip() for line in file_handle.readlines() if line.strip()]


def _parse_line(line: str) -> dict:
    session_match = SESSION_RE.search(line)
    tool_match = TOOL_RE.search(line)
    success_match = SUCCESS_RE.search(line)
    args_match = ARGS_RE.search(line)
    result_match = RESULT_RE.search(line)

    return {
        "raw": line,
        "session_id": session_match.group(1) if session_match else "",
        "tool": tool_match.group(1) if tool_match else "",
        "success": (success_match.group(1).lower() == "true") if success_match else False,
        "args": args_match.group(1) if args_match else "",
        "result": result_match.group(1) if result_match else "",
    }


def get_recent_actions(limit: int = 20) -> list[dict]:
    lines = _read_lines()
    parsed = [_parse_line(line) for line in lines[-limit:]]
    parsed.reverse()
    return parsed


def get_action_summary() -> dict:
    actions = [_parse_line(line) for line in _read_lines()]
    total = len(actions)
    successful = sum(1 for action in actions if action["success"])
    failed = total - successful
    tool_counts = Counter(action["tool"] for action in actions if action["tool"])
    session_counts = Counter(action["session_id"] for action in actions if action["session_id"])

    return {
        "total_actions": total,
        "successful_actions": successful,
        "failed_actions": failed,
        "top_tools": dict(tool_counts.most_common(10)),
        "top_sessions": dict(session_counts.most_common(10)),
    }
