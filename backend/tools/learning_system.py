# learning_system.py — Continuous learning like a human
# Agent learns from corrections, feedback, preferences, and mistakes
# Stores lessons permanently and injects them into every conversation

import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from config.paths import BACKEND_DIR

LEARNING_FILE = BACKEND_DIR / "agent_learning.json"
MAX_INJECTED_LESSONS = 15   # Max lessons to inject into prompt
MAX_TOTAL_LESSONS    = 200  # Max lessons to store


# ── DATA STRUCTURE ────────────────────────────────────────────────────────────

def _empty_store() -> dict:
    return {
        "lessons": [],
        "user_profile": {
            "name": None,
            "known_facts": [],
            "preferences": {},
        },
        "stats": {
            "total_interactions": 0,
            "corrections_made": 0,
            "lessons_learned": 0,
        },
    }


# ── FILE I/O ──────────────────────────────────────────────────────────────────

def _load() -> dict:
    if not LEARNING_FILE.exists():
        return _empty_store()
    try:
        return json.loads(LEARNING_FILE.read_text(encoding="utf-8"))
    except Exception:
        return _empty_store()


def _save(store: dict) -> None:
    try:
        LEARNING_FILE.write_text(
            json.dumps(store, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
    except Exception as e:
        print(f"[Learning] Save error: {e}")


# ── FEEDBACK DETECTION ────────────────────────────────────────────────────────

# Signals the user is correcting or teaching
CORRECTION_SIGNALS = [
    "no,", "no ", "wrong", "that's wrong", "that is wrong",
    "incorrect", "not right", "you're wrong", "you are wrong",
    "i didn't mean", "i didn't say", "i said", "i meant",
    "that's not what", "not what i asked", "stop doing",
    "don't do that", "never do that", "you misunderstood",
    "that's not correct", "thats wrong", "nahi", "galat",
]

# Signals the user is happy — reinforcement
PRAISE_SIGNALS = [
    "perfect", "exactly", "yes exactly", "that's right",
    "that is right", "correct", "good job", "well done",
    "great job", "excellent", "amazing", "brilliant",
    "that's what i wanted", "yes that's it", "this is right",
    "you got it", "bilkul", "ekdum sahi", "sahi hai",
]

# Signals the user is teaching the agent a preference
TEACHING_SIGNALS = [
    "remember", "always", "never", "i prefer", "i want you to",
    "next time", "from now on", "in future", "make sure",
    "please always", "please never", "i like when you",
    "i don't like when you", "stop saying", "yaad rakh",
    "hamesha", "kabhi mat",
]

# Signals frustration — something went wrong
FRUSTRATION_SIGNALS = [
    "why did you", "why are you", "that's annoying",
    "this is frustrating", "useless", "not working",
    "again?", "same mistake", "stop it", "ugh", "arre",
    "yaar", "kya kar raha hai",
]

# User sharing personal info
PERSONAL_INFO_PATTERNS = [
    (r"my name is ([A-Za-z]+)", "name"),
    (r"i am ([A-Za-z]+)", "name"),
    (r"i'm ([A-Za-z]+)", "name"),
    (r"call me ([A-Za-z]+)", "name"),
    (r"i am (\d+) years old", "age"),
    (r"i'm (\d+) years old", "age"),
    (r"i live in ([A-Za-z\s]+)", "location"),
    (r"i am from ([A-Za-z\s]+)", "location"),
    (r"i work as ([A-Za-z\s]+)", "profession"),
    (r"i am a ([A-Za-z\s]+)", "profession"),
    (r"i study ([A-Za-z\s]+)", "study"),
    (r"i use ([A-Za-z\s]+) for", "tool_preference"),
]


def detect_feedback_type(user_message: str) -> str | None:
    """Detect what kind of feedback the user is giving."""
    msg = user_message.lower().strip()

    if any(s in msg for s in TEACHING_SIGNALS):
        return "teaching"
    if any(s in msg for s in CORRECTION_SIGNALS):
        return "correction"
    if any(s in msg for s in FRUSTRATION_SIGNALS):
        return "frustration"
    if any(s in msg for s in PRAISE_SIGNALS):
        return "praise"
    return None


def extract_personal_info(user_message: str) -> dict:
    """Extract any personal information the user shares."""
    msg = user_message.lower()
    extracted = {}
    for pattern, field in PERSONAL_INFO_PATTERNS:
        match = re.search(pattern, msg, re.IGNORECASE)
        if match:
            extracted[field] = match.group(1).strip().title()
    return extracted


# ── LESSON MANAGEMENT ─────────────────────────────────────────────────────────

def _find_similar_lesson(lessons: list, topic: str) -> Optional[dict]:
    """Find an existing lesson that covers the same topic."""
    topic_words = set(topic.lower().split())
    for lesson in lessons:
        lesson_words = set(lesson.get("lesson", "").lower().split())
        # If 50%+ words overlap, it's the same lesson
        overlap = topic_words & lesson_words
        if len(overlap) >= max(2, len(topic_words) * 0.5):
            return lesson
    return None


def add_lesson(
    lesson_text: str,
    lesson_type: str,
    trigger: str = "",
    context: str = "",
) -> None:
    """Add or reinforce a lesson."""
    store = _load()
    lessons = store["lessons"]

    # Check if similar lesson exists
    existing = _find_similar_lesson(lessons, lesson_text)

    if existing:
        # Reinforce existing lesson
        existing["times_reinforced"] = existing.get("times_reinforced", 1) + 1
        existing["weight"] = min(10, existing.get("weight", 1) + 1)
        existing["last_reinforced"] = datetime.now().isoformat()
        existing["trigger"] = trigger or existing.get("trigger", "")
    else:
        # New lesson
        lesson = {
            "id": uuid.uuid4().hex[:8],
            "type": lesson_type,
            "lesson": lesson_text,
            "trigger": trigger[:200] if trigger else "",
            "context": context[:300] if context else "",
            "weight": 3 if lesson_type == "teaching" else 2,
            "times_reinforced": 1,
            "created_at": datetime.now().isoformat(),
            "last_reinforced": datetime.now().isoformat(),
        }
        lessons.append(lesson)
        store["stats"]["lessons_learned"] = store["stats"].get("lessons_learned", 0) + 1

    # Keep only the most important lessons
    if len(lessons) > MAX_TOTAL_LESSONS:
        lessons.sort(key=lambda x: x.get("weight", 1), reverse=True)
        store["lessons"] = lessons[:MAX_TOTAL_LESSONS]
    else:
        store["lessons"] = lessons

    _save(store)


def update_user_profile(info: dict) -> None:
    """Update user profile with new personal information."""
    if not info:
        return
    store = _load()
    profile = store.get("user_profile", {})

    for key, value in info.items():
        if key == "name" and value:
            profile["name"] = value
        elif key in ("age", "location", "profession", "study"):
            facts = profile.get("known_facts", [])
            fact_str = f"{key}: {value}"
            if fact_str not in facts:
                facts.append(fact_str)
            profile["known_facts"] = facts[-20:]  # Keep last 20 facts
        elif key == "tool_preference":
            prefs = profile.get("preferences", {})
            prefs["tools"] = prefs.get("tools", [])
            if value not in prefs["tools"]:
                prefs["tools"].append(value)
            profile["preferences"] = prefs

    store["user_profile"] = profile
    _save(store)


def record_interaction() -> None:
    """Record that an interaction happened."""
    store = _load()
    store["stats"]["total_interactions"] = store["stats"].get("total_interactions", 0) + 1
    _save(store)


def record_correction() -> None:
    """Record that a correction was made."""
    store = _load()
    store["stats"]["corrections_made"] = store["stats"].get("corrections_made", 0) + 1
    _save(store)


# ── LEARNING FROM CONVERSATION ────────────────────────────────────────────────

def process_message(
    user_message: str,
    agent_response: str,
    session_id: str = "default",
) -> None:
    """
    Process a conversation turn and learn from it.
    Called after every message exchange.
    """
    try:
        record_interaction()

        # Extract personal info from user message
        personal_info = extract_personal_info(user_message)
        if personal_info:
            update_user_profile(personal_info)

        # Detect feedback type
        feedback = detect_feedback_type(user_message)

        if feedback == "teaching":
            # User is explicitly teaching the agent something
            lesson = f"User preference: {user_message}"
            add_lesson(lesson, "teaching", trigger=user_message)

        elif feedback == "correction":
            # User is correcting the agent
            lesson = f"Correction needed: When user says something like '{user_message[:100]}', previous response was wrong. Adjust approach."
            add_lesson(lesson, "correction", trigger=user_message, context=agent_response[:200])
            record_correction()

        elif feedback == "frustration":
            # User is frustrated — something went repeatedly wrong
            lesson = f"User was frustrated by: '{user_message[:100]}'. Avoid this behavior."
            add_lesson(lesson, "frustration", trigger=user_message, context=agent_response[:200])
            record_correction()

        elif feedback == "praise":
            # User is happy — reinforce what we did
            lesson = f"User approved of this approach: context was '{agent_response[:150]}'"
            add_lesson(lesson, "praise", trigger=user_message, context=agent_response[:200])

    except Exception as e:
        print(f"[Learning] process_message error: {e}")


def learn_from_tool_failure(
    tool_name: str,
    user_request: str,
    error_message: str,
) -> None:
    """Learn when a tool fails so the agent can handle it better next time."""
    try:
        lesson = (
            f"Tool '{tool_name}' failed for request: '{user_request[:100]}'. "
            f"Error: {error_message[:100]}. "
            f"Next time, acknowledge this limitation honestly."
        )
        add_lesson(lesson, "tool_failure", trigger=user_request)
    except Exception:
        pass


# ── PROMPT INJECTION ──────────────────────────────────────────────────────────

def get_learning_context() -> str:
    """
    Format learned lessons and user profile for injection into system prompt.
    Returns empty string if nothing learned yet.
    """
    try:
        store = _load()
        lessons = store.get("lessons", [])
        profile = store.get("user_profile", {})
        stats = store.get("stats", {})

        if not lessons and not profile.get("name") and not profile.get("known_facts"):
            return ""

        lines = ["━━ WHAT I HAVE LEARNED ━━"]

        # User profile
        if profile.get("name"):
            lines.append(f"User's name: {profile['name']}")

        if profile.get("known_facts"):
            lines.append("Known facts about the user:")
            for fact in profile["known_facts"][-10:]:
                lines.append(f"  • {fact}")

        if profile.get("preferences"):
            prefs = profile["preferences"]
            if prefs.get("tools"):
                lines.append(f"User's tools: {', '.join(prefs['tools'][-5:])}")

        # Lessons — sort by weight and recency
        if lessons:
            sorted_lessons = sorted(
                lessons,
                key=lambda x: (x.get("weight", 1), x.get("times_reinforced", 1)),
                reverse=True,
            )
            top_lessons = sorted_lessons[:MAX_INJECTED_LESSONS]

            if top_lessons:
                lines.append("\nLessons learned from past interactions:")
                for lesson in top_lessons:
                    lesson_type = lesson.get("type", "")
                    text = lesson.get("lesson", "")
                    times = lesson.get("times_reinforced", 1)
                    tag = {
                        "teaching": "📚",
                        "correction": "⚠️",
                        "frustration": "❗",
                        "praise": "✅",
                        "tool_failure": "🔧",
                    }.get(lesson_type, "•")
                    reinforced = f" (reinforced {times}x)" if times > 1 else ""
                    lines.append(f"  {tag} {text}{reinforced}")

        # Stats
        total = stats.get("total_interactions", 0)
        corrections = stats.get("corrections_made", 0)
        if total > 0:
            lines.append(
                f"\nInteraction history: {total} conversations, "
                f"{corrections} corrections recorded."
            )

        lines.append("━━━━━━━━━━━━━━━━━━━━━━━")
        return "\n".join(lines)

    except Exception as e:
        print(f"[Learning] get_learning_context error: {e}")
        return ""


# ── MANAGEMENT TOOLS ──────────────────────────────────────────────────────────

def get_all_lessons() -> dict:
    """Return all stored lessons and profile."""
    store = _load()
    return {
        "lessons": store.get("lessons", []),
        "user_profile": store.get("user_profile", {}),
        "stats": store.get("stats", {}),
    }


def delete_lesson(lesson_id: str) -> bool:
    """Delete a specific lesson by ID."""
    store = _load()
    before = len(store["lessons"])
    store["lessons"] = [l for l in store["lessons"] if l.get("id") != lesson_id]
    if len(store["lessons"]) < before:
        _save(store)
        return True
    return False


def clear_all_lessons() -> None:
    """Clear all learned lessons (keep user profile)."""
    store = _load()
    store["lessons"] = []
    store["stats"] = {
        "total_interactions": store["stats"].get("total_interactions", 0),
        "corrections_made": 0,
        "lessons_learned": 0,
    }
    _save(store)


def update_user_name(name: str) -> None:
    """Manually set the user's name."""
    update_user_profile({"name": name})


def get_learning_summary() -> str:
    """Return a human-readable summary of what the agent has learned."""
    store = _load()
    lessons = store.get("lessons", [])
    profile = store.get("user_profile", {})
    stats = store.get("stats", {})

    if not lessons and not profile.get("name"):
        return "I haven't learned anything specific yet. Keep talking to me and I'll get smarter!"

    summary = []

    if profile.get("name"):
        summary.append(f"I know your name is {profile['name']}.")

    if profile.get("known_facts"):
        summary.append(f"I know {len(profile['known_facts'])} facts about you.")

    by_type = {}
    for lesson in lessons:
        t = lesson.get("type", "other")
        by_type[t] = by_type.get(t, 0) + 1

    if by_type.get("teaching"):
        summary.append(f"You've taught me {by_type['teaching']} preferences.")
    if by_type.get("correction"):
        summary.append(f"I've learned from {by_type['correction']} corrections.")
    if by_type.get("praise"):
        summary.append(f"I know {by_type['praise']} things you liked.")

    total = stats.get("total_interactions", 0)
    if total:
        summary.append(f"We've had {total} conversations together.")

    return " ".join(summary)