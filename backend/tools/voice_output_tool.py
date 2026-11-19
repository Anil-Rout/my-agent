# voice_output_tool.py — Neural text-to-speech using Microsoft Edge TTS
# Uses en-IN-NeerjaNeural — natural Indian English female voice
# Falls back to pyttsx3 Zira if edge-tts unavailable

import asyncio
import os
import re
import tempfile
import threading

# ── VOICE CONFIG ─────────────────────────────────────────────────────────────

# Primary — Microsoft Neural voices (edge-tts)
# Options: en-IN-NeerjaNeural, en-US-JennyNeural, en-US-AriaNeural
PRIMARY_VOICE   = "en-IN-NeerjaNeural"
FALLBACK_VOICE  = "en-US-JennyNeural"

# Speech settings
SPEAKING_RATE   = "-5%"    # Slightly slower than default for clarity
SPEAKING_VOLUME = "+10%"   # Slightly louder

_lock    = threading.Lock()
_speaking = False
_current_thread = None


# ── TEXT CLEANING ─────────────────────────────────────────────────────────────

def _clean(text: str) -> str:
    """Clean text before speaking — remove markdown, emoji, excess length."""
    if not text:
        return ""

    # Remove markdown
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*',     r'\1', text)
    text = re.sub(r'`{1,3}.*?`{1,3}', '', text, flags=re.DOTALL)
    text = re.sub(r'#{1,6}\s',      '',  text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

    # Remove emoji and non-ASCII (keep Indian chars)
    text = re.sub(r'[^\x00-\x7F\u0900-\u097F\s]+', ' ', text)

    # Remove list markers
    text = re.sub(r'^\s*[-•*]\s+',  '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)

    # Flatten newlines
    text = re.sub(r'\n+', '. ', text)
    text = re.sub(r'\s+', ' ', text)

    # Cap at 250 chars — find natural sentence break
    if len(text) > 250:
        cut = text[:250].rfind('.')
        text = text[:cut + 1] if cut > 80 else text[:250]

    return text.strip()


# ── EDGE-TTS PLAYBACK ─────────────────────────────────────────────────────────

async def _speak_edge(text: str, voice: str) -> None:
    """Generate speech with edge-tts and play with pygame."""
    import edge_tts
    import pygame

    communicate = edge_tts.Communicate(
        text,
        voice=voice,
        rate=SPEAKING_RATE,
        volume=SPEAKING_VOLUME,
    )

    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp_path = tmp.name
    tmp.close()

    try:
        await communicate.save(tmp_path)

        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.mixer.init()
        pygame.mixer.music.load(tmp_path)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            await asyncio.sleep(0.05)

        pygame.mixer.music.stop()
        pygame.mixer.quit()
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def _run_edge_tts(text: str) -> bool:
    """Try to speak with edge-tts. Returns True if successful."""
    try:
        for voice in [PRIMARY_VOICE, FALLBACK_VOICE]:
            try:
                asyncio.run(_speak_edge(text, voice))
                return True
            except Exception as e:
                if "Voice" in str(e) or "not found" in str(e).lower():
                    continue
                raise
        return False
    except Exception as e:
        print(f"[TTS] edge-tts error: {e}")
        return False


# ── PYTTSX3 FALLBACK ──────────────────────────────────────────────────────────

_pyttsx3_engine = None

def _get_pyttsx3():
    global _pyttsx3_engine
    if _pyttsx3_engine is not None:
        return _pyttsx3_engine
    try:
        import pyttsx3
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')

        # Find best female voice
        female = None
        for v in voices:
            name = v.name.lower()
            if any(n in name for n in ['zira', 'hazel', 'susan', 'female']):
                female = v.id
                break

        # Fallback — any non-male voice
        if not female:
            for v in voices:
                name = v.name.lower()
                if not any(n in name for n in ['david', 'mark', 'george', 'james']):
                    female = v.id
                    break

        if female:
            engine.setProperty('voice', female)

        engine.setProperty('rate', 155)
        engine.setProperty('volume', 0.95)
        _pyttsx3_engine = engine
        return engine
    except Exception as e:
        print(f"[TTS] pyttsx3 init error: {e}")
        return None


def _run_pyttsx3(text: str) -> None:
    try:
        engine = _get_pyttsx3()
        if engine:
            engine.say(text)
            engine.runAndWait()
    except Exception as e:
        print(f"[TTS] pyttsx3 speak error: {e}")


# ── PUBLIC API ────────────────────────────────────────────────────────────────

def speak(text: str) -> None:
    """
    Speak text using neural TTS (edge-tts) with pyttsx3 fallback.
    Runs in background thread — never blocks the agent response.
    """
    global _speaking, _current_thread

    cleaned = _clean(text)
    if not cleaned:
        return

    def _run():
        global _speaking
        with _lock:
            _speaking = True
            try:
                success = _run_edge_tts(cleaned)
                if not success:
                    _run_pyttsx3(cleaned)
            finally:
                _speaking = False

    # Cancel previous speech if still running
    _current_thread = threading.Thread(target=_run, daemon=True)
    _current_thread.start()


def stop_speaking() -> str:
    """Stop current speech immediately."""
    global _speaking
    _speaking = False
    try:
        import pygame
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
    except Exception:
        pass
    try:
        global _pyttsx3_engine
        if _pyttsx3_engine:
            _pyttsx3_engine.stop()
    except Exception:
        pass
    return "Stopped."


def is_speaking() -> bool:
    return _speaking


def set_speaking_rate(rate: str = "normal") -> str:
    """Set speaking rate: slow / normal / fast."""
    global SPEAKING_RATE
    rates = {"slow": "-15%", "normal": "-5%", "fast": "+10%"}
    SPEAKING_RATE = rates.get(rate.lower(), "-5%")
    return f"Speaking rate set to {rate}."


def set_voice(voice_name: str) -> str:
    """
    Change the neural voice.
    Options: neerja (Indian), jenny (US), aria (US)
    """
    global PRIMARY_VOICE
    voices = {
        "neerja": "en-IN-NeerjaNeural",
        "indian": "en-IN-NeerjaNeural",
        "jenny":  "en-US-JennyNeural",
        "aria":   "en-US-AriaNeural",
        "us":     "en-US-JennyNeural",
    }
    PRIMARY_VOICE = voices.get(voice_name.lower(), "en-IN-NeerjaNeural")
    return f"Voice changed to {PRIMARY_VOICE}."