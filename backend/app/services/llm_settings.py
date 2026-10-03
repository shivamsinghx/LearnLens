"""Environment-driven LLM / Ollama configuration."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

DEFAULT_LLM_PROVIDER = "ollama"
DEFAULT_LLM_MODEL = "gemma3:4b"
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_LLM_TIMEOUT_SECONDS = 120.0


def get_llm_provider() -> str:
    """Return the configured LLM provider name (currently only ``ollama``)."""
    return os.getenv("LLM_PROVIDER", DEFAULT_LLM_PROVIDER).strip().lower() or DEFAULT_LLM_PROVIDER


def get_llm_model() -> str:
    """Return the configured Gemma model tag for Ollama."""
    return os.getenv("LLM_MODEL", DEFAULT_LLM_MODEL).strip() or DEFAULT_LLM_MODEL


def get_ollama_base_url() -> str:
    """Return the Ollama HTTP base URL (no trailing slash)."""
    raw = os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL).strip()
    url = raw or DEFAULT_OLLAMA_BASE_URL
    return url.rstrip("/")


def get_llm_timeout_seconds() -> float:
    """Return the HTTP timeout for LLM generation requests."""
    raw = os.getenv("LLM_TIMEOUT_SECONDS", "").strip()
    if not raw:
        return DEFAULT_LLM_TIMEOUT_SECONDS
    try:
        value = float(raw)
    except ValueError as exc:
        raise RuntimeError(
            "LLM_TIMEOUT_SECONDS must be a positive number "
            f"(got {raw!r})."
        ) from exc
    if value <= 0:
        raise RuntimeError("LLM_TIMEOUT_SECONDS must be > 0.")
    return value
