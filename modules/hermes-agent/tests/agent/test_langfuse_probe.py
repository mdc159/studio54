import json
from urllib.error import URLError

import pytest

from agent import langfuse_probe


@pytest.fixture(autouse=True)
def clear_langfuse_env(monkeypatch):
    for name in (
        "LANGFUSE_HOST",
        "LANGFUSE_PUBLIC_KEY",
        "LANGFUSE_SECRET_KEY",
        "LANGFUSE_TRACE_ID",
        "LANGFUSE_SESSION_ID",
        "LANGFUSE_CAPTURE_CONTENT",
        "LANGFUSE_CONTENT_MAX_CHARS",
        "HERMES_RUN_ID",
        "HERMES_SESSION_ID",
        "PAPERCLIP_RUN_ID",
        "PAPERCLIP_COMPANY_ID",
        "PAPERCLIP_AGENT_ID",
        "PAPERCLIP_TASK_ID",
    ):
        monkeypatch.delenv(name, raising=False)


def test_langfuse_probe_noops_without_config(monkeypatch):
    sent = []
    monkeypatch.setattr(langfuse_probe, "_send_ingestion", lambda events: sent.append(events))

    probe = langfuse_probe.LangfuseGenerationProbe(
        provider="openrouter",
        model="google/gemini-2.5-flash",
        base_url="https://openrouter.ai/api/v1",
        streaming=False,
    )
    probe.finish(status="success")

    assert sent == []


def test_langfuse_probe_emits_conservative_generation_metadata(monkeypatch):
    sent = []
    monkeypatch.setenv("LANGFUSE_HOST", "http://127.0.0.1:3000")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    monkeypatch.setenv("LANGFUSE_TRACE_ID", "trace-123")
    monkeypatch.setenv("LANGFUSE_SESSION_ID", "session-123")
    monkeypatch.setenv("HERMES_RUN_ID", "run-123")
    monkeypatch.setenv("PAPERCLIP_RUN_ID", "paperclip-run-123")
    monkeypatch.setenv("PAPERCLIP_COMPANY_ID", "company-123")
    monkeypatch.setenv("PAPERCLIP_AGENT_ID", "agent-123")
    monkeypatch.setenv("PAPERCLIP_TASK_ID", "task-123")
    monkeypatch.setattr(langfuse_probe, "_send_ingestion", lambda events: sent.append(events))

    messages = [{"role": "user", "content": "hello"}]
    probe = langfuse_probe.LangfuseGenerationProbe(
        provider="openrouter",
        model="google/gemini-2.5-flash",
        base_url="https://openrouter.ai/api/v1",
        streaming=True,
        input=messages,
    )
    probe.finish(status="success", output="hi there")

    assert len(sent) == 1
    trace, observation = sent[0]
    assert trace["type"] == "trace-create"
    assert trace["body"]["id"] == "trace-123"
    assert trace["body"]["sessionId"] == "session-123"
    assert observation["type"] == "observation-create"
    assert observation["body"]["traceId"] == "trace-123"
    assert observation["body"]["type"] == "GENERATION"
    assert observation["body"]["name"] == "openai.chat.completions"
    assert "input" not in observation["body"]
    assert "output" not in observation["body"]

    metadata = observation["body"]["metadata"]
    assert metadata["provider"] == "openrouter"
    assert metadata["model"] == "google/gemini-2.5-flash"
    assert metadata["base_url_host"] == "openrouter.ai"
    assert metadata["streaming"] is True
    assert metadata["status"] == "success"
    assert metadata["hermes_run_id"] == "run-123"
    assert metadata["paperclip_run_id"] == "paperclip-run-123"
    assert metadata["paperclip_company_id"] == "company-123"
    assert metadata["paperclip_agent_id"] == "agent-123"
    assert metadata["paperclip_task_id"] == "task-123"
    assert metadata["content_capture_enabled"] is False
    assert "latency_ms" in metadata


def test_langfuse_trace_id_precedence_includes_paperclip_run_id(monkeypatch):
    monkeypatch.setenv("LANGFUSE_HOST", "http://127.0.0.1:3000")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    monkeypatch.setenv("LANGFUSE_TRACE_ID", "trace-123")
    monkeypatch.setenv("HERMES_RUN_ID", "hermes-123")
    monkeypatch.setenv("PAPERCLIP_RUN_ID", "paperclip-123")
    assert _probe_trace_id() == "trace-123"

    monkeypatch.delenv("LANGFUSE_TRACE_ID")
    assert _probe_trace_id() == "hermes-123"

    monkeypatch.delenv("HERMES_RUN_ID")
    assert _probe_trace_id() == "paperclip-123"


def _probe_trace_id() -> str:
    return langfuse_probe.LangfuseGenerationProbe(
        provider="openrouter",
        model="model",
        base_url="https://example.test/v1",
        streaming=False,
    ).trace_id


def test_langfuse_probe_captures_content_when_explicitly_enabled(monkeypatch):
    sent = []
    monkeypatch.setenv("LANGFUSE_HOST", "http://127.0.0.1:3000")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    monkeypatch.setenv("LANGFUSE_CAPTURE_CONTENT", "true")
    monkeypatch.setattr(langfuse_probe, "_send_ingestion", lambda events: sent.append(events))

    messages = [{"role": "user", "content": "prompt"}]
    probe = langfuse_probe.LangfuseGenerationProbe(
        provider="openrouter",
        model="model",
        base_url="https://example.test/v1",
        streaming=False,
        input=messages,
    )
    probe.finish(status="success", output="assistant output")

    observation = sent[0][1]["body"]
    assert observation["input"] == messages
    assert observation["output"] == "assistant output"
    assert observation["metadata"]["content_capture_enabled"] is True


def test_langfuse_probe_omits_content_by_default_and_when_disabled(monkeypatch):
    sent = []
    monkeypatch.setenv("LANGFUSE_HOST", "http://127.0.0.1:3000")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    monkeypatch.setattr(langfuse_probe, "_send_ingestion", lambda events: sent.append(events))

    probe = langfuse_probe.LangfuseGenerationProbe(
        provider="openrouter",
        model="model",
        base_url="https://example.test/v1",
        streaming=False,
        input=[{"role": "user", "content": "secret prompt"}],
    )
    probe.finish(status="success", output="secret output")

    observation = sent[0][1]["body"]
    assert "input" not in observation
    assert "output" not in observation
    assert observation["metadata"]["content_capture_enabled"] is False

    sent.clear()
    monkeypatch.setenv("LANGFUSE_CAPTURE_CONTENT", "false")
    probe = langfuse_probe.LangfuseGenerationProbe(
        provider="openrouter",
        model="model",
        base_url="https://example.test/v1",
        streaming=False,
        input=[{"role": "user", "content": "secret prompt"}],
    )
    probe.finish(status="success", output="secret output")

    observation = sent[0][1]["body"]
    assert "input" not in observation
    assert "output" not in observation
    assert observation["metadata"]["content_capture_enabled"] is False


def test_langfuse_probe_truncates_content_and_records_metadata(monkeypatch):
    sent = []
    monkeypatch.setenv("LANGFUSE_HOST", "http://127.0.0.1:3000")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    monkeypatch.setenv("LANGFUSE_CAPTURE_CONTENT", "true")
    monkeypatch.setenv("LANGFUSE_CONTENT_MAX_CHARS", "10")
    monkeypatch.setattr(langfuse_probe, "_send_ingestion", lambda events: sent.append(events))

    probe = langfuse_probe.LangfuseGenerationProbe(
        provider="openrouter",
        model="model",
        base_url="https://example.test/v1",
        streaming=False,
        input=[{"role": "user", "content": "0123456789abcdef"}],
    )
    probe.finish(status="success", output="0123456789abcdef")

    observation = sent[0][1]["body"]
    metadata = observation["metadata"]
    assert observation["input"] == '[{"content'
    assert observation["output"] == "0123456789"
    assert metadata["input_truncated"] is True
    assert metadata["output_truncated"] is True
    assert metadata["input_max_chars"] == 10
    assert metadata["output_max_chars"] == 10


def test_langfuse_probe_records_stream_partial_metadata(monkeypatch):
    sent = []
    monkeypatch.setenv("LANGFUSE_HOST", "http://127.0.0.1:3000")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    monkeypatch.setattr(langfuse_probe, "_send_ingestion", lambda events: sent.append(events))

    probe = langfuse_probe.LangfuseGenerationProbe(
        provider="openrouter",
        model="model",
        base_url="https://example.test/v1",
        streaming=True,
    )
    probe.finish(
        status="error",
        error=RuntimeError("stream failed"),
        output="partial text",
        metadata={
            "partial_output": True,
            "finish_reason": "error",
            "stream_attempt": 2,
        },
    )

    metadata = sent[0][1]["body"]["metadata"]
    assert metadata["partial_output"] is True
    assert metadata["finish_reason"] == "error"
    assert metadata["stream_attempt"] == 2
    assert metadata["error_class"] == "RuntimeError"


def test_langfuse_ingestion_swallow_network_errors(monkeypatch):
    monkeypatch.setenv("LANGFUSE_HOST", "http://127.0.0.1:3000")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")

    def fail(*args, **kwargs):
        raise URLError("offline")

    monkeypatch.setattr(langfuse_probe, "urlopen", fail)
    langfuse_probe._send_ingestion([{"type": "trace-create", "body": {}}])


def test_langfuse_ingestion_uses_basic_auth_and_batch(monkeypatch):
    captured = {}
    monkeypatch.setenv("LANGFUSE_HOST", "http://127.0.0.1:3000/")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")

    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["auth"] = request.headers["Authorization"]
        captured["body"] = json.loads(request.data.decode())
        return Response()

    monkeypatch.setattr(langfuse_probe, "urlopen", fake_urlopen)
    langfuse_probe._send_ingestion([{"type": "observation-create"}])

    assert captured["url"] == "http://127.0.0.1:3000/api/public/ingestion"
    assert captured["timeout"] == 2.0
    assert captured["auth"].startswith("Basic ")
    assert captured["body"] == {"batch": [{"type": "observation-create"}]}
