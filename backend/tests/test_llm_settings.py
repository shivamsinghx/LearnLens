from __future__ import annotations

import pytest

from app.services import llm_settings


def test_llm_settings_defaults(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_TIMEOUT_SECONDS", raising=False)

    assert llm_settings.get_llm_provider() == "ollama"
    assert llm_settings.get_llm_model() == "gemma3:4b"
    assert llm_settings.get_ollama_base_url() == "http://localhost:11434"
    assert llm_settings.get_llm_timeout_seconds() == 120.0


def test_llm_settings_from_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LLM_PROVIDER", "OLLAMA")
    monkeypatch.setenv("LLM_MODEL", "gemma3:1b")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/")
    monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "90")

    assert llm_settings.get_llm_provider() == "ollama"
    assert llm_settings.get_llm_model() == "gemma3:1b"
    assert llm_settings.get_ollama_base_url() == "http://127.0.0.1:11434"
    assert llm_settings.get_llm_timeout_seconds() == 90.0
