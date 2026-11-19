import os
import time
from functools import lru_cache

from langchain_community.llms import Ollama
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

from config.paths import load_backend_env

load_backend_env()

def clear_llm_cache():
    get_groq_llm.cache_clear()
    get_gemini_llm.cache_clear()
    get_openrouter_llm.cache_clear()
    get_ollama_llm.cache_clear()
    _PROVIDER_FAILURES.clear()


PROVIDER_COOLDOWN_SECONDS = int(os.getenv("LLM_PROVIDER_COOLDOWN_SECONDS", "300"))
_PROVIDER_FAILURES: dict[str, float] = {}


def _has_env(name: str) -> bool:
    value = os.getenv(name, "").strip()
    return bool(value)


@lru_cache(maxsize=1)
def get_groq_llm():
    return ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        temperature=0,
        max_tokens=1024,
    )


@lru_cache(maxsize=1)
def get_openrouter_llm():
    return ChatOpenAI(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        model=os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3-nano-30b-a3b:free"),
        temperature=0,
        max_tokens=1024,
    )


@lru_cache(maxsize=1)
def get_ollama_llm():
    return Ollama(
        model=os.getenv("OLLAMA_MODEL", "llama3.1:8b"),
        temperature=0,
    )

@lru_cache(maxsize=1)
def get_gemini_llm():
    return ChatGoogleGenerativeAI(
        google_api_key=os.getenv("GEMINI_API_KEY"),
        model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
        temperature=0,
        max_output_tokens=1024,
    )


def _tool_candidates():
    candidates = []
    if _has_env("GEMINI_API_KEY"):
        candidates.append(("Gemini", get_gemini_llm))
    if _has_env("GROQ_API_KEY"):
        candidates.append(("Groq", get_groq_llm))
    if _has_env("OPENAI_API_KEY"):
        candidates.append(("OpenAI", get_openai_llm))
    if _has_env("OPENROUTER_API_KEY"):
        candidates.append(("OpenRouter", get_openrouter_llm))
    return candidates

def _all_candidates():
    candidates = list(_tool_candidates())
    candidates.append(("Ollama", get_ollama_llm))
    return candidates


def _is_in_cooldown(provider_name: str) -> bool:
    failed_at = _PROVIDER_FAILURES.get(provider_name)
    if failed_at is None:
        return False
    return (time.time() - failed_at) < PROVIDER_COOLDOWN_SECONDS


def mark_provider_failed(provider_name: str, exc: Exception | None = None) -> None:
    _PROVIDER_FAILURES[provider_name] = time.time()
    if exc is not None:
        print(f"Provider {provider_name} marked failed: {exc}")


def mark_provider_healthy(provider_name: str) -> None:
    _PROVIDER_FAILURES.pop(provider_name, None)


def get_llm(need_tools: bool = True, exclude: set[str] | None = None):
    """
    Return the best available provider.

    When a provider fails at runtime, it is put on cooldown for a few minutes
    so the backend can fail over instead of repeatedly picking the same dead path.
    """
    exclude = exclude or set()
    candidates = _tool_candidates() if need_tools else _all_candidates()

    if not candidates:
        if need_tools:
            raise RuntimeError(
                "No tool-capable LLM provider is configured. Set GROQ_API_KEY or OPENROUTER_API_KEY."
            )
        return get_ollama_llm(), "Ollama"

    preferred = [
        (provider_name, provider_factory)
        for provider_name, provider_factory in candidates
        if provider_name not in exclude and not _is_in_cooldown(provider_name)
    ]

    fallback = [
        (provider_name, provider_factory)
        for provider_name, provider_factory in candidates
        if provider_name not in exclude and provider_name not in {name for name, _ in preferred}
    ]

    ordered_candidates = preferred or fallback

    if not ordered_candidates:
        if need_tools:
            raise RuntimeError("No available tool-capable LLM providers remain after exclusions/cooldowns.")
        return get_ollama_llm(), "Ollama"

    errors = []
    for provider_name, provider_factory in ordered_candidates:
        try:
            return provider_factory(), provider_name
        except Exception as exc:
            mark_provider_failed(provider_name, exc)
            errors.append(f"{provider_name}: {exc}")

    if need_tools:
        raise RuntimeError("All tool-capable LLM providers failed to initialize: " + " | ".join(errors))

    return get_ollama_llm(), "Ollama"
