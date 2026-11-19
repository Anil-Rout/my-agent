# memory.py — Pinecone vector memory
# Agent remembers ALL conversations intelligently
# Uses semantic search — finds relevant memories even if wording is different

from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from datetime import datetime
import uuid
import os

from config.paths import load_backend_env


load_backend_env()

pc = None
index = None
embedder = None


def get_index():
    global pc, index

    if index is not None:
        return index

    api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX", "agent-memory")

    if not api_key:
        return None

    try:
        pc = Pinecone(api_key=api_key)
        index = pc.Index(index_name)
        return index
    except Exception as e:
        print(f"Memory index init error: {e}")
        return None


def get_embedder():
    global embedder

    if embedder is not None:
        return embedder

    try:
        embedder = SentenceTransformer("all-mpnet-base-v2")
        return embedder
    except Exception as e:
        print(f"Embedder init error: {e}")
        return None


def save_memory(text: str, role: str, metadata: dict | None = None):
    """
    Save a message to Pinecone memory.
    role = 'user' or 'assistant'
    """
    try:
        current_index = get_index()
        if not current_index:
            return

        current_embedder = get_embedder()
        if not current_embedder:
            return

        vector = current_embedder.encode(text).tolist()
        current_index.upsert(vectors=[{
            "id": str(uuid.uuid4()),
            "values": vector,
            "metadata": {
                "text": text,
                "role": role,
                "timestamp": datetime.now().isoformat(),
                **(metadata or {})
            }
        }])
    except Exception as e:
        print(f"Memory save error: {e}")


def search_memory(query: str, top_k: int = 5) -> list:
    """
    Search for relevant past memories.
    Returns most semantically similar past conversations.
    """
    try:
        current_index = get_index()
        if not current_index:
            return []

        current_embedder = get_embedder()
        if not current_embedder:
            return []

        vector = current_embedder.encode(query).tolist()
        results = current_index.query(
            vector=vector,
            top_k=top_k,
            include_metadata=True
        )
        return [match.metadata for match in results.matches if match.score > 0.5]
    except Exception as e:
        print(f"Memory search error: {e}")
        return []


def get_relevant_context(query: str) -> str:
    """
    Get relevant past conversations as a context string.
    This is injected into every AI prompt automatically.
    """
    memories = search_memory(query)
    if not memories:
        return ""

    context_lines = []
    for m in memories:
        role = m.get("role", "unknown")
        text = m.get("text", "")
        time = m.get("timestamp", "")[:10]  # Just date
        context_lines.append(f"[{time}] {role}: {text}")

    return "Relevant past context:\n" + "\n".join(context_lines) + "\n"

def clear_all_memory():
    """Clear ALL memories — use carefully!"""
    try:
        current_index = get_index()
        if current_index is None:
            return
        current_index.delete(delete_all=True)
        print("All memories cleared.")
    except Exception as e:
        print(f"Error clearing memory: {e}")
