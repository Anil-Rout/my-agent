# clipboard_tool.py — Read and write Windows clipboard

import pyperclip


def make_result(action: str, success: bool, message: str, data: dict | None = None) -> dict:
    return {"success": success, "action": action, "message": message, "data": data or {}}


def get_clipboard() -> dict:
    """Read current text from clipboard."""
    try:
        text = pyperclip.paste()
        if not text:
            return make_result(
                action="get_clipboard",
                success=True,
                message="Clipboard is empty.",
                data={"text": ""},
            )
        preview = text[:200] + ("..." if len(text) > 200 else "")
        return make_result(
            action="get_clipboard",
            success=True,
            message=f"Clipboard contains: {preview}",
            data={"text": text, "length": len(text)},
        )
    except Exception as exc:
        return make_result(
            action="get_clipboard",
            success=False,
            message=f"Failed to read clipboard: {exc}",
        )


def set_clipboard(text: str) -> dict:
    """Write text to clipboard."""
    try:
        pyperclip.copy(text)
        preview = text[:100] + ("..." if len(text) > 100 else "")
        return make_result(
            action="set_clipboard",
            success=True,
            message=f"Copied to clipboard: {preview}",
            data={"text": text, "length": len(text)},
        )
    except Exception as exc:
        return make_result(
            action="set_clipboard",
            success=False,
            message=f"Failed to copy to clipboard: {exc}",
        )


def clear_clipboard() -> dict:
    """Clear the clipboard."""
    try:
        pyperclip.copy("")
        return make_result(
            action="clear_clipboard",
            success=True,
            message="Clipboard cleared.",
        )
    except Exception as exc:
        return make_result(
            action="clear_clipboard",
            success=False,
            message=f"Failed to clear clipboard: {exc}",
        )


def append_to_clipboard(text: str) -> dict:
    """Append text to existing clipboard content."""
    try:
        existing = pyperclip.paste() or ""
        new_text = existing + text
        pyperclip.copy(new_text)
        return make_result(
            action="append_clipboard",
            success=True,
            message=f"Appended to clipboard. Total length: {len(new_text)} chars.",
            data={"text": new_text, "length": len(new_text)},
        )
    except Exception as exc:
        return make_result(
            action="append_clipboard",
            success=False,
            message=f"Failed to append to clipboard: {exc}",
        )