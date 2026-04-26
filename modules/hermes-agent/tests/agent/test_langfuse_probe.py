import base64
import json
from urllib.error import URLError

from agent.langfuse_probe import LangfuseGenerationProbe


def test_langfuse_probe_noops_without_config(monkeypatch):
    monkeypatch.delenv("LANGFUSE_HOST", raising=False)
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)

    probe = LangfuseGenerationProbe(
        provider="openrouter",
        model="google/gemini-2.5-flash",
        base_url="https://openrouter.ai/api/v1",
        streaming=False,
        api_mode="chat_completions",
    )

    assert probe.enabled is False
    probe.finish(status="success")


def test_langfuse_probe_emits_conservative_generation_metadata(monkeypatch):
    requests = []

    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b"{}"

    def fake_urlopen(request, timeout):
        requests.append((request, timeout))
        return _Response()

    monkeypatch.setenv("LANGFUSE_HOST", "https://donna.tailfedd3b.ts.net:8446/")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    monkeypatch.setenv("LANGFUSE_TRACE_ID", "trace-123")
    monkeypatch.setenv("LANGFUSE_SESSION_ID", "session-123")
    monkeypatch.setenv("HERMES_RUN_ID", "run-123")
    monkeypatch.setattr("agent.langfuse_probe.urlopen", fake_urlopen)

    probe = LangfuseGenerationProbe(
        provider="openrouter",
        model="google/gemini-2.5-flash",
        base_url="https://openrouter.ai/api/v1",
        streaming=True,
        api_mode="chat_completions",
    )
    probe.finish(status="success")

    assert len(requests) == 1
    request, timeout = requests[0]
    assert timeout == 2.0
    assert request.full_url == "https://donna.tailfedd3b.ts.net:8446/api/public/ingestion"

    payload = json.loads(request.data.decode("utf-8"))
    trace_event, observation_event = payload["batch"]
    assert trace_event["type"] == "trace-create"
    assert trace_event["body"]["id"] == "trace-123"
    assert trace_event["body"]["sessionId"] == "session-123"

    observation = observation_event["body"]
    assert observation_event["type"] == "observation-create"
    assert observation["traceId"] == "trace-123"
    assert observation["type"] == "GENERATION"
    assert observation["name"] == "openai.chat.completions"
    assert observation["model"] == "google/gemini-2.5-flash"
    assert "input" not in observation
    assert "output" not in observation
    assert observation["metadata"] == {
        "provider": "openrouter",
        "model": "google/gemini-2.5-flash",
        "base_url_host": "openrouter.ai",
        "streaming": True,
        "status": "success",
        "latency_ms": observation["metadata"]["latency_ms"],
        "api_mode": "chat_completions",
        "hermes_run_id": "run-123",
        "session_id": "session-123",
    }


def test_langfuse_probe_swallow_ingestion_errors(monkeypatch):
    def fake_urlopen(request, timeout):
        raise URLError("offline")

    monkeypatch.setenv("LANGFUSE_HOST", "http://127.0.0.1:3000")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    monkeypatch.setattr("agent.langfuse_probe.urlopen", fake_urlopen)

    probe = LangfuseGenerationProbe(
        provider="openrouter",
        model="google/gemini-2.5-flash",
        base_url="https://openrouter.ai/api/v1",
        streaming=False,
        api_mode="chat_completions",
    )

    probe.finish(status="error", error=RuntimeError("boom"))


def test_langfuse_probe_uses_basic_auth_and_batch(monkeypatch):
    requests = []

    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b"{}"

    def fake_urlopen(request, timeout):
        requests.append(request)
        return _Response()

    monkeypatch.setenv("LANGFUSE_HOST", "http://127.0.0.1:3000")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    monkeypatch.setattr("agent.langfuse_probe.urlopen", fake_urlopen)

    probe = LangfuseGenerationProbe(
        provider="openrouter",
        model="model",
        base_url="https://example.test/v1",
        streaming=False,
        api_mode="chat_completions",
    )
    probe.finish(status="success")

    request = requests[0]
    expected_auth = base64.b64encode(b"pk-test:sk-test").decode("ascii")
    assert request.headers["Authorization"] == f"Basic {expected_auth}"
    assert json.loads(request.data.decode("utf-8"))["batch"][1]["body"]["type"] == "GENERATION"
