import json
from urllib.error import URLError

from agent import langfuse_probe


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
    monkeypatch.setattr(langfuse_probe, "_send_ingestion", lambda events: sent.append(events))

    probe = langfuse_probe.LangfuseGenerationProbe(
        provider="openrouter",
        model="google/gemini-2.5-flash",
        base_url="https://openrouter.ai/api/v1",
        streaming=True,
    )
    probe.finish(status="success")

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
    assert "latency_ms" in metadata


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
