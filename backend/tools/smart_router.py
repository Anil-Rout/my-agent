# smart_router.py — Detects available apps for a task and asks user to choose

import os
from pathlib import Path

# ── APP DETECTION ─────────────────────────────────────────────────────────────

def _app_exists(paths: list[str]) -> bool:
    """Check if any of the given paths exist."""
    for path in paths:
        if os.path.exists(path):
            return True
    return False


def _get_username() -> str:
    return os.environ.get("USERNAME", "user")


def detect_available_apps() -> dict:
    """
    Detect which apps are installed on this PC, organized by category.
    Returns dict of category → list of available app names.
    """
    u = _get_username()
    home = str(Path.home())

    categories = {}

    # ── Messaging ──
    messaging = []
    if _app_exists([
        rf"C:\Users\{u}\AppData\Local\WhatsApp\WhatsApp.exe",
        rf"{home}\AppData\Local\WhatsApp\WhatsApp.exe",
    ]):
        messaging.append("WhatsApp")

    if _app_exists([
        r"C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE",
        r"C:\Program Files (x86)\Microsoft Office\root\Office16\OUTLOOK.EXE",
        rf"C:\Users\{u}\AppData\Local\Microsoft\WindowsApps\outlook.exe",
    ]):
        messaging.append("Outlook")

    if _app_exists([
        rf"C:\Users\{u}\AppData\Local\Telegram Desktop\Telegram.exe",
    ]):
        messaging.append("Telegram")

    if _app_exists([
        rf"C:\Users\{u}\AppData\Local\Discord\Update.exe",
    ]):
        messaging.append("Discord")

    # Gmail always available via browser
    messaging.append("Gmail (browser)")

    if messaging:
        categories["messaging"] = messaging

    # ── Browsers ──
    browsers = []
    if _app_exists([
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]):
        browsers.append("Chrome")

    if _app_exists([
        rf"C:\Users\{u}\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe",
    ]):
        browsers.append("Brave")

    if _app_exists([
        r"C:\Program Files\Mozilla Firefox\firefox.exe",
        r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
    ]):
        browsers.append("Firefox")

    # Edge is always on Windows 10/11
    browsers.append("Microsoft Edge")

    if browsers:
        categories["browser"] = browsers

    # ── Music / Media ──
    music = []
    if _app_exists([
        rf"C:\Users\{u}\AppData\Roaming\Spotify\Spotify.exe",
        rf"C:\Users\{u}\AppData\Local\Microsoft\WindowsApps\Spotify.exe",
    ]):
        music.append("Spotify")

    if _app_exists([
        r"C:\Program Files\VideoLAN\VLC\vlc.exe",
        r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
    ]):
        music.append("VLC")

    if _app_exists([
        rf"C:\Users\{u}\AppData\Local\Programs\YouTube Music Desktop App\YouTube Music Desktop App.exe",
    ]):
        music.append("YouTube Music")

    music.append("YouTube (browser)")

    if music:
        categories["music"] = music

    # ── Code editors ──
    editors = []
    if _app_exists([r"C:\Program Files\Microsoft VS Code\Code.exe"]):
        editors.append("VS Code")

    if _app_exists([
        r"C:\Program Files\JetBrains",
        r"C:\Program Files (x86)\JetBrains",
    ]):
        editors.append("JetBrains IDE")

    if _app_exists([r"C:\Windows\System32\notepad.exe"]):
        editors.append("Notepad")

    if editors:
        categories["code_editor"] = editors

    # ── Email ──
    email = []
    if "Outlook" in messaging:
        email.append("Outlook")
    email.append("Gmail (browser)")
    if "Thunderbird" in messaging:
        email.append("Thunderbird")
    categories["email"] = email

    # ── Video calls ──
    video = []
    if _app_exists([
        rf"C:\Users\{u}\AppData\Roaming\Zoom\bin\Zoom.exe",
    ]):
        video.append("Zoom")

    if _app_exists([
        rf"C:\Users\{u}\AppData\Local\Microsoft\Teams\current\Teams.exe",
        rf"C:\Users\{u}\AppData\Local\Microsoft\WindowsApps\teams.exe",
    ]):
        video.append("Microsoft Teams")

    video.append("Google Meet (browser)")

    if video:
        categories["video_call"] = video

    return categories


# ── TASK → CATEGORY MAPPING ───────────────────────────────────────────────────

TASK_KEYWORDS = {
    "messaging": [
        "send message", "message to", "send to", "text to",
        "msg to", "send msg", "whatsapp", "telegram",
    ],
    "email": [
        "send email", "email to", "mail to", "send mail",
        "write email", "compose email",
    ],
    "browser": [
        "open browser", "open internet", "browse",
        "search on browser",
    ],
    "music": [
        "play music", "play song", "open music",
        "play", "song", "music",
    ],
    "code_editor": [
        "open editor", "write code", "coding",
        "open code", "edit code",
    ],
    "video_call": [
        "video call", "video meeting", "start meeting",
        "join meeting", "call via",
    ],
}


def detect_task_category(user_message: str) -> str | None:
    """Detect which category a user request belongs to."""
    msg = user_message.lower()
    for category, keywords in TASK_KEYWORDS.items():
        if any(kw in msg for kw in keywords):
            return category
    return None


def get_options_for_task(user_message: str) -> dict | None:
    """Only ask if user did NOT specify which app to use."""
    msg = user_message.lower()

    # If user already named a specific app — don't ask
    specific_apps = [
        "whatsapp", "telegram", "gmail", "outlook", "chrome",
        "brave", "firefox", "edge", "spotify", "vlc", "youtube",
        "zoom", "teams", "meet", "notepad", "vscode", "vs code",
    ]
    if any(app in msg for app in specific_apps):
        return None  # User already chose — proceed directly

    category = detect_task_category(user_message)
    if not category:
        return None

    available = detect_available_apps()
    options = available.get(category, [])

    if len(options) <= 1:
        return None

    return {
        "category": category,
        "options": options,
        "question": _build_question(category, options, user_message),
    }

def _build_question(category: str, options: list, original_request: str) -> str:
    """Build a natural question asking which app to use."""
    options_str = ", ".join(options[:-1]) + f" or {options[-1]}" if len(options) > 1 else options[0]

    category_labels = {
        "messaging": "send this message",
        "email": "send this email",
        "browser": "open",
        "music": "play music",
        "code_editor": "open for coding",
        "video_call": "start the call",
    }

    action = category_labels.get(category, "do this")
    return f"Which app should I use to {action}? {options_str}?"


def get_all_available_apps_summary() -> str:
    """Return a formatted summary of all available apps by category."""
    apps = detect_available_apps()
    if not apps:
        return "Could not detect installed apps."

    lines = ["Apps available on your PC:"]
    labels = {
        "messaging": "Messaging",
        "email": "Email",
        "browser": "Browsers",
        "music": "Music",
        "code_editor": "Code editors",
        "video_call": "Video calls",
    }
    for category, options in apps.items():
        label = labels.get(category, category.title())
        lines.append(f"  {label}: {', '.join(options)}")

    return "\n".join(lines)