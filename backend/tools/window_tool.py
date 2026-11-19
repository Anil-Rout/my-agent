# window_tool.py — Window management for Windows PC

import pygetwindow as gw


def make_result(action: str, success: bool, message: str, data: dict | None = None) -> dict:
    return {"success": success, "action": action, "message": message, "data": data or {}}


def _find_window(title_keyword: str):
    """Find best matching window by keyword in title."""
    keyword = title_keyword.lower().strip()

    # Common app name aliases
    aliases = {
        "chrome": "google chrome",
        "google": "google chrome",
        "browser": "google chrome",
        "firefox": "firefox",
        "edge": "microsoft edge",
        "notepad": "notepad",
        "explorer": "file explorer",
        "file explorer": "file explorer",
        "vs code": "visual studio code",
        "vscode": "visual studio code",
        "code": "visual studio code",
        "word": "microsoft word",
        "excel": "microsoft excel",
        "powerpoint": "microsoft powerpoint",
        "vlc": "vlc",
        "spotify": "spotify",
        "discord": "discord",
        "youtube": "youtube",
        "terminal": "windows powershell",
        "powershell": "powershell",
        "cmd": "cmd",
    }

    # Resolve alias
    search = aliases.get(keyword, keyword)

    all_windows = [w for w in gw.getAllWindows() if w.title.strip()]

    # Try exact keyword match first
    exact = [w for w in all_windows if search in w.title.lower()]
    if exact:
        # Prefer visible/active windows
        return max(exact, key=lambda w: len(w.title))

    # Fall back to original keyword
    fallback = [w for w in all_windows if keyword in w.title.lower()]
    if fallback:
        return max(fallback, key=lambda w: len(w.title))

    return None


def list_windows() -> dict:
    """List all open windows."""
    try:
        windows = [w.title for w in gw.getAllWindows() if w.title.strip()]
        if not windows:
            return make_result(
                action="list_windows",
                success=True,
                message="No open windows found.",
                data={"windows": []},
            )
        window_list = "\n".join(f"  • {t}" for t in windows[:20])
        return make_result(
            action="list_windows",
            success=True,
            message=f"Open windows:\n{window_list}",
            data={"windows": windows},
        )
    except Exception as exc:
        return make_result(
            action="list_windows",
            success=False,
            message=f"Failed to list windows: {exc}",
        )


def minimize_window(title_keyword: str) -> dict:
    """Minimize a window by title keyword."""
    try:
        win = _find_window(title_keyword)
        if not win:
            return make_result(
                action="minimize_window",
                success=False,
                message=f"No window found matching: {title_keyword}",
            )
        win.minimize()
        return make_result(
            action="minimize_window",
            success=True,
            message=f"Minimized: {win.title}",
            data={"title": win.title},
        )
    except Exception as exc:
        return make_result(
            action="minimize_window",
            success=False,
            message=f"Failed to minimize window: {exc}",
        )


def maximize_window(title_keyword: str) -> dict:
    """Maximize a window by title keyword."""
    try:
        win = _find_window(title_keyword)
        if not win:
            return make_result(
                action="maximize_window",
                success=False,
                message=f"No window found matching: {title_keyword}",
            )
        win.maximize()
        return make_result(
            action="maximize_window",
            success=True,
            message=f"Maximized: {win.title}",
            data={"title": win.title},
        )
    except Exception as exc:
        return make_result(
            action="maximize_window",
            success=False,
            message=f"Failed to maximize window: {exc}",
        )


def restore_window(title_keyword: str) -> dict:
    """Restore a minimized or maximized window to normal size."""
    try:
        win = _find_window(title_keyword)
        if not win:
            return make_result(
                action="restore_window",
                success=False,
                message=f"No window found matching: {title_keyword}",
            )
        win.restore()
        return make_result(
            action="restore_window",
            success=True,
            message=f"Restored: {win.title}",
            data={"title": win.title},
        )
    except Exception as exc:
        return make_result(
            action="restore_window",
            success=False,
            message=f"Failed to restore window: {exc}",
        )


def close_window(title_keyword: str) -> dict:
    """Close a window by title keyword."""
    try:
        win = _find_window(title_keyword)
        if not win:
            return make_result(
                action="close_window",
                success=False,
                message=f"No window found matching: {title_keyword}",
            )
        title = win.title
        win.close()
        return make_result(
            action="close_window",
            success=True,
            message=f"Closed: {title}",
            data={"title": title},
        )
    except Exception as exc:
        return make_result(
            action="close_window",
            success=False,
            message=f"Failed to close window: {exc}",
        )


def focus_window(title_keyword: str) -> dict:
    """Bring a window to the front and focus it."""
    try:
        import ctypes
        import time

        win = _find_window(title_keyword)
        if not win:
            return make_result(
                action="focus_window",
                success=False,
                message=f"No window found matching: {title_keyword}",
            )

        win.restore()
        time.sleep(0.2)

        user32 = ctypes.windll.user32
        hwnd = win._hWnd
        user32.keybd_event(0x12, 0, 0, 0)
        user32.SetForegroundWindow(hwnd)
        user32.keybd_event(0x12, 0, 2, 0)

        return make_result(
            action="focus_window",
            success=True,
            message=f"Focused: {win.title}",
            data={"title": win.title},
        )
    except Exception as exc:
        return make_result(
            action="focus_window",
            success=False,
            message=f"Failed to focus window: {exc}",
        )


def minimize_all_windows() -> dict:
    """Minimize all open windows and show the desktop."""
    try:
        import ctypes
        ctypes.windll.user32.keybd_event(0x5B, 0, 0, 0)   # Win key down
        ctypes.windll.user32.keybd_event(0x44, 0, 0, 0)   # D key down
        ctypes.windll.user32.keybd_event(0x44, 0, 2, 0)   # D key up
        ctypes.windll.user32.keybd_event(0x5B, 0, 2, 0)   # Win key up
        return make_result(
            action="minimize_all_windows",
            success=True,
            message="All windows minimized — desktop shown.",
        )
    except Exception as exc:
        return make_result(
            action="minimize_all_windows",
            success=False,
            message=f"Failed to minimize all windows: {exc}",
        )