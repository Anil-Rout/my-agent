# memory.py — Stores and retrieves conversation history
# Agent remembers what you talked about

import json
import os
from datetime import datetime

MEMORY_FILE = "database/memory.json"

def save_message(role: str, content: str):
    """Save a single message to memory file"""
    memory = load_memory()
    memory.append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

def load_memory() -> list:
    """Load all messages from memory file"""
    if not os.path.exists(MEMORY_FILE):
        return []
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def get_conversation_history() -> list:
    """Get history in format Groq API expects"""
    memory = load_memory()
    return [
        {"role": m["role"], "content": m["content"]}
        for m in memory[-20:]  # Last 20 messages only
    ]

def clear_memory():
    """Clear all conversation history"""
    with open(MEMORY_FILE, "w") as f:
        json.dump([], f)
