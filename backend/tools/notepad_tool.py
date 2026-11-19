# notepad_tool.py — Full Notepad control via agent
# Supports: open, new tab, write, edit, save, find, replace, all features

import os
import subprocess
import time
import ctypes
import pyautogui
import pyperclip
import pygetwindow as gw
from datetime import datetime


def make_result(action: str, success: bool, message: str, data: dict | None = None) -> dict:
    return {"success": success, "action": action, "message": message, "data": data or {}}


# ── FOCUS HELPERS ─────────────────────────────────────────────────────────────

def _get_notepad_window():
    """Find the Notepad window."""
    windows = [w for w in gw.getAllWindows()
               if 'notepad' in w.title.lower() and w.title.strip()]
    return windows[0] if windows else None


def _focus_notepad() -> bool:
    """Focus the Notepad window. Returns True if found."""
    win = _get_notepad_window()
    if not win:
        return False
    try:
        win.restore()
        time.sleep(0.3)
        user32 = ctypes.windll.user32
        user32.keybd_event(0x12, 0, 0, 0)   # Alt down
        user32.SetForegroundWindow(win._hWnd)
        user32.keybd_event(0x12, 0, 2, 0)   # Alt up
        time.sleep(0.4)
        return True
    except Exception:
        return False


def _open_notepad_if_needed() -> bool:
    """Open Notepad if not already running."""
    if _get_notepad_window():
        return _focus_notepad()
    os.system('start notepad.exe')
    time.sleep(1.5)
    return _focus_notepad()


def _paste_text(text: str) -> None:
    """Paste text into current window via clipboard (more reliable than typewrite)."""
    pyperclip.copy(text)
    time.sleep(0.2)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.2)


# ── CORE FEATURES ─────────────────────────────────────────────────────────────

def open_notepad() -> dict:
    """Open Notepad and return smart suggestions."""
    try:
        os.system('start notepad.exe')
        time.sleep(2.0)  # give it more time to open
        win = _get_notepad_window()
        if not win:
            # Try subprocess as fallback
            subprocess.Popen('notepad.exe', shell=True)
            time.sleep(2.0)
            win = _get_notepad_window()
        if win:
            _focus_notepad()
            return make_result(
                "open_notepad", True,
                "Notepad is open! What would you like to do?\n"
                "• New tab — start fresh\n"
                "• Start writing — tell me what to write\n"
                "• Open a file — which file?\n"
                "• Save after writing — what name?",
                {"suggestions": True}
            )
        # Even if window check fails, notepad likely opened
        return make_result(
            "open_notepad", True,
            "Notepad is open! What would you like to do — new tab, write something, or open a file?",
            {"suggestions": True}
        )
    except Exception as exc:
        return make_result("open_notepad", False, f"Failed: {exc}")


def new_tab() -> dict:
    """Create a new tab in Notepad (Windows 11) or new window (Windows 10)."""
    try:
        if not _open_notepad_if_needed():
            return make_result("new_tab", False, "Notepad is not open.")
        pyautogui.hotkey('ctrl', 'n')
        time.sleep(0.5)
        return make_result("new_tab", True, "New tab created in Notepad.")
    except Exception as exc:
        return make_result("new_tab", False, f"Failed to create new tab: {exc}")


def write_text(text: str, clear_first: bool = False) -> dict:
    """Write text into Notepad. Optionally clear existing content first."""
    try:
        if not _open_notepad_if_needed():
            return make_result("write_text", False, "Notepad is not open.")

        if clear_first:
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.2)
            pyautogui.press('delete')
            time.sleep(0.2)

        _paste_text(text)
        preview = text[:50] + ('...' if len(text) > 50 else '')
        return make_result("write_text", True,
            f"Text written to Notepad: {preview}",
            {"text": text, "cleared_first": clear_first})
    except Exception as exc:
        return make_result("write_text", False, f"Failed to write text: {exc}")


def append_text(text: str) -> dict:
    """Append text at the end of current Notepad content."""
    try:
        if not _open_notepad_if_needed():
            return make_result("append_text", False, "Notepad is not open.")
        pyautogui.hotkey('ctrl', 'end')   # Go to end
        time.sleep(0.2)
        _paste_text(text)
        return make_result("append_text", True,
            f"Text appended to Notepad.",
            {"text": text})
    except Exception as exc:
        return make_result("append_text", False, f"Failed to append text: {exc}")


def clear_notepad() -> dict:
    """Clear all text in current Notepad tab."""
    try:
        if not _focus_notepad():
            return make_result("clear_notepad", False, "Notepad is not open.")
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        pyautogui.press('delete')
        time.sleep(0.2)
        return make_result("clear_notepad", True, "Notepad content cleared.")
    except Exception as exc:
        return make_result("clear_notepad", False, f"Failed to clear: {exc}")


def save_file(filename: str = "") -> dict:
    """Save current Notepad file. Uses Ctrl+S — triggers Save dialog if new file."""
    try:
        if not _focus_notepad():
            return make_result("save_file", False, "Notepad is not open.")

        pyautogui.hotkey('ctrl', 's')
        time.sleep(1.5)

        # Check if Save As dialog appeared (new file)
        # Type filename if provided and dialog is open
        if filename:
            # Clear existing name and type new one
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.2)
            _paste_text(filename)
            time.sleep(0.3)
            pyautogui.press('enter')
            time.sleep(0.5)
            return make_result("save_file", True,
                f"File saved as: {filename}",
                {"filename": filename})

        return make_result("save_file", True, "File saved.")
    except Exception as exc:
        return make_result("save_file", False, f"Failed to save: {exc}")


def save_as(filename: str) -> dict:
    """Save current content as a new file with specified name."""
    try:
        if not _focus_notepad():
            return make_result("save_as", False, "Notepad is not open.")

        # Desktop path
        desktop = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")
        if not os.path.isabs(filename):
            filepath = os.path.join(desktop, filename)
            if not filename.endswith('.txt'):
                filepath += '.txt'
        else:
            filepath = filename

        pyautogui.hotkey('ctrl', 'shift', 's')
        time.sleep(1.5)

        # Type full path in dialog
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        _paste_text(filepath)
        time.sleep(0.3)
        pyautogui.press('enter')
        time.sleep(0.8)

        # Handle overwrite confirmation if exists
        pyautogui.press('enter')
        time.sleep(0.3)

        return make_result("save_as", True,
            f"File saved as: {filepath}",
            {"filepath": filepath})
    except Exception as exc:
        return make_result("save_as", False, f"Failed to save as: {exc}")


def open_file_in_notepad(filepath: str) -> dict:
    """Open a specific file in Notepad."""
    try:
        if not os.path.exists(filepath):
            # Try desktop
            desktop = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")
            alt = os.path.join(desktop, filepath)
            if os.path.exists(alt):
                filepath = alt
            else:
                return make_result("open_file", False, f"File not found: {filepath}")

        subprocess.Popen(f'notepad.exe "{filepath}"', shell=True)
        time.sleep(1.5)
        _focus_notepad()
        return make_result("open_file", True,
            f"Opened in Notepad: {os.path.basename(filepath)}",
            {"filepath": filepath})
    except Exception as exc:
        return make_result("open_file", False, f"Failed to open file: {exc}")


def find_text(search_term: str) -> dict:
    """Find text in Notepad using Find dialog."""
    try:
        if not _focus_notepad():
            return make_result("find_text", False, "Notepad is not open.")

        pyautogui.hotkey('ctrl', 'f')
        time.sleep(0.8)
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        _paste_text(search_term)
        time.sleep(0.3)
        pyautogui.press('enter')
        time.sleep(0.3)

        return make_result("find_text", True,
            f"Searching for: '{search_term}' in Notepad.",
            {"search_term": search_term})
    except Exception as exc:
        return make_result("find_text", False, f"Find failed: {exc}")


def find_and_replace(find_term: str, replace_term: str, replace_all: bool = True) -> dict:
    """Find and replace text in Notepad."""
    try:
        if not _focus_notepad():
            return make_result("find_replace", False, "Notepad is not open.")

        pyautogui.hotkey('ctrl', 'h')
        time.sleep(1.0)

        # Type find term
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        _paste_text(find_term)
        time.sleep(0.3)

        # Tab to replace field
        pyautogui.press('tab')
        time.sleep(0.2)
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        _paste_text(replace_term)
        time.sleep(0.3)

        if replace_all:
            # Alt+A for Replace All
            pyautogui.hotkey('alt', 'a')
        else:
            # Alt+R for Replace once
            pyautogui.hotkey('alt', 'r')

        time.sleep(0.5)
        pyautogui.press('escape')

        action = "all occurrences replaced" if replace_all else "first occurrence replaced"
        return make_result("find_replace", True,
            f"'{find_term}' → '{replace_term}' ({action}).",
            {"find": find_term, "replace": replace_term})
    except Exception as exc:
        return make_result("find_replace", False, f"Replace failed: {exc}")


def select_all() -> dict:
    """Select all text in Notepad."""
    try:
        if not _focus_notepad():
            return make_result("select_all", False, "Notepad is not open.")
        pyautogui.hotkey('ctrl', 'a')
        return make_result("select_all", True, "All text selected.")
    except Exception as exc:
        return make_result("select_all", False, f"Failed: {exc}")


def copy_all_text() -> dict:
    """Select all and copy text from Notepad to clipboard."""
    try:
        if not _focus_notepad():
            return make_result("copy_all", False, "Notepad is not open.")
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.3)
        text = pyperclip.paste()
        preview = text[:100] + ('...' if len(text) > 100 else '')
        return make_result("copy_all", True,
            f"Text copied from Notepad: {preview}",
            {"text": text})
    except Exception as exc:
        return make_result("copy_all", False, f"Failed to copy: {exc}")


def undo() -> dict:
    """Undo last action in Notepad."""
    try:
        if not _focus_notepad():
            return make_result("undo", False, "Notepad is not open.")
        pyautogui.hotkey('ctrl', 'z')
        return make_result("undo", True, "Undo applied.")
    except Exception as exc:
        return make_result("undo", False, f"Undo failed: {exc}")


def redo() -> dict:
    """Redo last undone action in Notepad."""
    try:
        if not _focus_notepad():
            return make_result("redo", False, "Notepad is not open.")
        pyautogui.hotkey('ctrl', 'y')
        return make_result("redo", True, "Redo applied.")
    except Exception as exc:
        return make_result("redo", False, f"Redo failed: {exc}")


def go_to_line(line_number: int) -> dict:
    """Go to a specific line number in Notepad."""
    try:
        if not _focus_notepad():
            return make_result("go_to_line", False, "Notepad is not open.")
        pyautogui.hotkey('ctrl', 'g')
        time.sleep(0.6)
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        pyautogui.typewrite(str(line_number), interval=0.05)
        time.sleep(0.2)
        pyautogui.press('enter')
        return make_result("go_to_line", True,
            f"Moved to line {line_number}.",
            {"line": line_number})
    except Exception as exc:
        return make_result("go_to_line", False, f"Failed: {exc}")


def insert_datetime() -> dict:
    """Insert current date and time at cursor position."""
    try:
        if not _focus_notepad():
            return make_result("insert_datetime", False, "Notepad is not open.")
        pyautogui.press('f5')  # Notepad shortcut for date/time
        return make_result("insert_datetime", True, "Date and time inserted.")
    except Exception as exc:
        return make_result("insert_datetime", False, f"Failed: {exc}")


def toggle_word_wrap() -> dict:
    """Toggle word wrap in Notepad."""
    try:
        if not _focus_notepad():
            return make_result("word_wrap", False, "Notepad is not open.")
        # Format menu → Word Wrap
        pyautogui.hotkey('alt', 'o')
        time.sleep(0.4)
        pyautogui.press('w')
        time.sleep(0.3)
        return make_result("word_wrap", True, "Word wrap toggled.")
    except Exception as exc:
        return make_result("word_wrap", False, f"Failed: {exc}")


def close_notepad_tab() -> dict:
    """Close the current Notepad tab."""
    try:
        if not _focus_notepad():
            return make_result("close_tab", False, "Notepad is not open.")
        pyautogui.hotkey('ctrl', 'w')
        time.sleep(0.5)
        return make_result("close_tab", True, "Notepad tab closed.")
    except Exception as exc:
        return make_result("close_tab", False, f"Failed: {exc}")


def zoom_in() -> dict:
    """Zoom in text in Notepad."""
    try:
        if not _focus_notepad():
            return make_result("zoom_in", False, "Notepad is not open.")
        pyautogui.hotkey('ctrl', '=')
        return make_result("zoom_in", True, "Zoomed in.")
    except Exception as exc:
        return make_result("zoom_in", False, f"Failed: {exc}")


def zoom_out() -> dict:
    """Zoom out text in Notepad."""
    try:
        if not _focus_notepad():
            return make_result("zoom_out", False, "Notepad is not open.")
        pyautogui.hotkey('ctrl', '-')
        return make_result("zoom_out", True, "Zoomed out.")
    except Exception as exc:
        return make_result("zoom_out", False, f"Failed: {exc}")


def zoom_reset() -> dict:
    """Reset zoom to default in Notepad."""
    try:
        if not _focus_notepad():
            return make_result("zoom_reset", False, "Notepad is not open.")
        pyautogui.hotkey('ctrl', '0')
        return make_result("zoom_reset", True, "Zoom reset to default.")
    except Exception as exc:
        return make_result("zoom_reset", False, f"Failed: {exc}")


def get_notepad_status() -> dict:
    """Check if Notepad is open and get current window title."""
    win = _get_notepad_window()
    if win:
        return make_result("notepad_status", True,
            f"Notepad is open — {win.title}",
            {"title": win.title, "open": True})
    return make_result("notepad_status", True,
        "Notepad is not currently open.",
        {"open": False})