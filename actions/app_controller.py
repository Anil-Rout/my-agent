# app_controller.py — Open and close applications

import subprocess
import psutil
import os

def open_application(app_name: str) -> str:
    """Open an application by name"""
    apps = {
        "chrome": "C:/Program Files/Google/Chrome/Application/chrome.exe",
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "explorer": "explorer.exe",
        "vscode": "code",
        "cmd": "cmd.exe",
    }
    try:
        app_key = app_name.lower()
        if app_key in apps:
            os.startfile(apps[app_key]) if os.path.exists(apps[app_key]) else subprocess.Popen(apps[app_key])
            return f"Opened {app_name}"
        else:
            subprocess.Popen(app_name)
            return f"Opened {app_name}"
    except Exception as e:
        return f"Error opening {app_name}: {str(e)}"

def take_screenshot(save_path: str = "screenshot.png") -> str:
    """Take a screenshot"""
    try:
        import pyautogui
        screenshot = pyautogui.screenshot()
        screenshot.save(save_path)
        return f"Screenshot saved to {save_path}"
    except Exception as e:
        return f"Error taking screenshot: {str(e)}"
