# whatsapp_tool.py — Send WhatsApp messages via desktop app
# Uses contact book for accurate name-to-number matching

import os
import time
import json
import webbrowser
import subprocess
import pyautogui
import pygetwindow as gw
import ctypes
from pathlib import Path
import io
import wave
import urllib.parse

from config.paths import BACKEND_DIR

# Contact book file — stores name → phone number mapping
CONTACTS_FILE = BACKEND_DIR / "whatsapp_contacts.json"


def make_result(action: str, success: bool, message: str, data: dict | None = None) -> dict:
    return {"success": success, "action": action, "message": message, "data": data or {}}


# ── CONTACT BOOK ──────────────────────────────────────────

def _load_contacts() -> dict:
    """Load contacts from JSON file."""
    if not CONTACTS_FILE.exists():
        return {}
    try:
        return json.loads(CONTACTS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_contacts(contacts: dict) -> None:
    """Save contacts to JSON file."""
    CONTACTS_FILE.write_text(
        json.dumps(contacts, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def _find_contact(name: str) -> str | None:
    """Find phone number by name (case-insensitive partial match)."""
    contacts = _load_contacts()
    name_lower = name.lower().strip()
    # Exact match first
    for contact_name, number in contacts.items():
        if contact_name.lower() == name_lower:
            return number
    # Partial match
    for contact_name, number in contacts.items():
        if name_lower in contact_name.lower():
            return number
    return None


def add_whatsapp_contact(name: str, phone: str) -> dict:
    """
    Add a contact to the WhatsApp contact book.
    phone must include country code e.g. +919876543210
    """
    try:
        # Clean phone number — keep only digits and leading +
        cleaned = '+' + ''.join(c for c in phone if c.isdigit())
        contacts = _load_contacts()
        contacts[name.strip()] = cleaned
        _save_contacts(contacts)
        return make_result(
            action="add_contact",
            success=True,
            message=f"Contact saved: {name} → {cleaned}",
            data={"name": name, "phone": cleaned},
        )
    except Exception as exc:
        return make_result(
            action="add_contact",
            success=False,
            message=f"Failed to save contact: {exc}",
        )


def list_whatsapp_contacts() -> dict:
    """List all saved WhatsApp contacts."""
    contacts = _load_contacts()
    if not contacts:
        return make_result(
            action="list_contacts",
            success=True,
            message="No contacts saved yet. Add contacts with their phone numbers first.",
            data={"contacts": {}},
        )
    lines = "\n".join(f"  • {name}: {number}" for name, number in contacts.items())
    return make_result(
        action="list_contacts",
        success=True,
        message=f"Saved WhatsApp contacts:\n{lines}",
        data={"contacts": contacts},
    )


def remove_whatsapp_contact(name: str) -> dict:
    """Remove a contact from the contact book."""
    contacts = _load_contacts()
    name_lower = name.lower().strip()
    found = None
    for contact_name in list(contacts.keys()):
        if contact_name.lower() == name_lower:
            found = contact_name
            break
    if not found:
        return make_result(
            action="remove_contact",
            success=False,
            message=f"Contact '{name}' not found.",
        )
    del contacts[found]
    _save_contacts(contacts)
    return make_result(
        action="remove_contact",
        success=True,
        message=f"Contact '{found}' removed.",
    )


# ── WHATSAPP MESSAGING ────────────────────────────────────

def send_whatsapp_message(contact: str, message: str) -> dict:
    """
    Send a WhatsApp message using wa.me URL scheme.
    Opens WhatsApp desktop directly to the correct contact.
    """
    try:
        phone = _find_contact(contact)

        if not phone:
            return make_result(
                action="send_whatsapp",
                success=False,
                message=(
                    f"I don't have {contact}'s number saved. "
                    f"Please add it first by saying: "
                    f"'add whatsapp contact {contact} +91XXXXXXXXXX'"
                ),
                data={"contact": contact},
            )

        # Encode message for URL
        import urllib.parse
        encoded_msg = urllib.parse.quote(message)

        # Remove + from phone for wa.me URL
        phone_digits = phone.replace('+', '').replace(' ', '')

        # Open WhatsApp directly to this contact with pre-filled message
        url = f"whatsapp://send?phone={phone_digits}&text={encoded_msg}"
        os.system(f'start "" "{url}"')
        time.sleep(3)

        # Focus WhatsApp
        user32 = ctypes.windll.user32
        windows = [w for w in gw.getAllWindows()
                   if 'whatsapp' in w.title.lower() and w.title.strip()]
        if windows:
            win = windows[0]
            win.restore()
            time.sleep(0.5)
            user32.keybd_event(0x12, 0, 0, 0)
            user32.SetForegroundWindow(win._hWnd)
            user32.keybd_event(0x12, 0, 2, 0)
            time.sleep(0.8)

            # Press Enter to send the pre-filled message
            pyautogui.press('enter')
            time.sleep(0.5)

        return make_result(
            action="send_whatsapp",
            success=True,
            message=f"Message sent to {contact} ({phone}).",
            data={"contact": contact, "phone": phone, "message": message},
        )

    except Exception as exc:
        return make_result(
            action="send_whatsapp",
            success=False,
            message=f"Failed to send WhatsApp message: {exc}",
        )


def open_whatsapp_chat(contact: str) -> dict:
    """Open WhatsApp chat with a specific contact using their saved number."""
    try:
        phone = _find_contact(contact)

        if not phone:
            return make_result(
                action="open_whatsapp_chat",
                success=False,
                message=(
                    f"I don't have {contact}'s number saved. "
                    f"Add it first: 'add whatsapp contact {contact} +91XXXXXXXXXX'"
                ),
            )

        phone_digits = phone.replace('+', '').replace(' ', '')
        url = f"whatsapp://send?phone={phone_digits}"
        os.system(f'start "" "{url}"')
        time.sleep(2)

        return make_result(
            action="open_whatsapp_chat",
            success=True,
            message=f"Opened WhatsApp chat with {contact}.",
            data={"contact": contact, "phone": phone},
        )
    except Exception as exc:
        return make_result(
            action="open_whatsapp_chat",
            success=False,
            message=f"Failed to open chat: {exc}",
        )





# ── IMAGE SENDING ─────────────────────────────────────────

def _copy_image_to_clipboard(image_path: str) -> bool:
    """Copy an image file to Windows clipboard."""
    try:
        import win32clipboard
        from PIL import Image

        img = Image.open(image_path).convert('RGB')
        output = io.BytesIO()
        img.save(output, 'BMP')
        data = output.getvalue()[14:]  # Strip BMP file header
        output.close()

        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
        win32clipboard.CloseClipboard()
        return True
    except Exception as exc:
        print(f"Clipboard image error: {exc}")
        return False


def send_whatsapp_image(contact: str, image_path: str) -> dict:
    """
    Send an image to a WhatsApp contact.
    Opens the chat, pastes image from clipboard, and sends.
    image_path: full path to the image file
    """
    try:
        # Verify file exists
        if not os.path.exists(image_path):
            # Try resolving from desktop/documents
            desktop = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")
            alt_path = os.path.join(desktop, image_path)
            if os.path.exists(alt_path):
                image_path = alt_path
            else:
                return make_result(
                    action="send_whatsapp_image",
                    success=False,
                    message=f"Image not found: {image_path}",
                )

        # Find contact number
        phone = _find_contact(contact)
        if not phone:
            return make_result(
                action="send_whatsapp_image",
                success=False,
                message=(
                    f"I don't have {contact}'s number saved. "
                    f"Add it first: 'add whatsapp contact {contact} +91XXXXXXXXXX'"
                ),
            )

        # Copy image to clipboard
        if not _copy_image_to_clipboard(image_path):
            return make_result(
                action="send_whatsapp_image",
                success=False,
                message="Failed to copy image to clipboard.",
            )

        # Open the specific chat
        phone_digits = phone.replace('+', '').replace(' ', '')
        url = f"whatsapp://send?phone={phone_digits}"
        os.system(f'start "" "{url}"')
        time.sleep(3.5)

        # Focus WhatsApp
        user32 = ctypes.windll.user32
        windows = [w for w in gw.getAllWindows()
                   if 'whatsapp' in w.title.lower() and w.title.strip()]
        if windows:
            win = windows[0]
            win.restore()
            time.sleep(0.5)
            user32.keybd_event(0x12, 0, 0, 0)
            user32.SetForegroundWindow(win._hWnd)
            user32.keybd_event(0x12, 0, 2, 0)
            time.sleep(0.8)

        # Click message input area and paste image
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(1.5)

        # Press Enter to send
        pyautogui.press('enter')
        time.sleep(0.5)

        filename = os.path.basename(image_path)
        return make_result(
            action="send_whatsapp_image",
            success=True,
            message=f"Image '{filename}' sent to {contact}.",
            data={"contact": contact, "image": image_path},
        )

    except Exception as exc:
        return make_result(
            action="send_whatsapp_image",
            success=False,
            message=f"Failed to send image: {exc}",
        )


# ── VOICE NOTE ────────────────────────────────────────────

def record_voice_note(duration_seconds: int = 5) -> dict:
    """
    Record audio from the microphone and save as a WAV file.
    Returns the path of the saved file.
    """
    try:
        import sounddevice as sd
        import soundfile as sf
        from datetime import datetime

        sample_rate = 44100
        filename = f"voice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        save_path = os.path.join(
            os.path.expanduser("~"), "OneDrive", "Desktop", filename
        )

        print(f"Recording for {duration_seconds} seconds...")
        audio = sd.rec(
            int(duration_seconds * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype='float32'
        )
        sd.wait()  # Wait until recording is complete
        sf.write(save_path, audio, sample_rate)

        return make_result(
            action="record_voice",
            success=True,
            message=f"Voice note recorded ({duration_seconds}s) and saved to Desktop: {filename}",
            data={"path": save_path, "filename": filename, "duration": duration_seconds},
        )
    except Exception as exc:
        return make_result(
            action="record_voice",
            success=False,
            message=f"Failed to record voice: {exc}",
        )


def send_whatsapp_voice(contact: str, duration_seconds: int = 5) -> dict:
    """
    Record a voice note and send it to a WhatsApp contact as an audio file.
    duration_seconds: how many seconds to record
    """
    try:
        # Step 1 — Record
        record_result = record_voice_note(duration_seconds)
        if not record_result["success"]:
            return record_result

        audio_path = record_result["data"]["path"]
        filename = record_result["data"]["filename"]

        # Step 2 — Find contact
        phone = _find_contact(contact)
        if not phone:
            return make_result(
                action="send_whatsapp_voice",
                success=False,
                message=(
                    f"Voice note recorded but I don't have {contact}'s number. "
                    f"File saved to Desktop: {filename}. "
                    f"Add contact first: 'add whatsapp contact {contact} +91XXXXXXXXXX'"
                ),
            )

        # Step 3 — Open chat
        phone_digits = phone.replace('+', '').replace(' ', '')
        url = f"whatsapp://send?phone={phone_digits}"
        os.system(f'start "" "{url}"')
        time.sleep(3.5)

        # Step 4 — Focus WhatsApp
        user32 = ctypes.windll.user32
        windows = [w for w in gw.getAllWindows()
                   if 'whatsapp' in w.title.lower() and w.title.strip()]
        if windows:
            win = windows[0]
            win.restore()
            time.sleep(0.5)
            user32.keybd_event(0x12, 0, 0, 0)
            user32.SetForegroundWindow(win._hWnd)
            user32.keybd_event(0x12, 0, 2, 0)
            time.sleep(0.8)

        # Step 5 — Attach the audio file
        # Click attachment button (paperclip) using keyboard shortcut
        pyautogui.hotkey('ctrl', 'o')  # some versions support this
        time.sleep(1.5)

        # If file dialog opened — type the path and press enter
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.typewrite(audio_path, interval=0.03)
        time.sleep(0.5)
        pyautogui.press('enter')
        time.sleep(1.5)
        pyautogui.press('enter')  # confirm send
        time.sleep(0.5)

        return make_result(
            action="send_whatsapp_voice",
            success=True,
            message=f"Voice note ({duration_seconds}s) sent to {contact}.",
            data={"contact": contact, "file": audio_path},
        )

    except Exception as exc:
        return make_result(
            action="send_whatsapp_voice",
            success=False,
            message=f"Failed to send voice note: {exc}",
        )