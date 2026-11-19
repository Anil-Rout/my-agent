# screen_tool.py — Screenshot + AI vision description

import base64
import os
import tempfile
from datetime import datetime

import pyautogui
import requests

from config.paths import load_backend_env

load_backend_env()

DESKTOP = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"


def make_result(action: str, success: bool, message: str, data: dict | None = None) -> dict:
    return {"success": success, "action": action, "message": message, "data": data or {}}


def _screenshot_to_base64() -> tuple[str, str]:
    """Take screenshot and return (base64_string, temp_file_path)."""
    screenshot = pyautogui.screenshot()
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    screenshot.save(tmp.name)
    tmp.close()
    with open(tmp.name, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return b64, tmp.name


def _ask_vision(b64_image: str, question: str) -> str:
    """Send screenshot to Groq vision model and get description."""
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set")

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": VISION_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{b64_image}"
                            },
                        },
                        {
                            "type": "text",
                            "text": question,
                        },
                    ],
                }
            ],
            "max_tokens": 1024,
        },
        timeout=30,
    )

    if response.status_code != 200:
        raise RuntimeError(f"Vision API error {response.status_code}: {response.text[:200]}")

    return response.json()["choices"][0]["message"]["content"]


def capture_and_describe(question: str = "Describe everything you see on this screen in detail.") -> dict:
    """Take a screenshot and describe it using AI vision."""
    tmp_path = None
    try:
        b64, tmp_path = _screenshot_to_base64()
        description = _ask_vision(b64, question)
        return make_result(
            action="capture_and_describe",
            success=True,
            message=description,
            data={"question": question},
        )
    except Exception as exc:
        return make_result(
            action="capture_and_describe",
            success=False,
            message=f"Screen capture failed: {exc}",
        )
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


def save_screenshot(filename: str | None = None) -> dict:
    """Take a screenshot and save it to Desktop."""
    try:
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"

        if not filename.endswith(".png"):
            filename += ".png"

        path = os.path.join(DESKTOP, filename)
        screenshot = pyautogui.screenshot()
        screenshot.save(path)

        return make_result(
            action="save_screenshot",
            success=True,
            message=f"Screenshot saved to Desktop: {filename}",
            data={"path": path, "filename": filename},
        )
    except Exception as exc:
        return make_result(
            action="save_screenshot",
            success=False,
            message=f"Failed to save screenshot: {exc}",
        )


def capture_and_answer(question: str) -> dict:
    """Take a screenshot and answer a specific question about what's on screen."""
    return capture_and_describe(question=question)