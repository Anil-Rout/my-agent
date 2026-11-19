import os
import subprocess
import time
import threading
import ctypes

from tools.file_tool import resolve_existing_folder_path

DESKTOP = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")
def _force_window_to_front(keyword: str, wait: float = 1.8) -> None:
    """
    Wait for a window matching keyword to appear then force it to front.
    Runs in a background thread so it never blocks the agent response.
    Uses the Alt-key trick which bypasses Windows focus-steal protection.
    """
    def _run():
        time.sleep(wait)
        try:
            user32 = ctypes.windll.user32
            found = []

            EnumWindowsProc = ctypes.WINFUNCTYPE(
                ctypes.c_bool,
                ctypes.POINTER(ctypes.c_int),
                ctypes.POINTER(ctypes.c_int),
            )

            def callback(hwnd, _):
                if user32.IsWindowVisible(hwnd):
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buf = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(hwnd, buf, length + 1)
                        if keyword.lower() in buf.value.lower():
                            found.append(hwnd)
                return True

            user32.EnumWindows(EnumWindowsProc(callback), 0)

            if found:
                hwnd = found[0]
                # Alt-key trick — tricks Windows into allowing focus change
                user32.keybd_event(0x12, 0, 0, 0)   # Alt key down
                user32.SetForegroundWindow(hwnd)
                user32.keybd_event(0x12, 0, 2, 0)   # Alt key up
                user32.ShowWindow(hwnd, 9)            # SW_RESTORE
        except Exception:
            pass

    threading.Thread(target=_run, daemon=True).start()


APPS = {
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "google chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "firefox": r"C:\Program Files\Mozilla Firefox\firefox.exe",
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
    "vscode": "code",
    "visual studio code": "code",
    "cmd": "cmd.exe",
    "command prompt": "cmd.exe",
    "powershell": "powershell.exe",
    "paint": "mspaint.exe",
    "wordpad": "wordpad.exe",
    "task manager": "taskmgr.exe",
    "control": "control.exe",
    "control panel": "control.exe",
    "settings": "ms-settings:",
    "camera": "microsoft.windows.camera:",
    "windows camera": "microsoft.windows.camera:",
    "whatsapp": "whatsapp:",
    "whats app": "whatsapp:",
}


APP_WINDOW_KEYWORDS = {
    "chrome": "Chrome",
    "google chrome": "Chrome",
    "firefox": "Firefox",
    "notepad": "Notepad",
    "calculator": "Calculator",
    "calc": "Calculator",
    "explorer": "File Explorer",
    "file explorer": "File Explorer",
    "vscode": "Visual Studio Code",
    "visual studio code": "Visual Studio Code",
    "cmd": "Command Prompt",
    "command prompt": "Command Prompt",
    "powershell": "PowerShell",
    "paint": "Paint",
    "wordpad": "WordPad",
    "task manager": "Task Manager",
    "control panel": "Control Panel",
    "settings": "Settings",
}


def _tool_result(action: str, success: bool, message: str, data: dict | None = None) -> dict:
    return {
        "success": success,
        "action": action,
        "message": message,
        "data": data or {},
    }


def open_application(app_name: str) -> dict:
    """Open an application by name."""
    try:
        app_key = app_name.lower().strip()
        launch_target = APPS.get(app_key, app_name)

        if launch_target.startswith("ms-") or launch_target.startswith("microsoft."):
              os.system(f'start {launch_target}')
        elif launch_target.endswith(".exe") or launch_target in ("notepad.exe", "calc.exe", "mspaint.exe", "taskmgr.exe", "cmd.exe", "powershell.exe", "wordpad.exe", "control.exe"):
            os.system(f'start "" "{launch_target}"')
        else:
            os.system(f'start "" "{launch_target}"')

        keyword = APP_WINDOW_KEYWORDS.get(app_key, app_name)
        _force_window_to_front(keyword)

        return _tool_result(
            action="open_application",
            success=True,
            message=f"Opened application: {app_name}",
            data={"app_name": app_name},
        )
    except Exception as exc:
        return _tool_result(
            action="open_application",
            success=False,
            message=f"Failed to open application '{app_name}': {exc}",
            data={"app_name": app_name},
        )


def open_website(url: str) -> str:
    """Open a website in the default browser."""
    try:
        import webbrowser

        if not url.startswith("http"):
            url = "https://" + url
        webbrowser.open(url)
        return f"Opened website: {url}"
    except Exception as exc:
        return f"Error: {exc}"


def take_screenshot(filename: str | None = None) -> str:
    """Take a screenshot and save it."""
    try:
        import pyautogui
        from datetime import datetime

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"

        path = os.path.join(DESKTOP, filename)
        screenshot = pyautogui.screenshot()
        screenshot.save(path)
        return f"Screenshot saved: {path}"
    except Exception as exc:
        return f"Error taking screenshot: {exc}"


def open_file(path: str) -> str:
    """Open any file with its default application."""
    try:
        os.startfile(path)
        return f"Opened file: {path}"
    except Exception as exc:
        return f"Error opening file: {exc}"


def open_folder(path: str) -> dict:
    """Open a folder in File Explorer."""
    try:
        resolved_path = resolve_existing_folder_path(path)
        if not resolved_path:
            return _tool_result(
                action="open_folder",
                success=False,
                message=f"Folder not found: {path}",
                data={"path": path},
            )
        subprocess.Popen(f'explorer "{resolved_path}"', shell=True)
        return _tool_result(
            action="open_folder",
            success=True,
            message=f"Opened folder: {resolved_path}",
            data={"path": resolved_path},
        )
    except Exception as exc:
        return _tool_result(
            action="open_folder",
            success=False,
            message=f"Failed to open folder: {exc}",
            data={"path": path},
        )


def get_open_windows() -> str:
    """Get the list of open windows."""
    try:
        import pygetwindow as gw

        windows = [title for title in gw.getAllTitles() if title.strip()]
        if not windows:
            return "No open windows found"

        result = "Open Windows:\n"
        for title in windows[:15]:
            result += f"  - {title}\n"
        return result
    except Exception as exc:
        return f"Error: {exc}"


def shutdown_pc(delay: int = 0) -> str:
    """Schedule a PC shutdown."""
    try:
        os.system(f"shutdown /s /t {delay}")
        return f"PC will shutdown in {delay} seconds"
    except Exception as exc:
        return f"Error: {exc}"


def restart_pc(delay: int = 0) -> str:
    """Schedule a PC restart."""
    try:
        os.system(f"shutdown /r /t {delay}")
        return f"PC will restart in {delay} seconds"
    except Exception as exc:
        return f"Error: {exc}"


def cancel_shutdown() -> str:
    """Cancel a scheduled shutdown or restart."""
    try:
        os.system("shutdown /a")
        return "Shutdown cancelled"
    except Exception as exc:
        return f"Error: {exc}"


def set_volume(level: int) -> str:
    """Set system volume 0-100."""
    try:
        from ctypes import POINTER, cast

        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMasterVolumeLevelScalar(level / 100, None)
        return f"Volume set to {level}%"
    except Exception as exc:
        return f"Error setting volume: {exc}"


def lock_screen() -> dict:
    """Lock the Windows PC screen."""
    try:
        import ctypes
        ctypes.windll.user32.LockWorkStation()
        return _tool_result(
            action="lock_screen",
            success=True,
            message="PC screen locked.",
            data={},
        )
    except Exception as exc:
        return _tool_result(
            action="lock_screen",
            success=False,
            message=f"Failed to lock screen: {exc}",
            data={},
        )


def sleep_pc() -> dict:
    """Put the PC to sleep."""
    try:
        import subprocess
        subprocess.Popen(
            "rundll32.exe powrprof.dll,SetSuspendState 0,1,0",
            shell=True,
        )
        return _tool_result(
            action="sleep_pc",
            success=True,
            message="PC is going to sleep.",
            data={},
        )
    except Exception as exc:
        return _tool_result(
            action="sleep_pc",
            success=False,
            message=f"Failed to sleep PC: {exc}",
            data={},
        )

def take_photo_with_camera() -> dict:
    """Open Camera app, wait for it to load, then take a photo."""
    try:
        import pyautogui
        import time

        # Open Windows Camera app
        os.system('start microsoft.windows.camera:')
        time.sleep(3)  # Wait for camera to load fully

        # Focus the camera window
        _force_window_to_front('Camera', wait=0)
        time.sleep(0.5)

        # Press Space to take photo (Windows Camera shortcut)
        pyautogui.press('space')
        time.sleep(1)

        # Photos are saved automatically to Pictures/Camera Roll
        camera_roll = os.path.join(
            os.path.expanduser("~"), "Pictures", "Camera Roll"
        )

        return _tool_result(
            action="take_photo",
            success=True,
            message=f"Photo taken and saved to: {camera_roll}",
            data={"folder": camera_roll},
        )
    except Exception as exc:
        return _tool_result(
            action="take_photo",
            success=False,
            message=f"Failed to take photo: {exc}",
            data={},
        )