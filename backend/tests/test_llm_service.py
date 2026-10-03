from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.services.llm_service import (
    SYSTEM_PROMPT,
    LLMError,
    LLMService,
    OllamaClient,
    OllamaConfig,
    build_user_prompt,
)
from tests.fakes import FakeLLMClient


def test_generate_answer_uses_system_and_context():
    client = FakeLLMClient(answer="Grounded answer.")
    service = LLMService(client=client)
    answer = service.generate_answer(
        context="<<<STUDY_MATERIAL_CONTEXT>>>\nSOURCE 1\n...\n<<<END_STUDY_MATERIAL_CONTEXT>>>",
        question="What is normalization?",
    )
    assert answer == "Grounded answer."
    assert len(client.generate_calls) == 1
    call = client.generate_calls[0]
    assert call["system"] == SYSTEM_PROMPT
    assert "STUDY_MATERIAL_CONTEXT" in call["user"]
    assert "What is normalization?" in call["user"]


def test_build_user_prompt_keeps_question_and_context_separate():
    prompt = build_user_prompt(context="CTX", question="  Why indexes?  ")
    assert "CTX" in prompt
    assert "Why indexes?" in prompt


def test_invalid_provider_rejected(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    with pytest.raises(LLMError) as exc_info:
        LLMService()
    assert exc_info.value.status_code == 500
    assert "Invalid language model configuration" in str(exc_info.value)


def test_ollama_unavailable_connection_error():
    client = OllamaClient(
        OllamaConfig(base_url="http://127.0.0.1:9", model="gemma3:4b", timeout_seconds=1.0)
    )
    with patch("app.services.llm_service.httpx.post", side_effect=httpx.ConnectError("boom")):
        with pytest.raises(LLMError) as exc_info:
            client.generate(system="sys", user="user")
    assert exc_info.value.status_code == 503
    assert "unavailable" in str(exc_info.value).lower()
    assert "127.0.0.1" not in str(exc_info.value)


def test_ollama_timeout():
    client = OllamaClient(
        OllamaConfig(base_url="http://localhost:11434", model="gemma3:4b", timeout_seconds=1.0)
    )
    with patch(
        "app.services.llm_service.httpx.post",
        side_effect=httpx.TimeoutException("slow"),
    ):
        with pytest.raises(LLMError) as exc_info:
            client.generate(system="sys", user="user")
    assert exc_info.value.status_code == 504


def test_ollama_model_not_found():
    client = OllamaClient(
        OllamaConfig(base_url="http://localhost:11434", model="gemma3:4b", timeout_seconds=5.0)
    )
    response = MagicMock()
    response.status_code = 404
    response.text = "model not found"
    response.json.return_value = {"error": "model not found"}
    with patch("app.services.llm_service.httpx.post", return_value=response):
        with pytest.raises(LLMError) as exc_info:
            client.generate(system="sys", user="user")
    assert "not available" in str(exc_info.value).lower()


def test_ollama_check_ready_model_missing():
    client = OllamaClient(
        OllamaConfig(base_url="http://localhost:11434", model="gemma3:4b", timeout_seconds=5.0)
    )
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"models": [{"name": "llama3.2:3b"}]}
    with patch("app.services.llm_service.httpx.get", return_value=response):
        with pytest.raises(LLMError) as exc_info:
            client.check_ready()
    assert "not available" in str(exc_info.value).lower()


def test_ollama_check_ready_success():
    client = OllamaClient(
        OllamaConfig(base_url="http://localhost:11434", model="gemma3:4b", timeout_seconds=5.0)
    )
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"models": [{"name": "gemma3:4b"}]}
    with patch("app.services.llm_service.httpx.get", return_value=response):
        payload = client.check_ready()
    assert payload["status"] == "ready"
    assert payload["model"] == "gemma3:4b"


def test_ollama_successful_generate_parses_message():
    client = OllamaClient(
        OllamaConfig(base_url="http://localhost:11434", model="gemma3:4b", timeout_seconds=5.0)
    )
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"message": {"role": "assistant", "content": "  Hello student.  "}}
    with patch("app.services.llm_service.httpx.post", return_value=response):
        text = client.generate(system="sys", user="user")
    assert text == "Hello student."
