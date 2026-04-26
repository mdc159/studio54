"""Minimal caller-side Langfuse probe for Hermes model calls.

This module intentionally uses only the standard library and treats Langfuse
as best-effort observability. Ingestion failures must never affect provider
calls.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


logger = logging.getLogger(__name__)


def _utcnow_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def base_url_host(base_url: str | None) -> str:
    """Return only the host portion of a provider base URL."""
    if not base_url:
        return ""
    parsed = urlparse(str(base_url))
    return parsed.hostname or ""


def configured() -> bool:
    return bool(
        os.getenv("LANGFUSE_HOST", "").strip()
        and os.getenv("LANGFUSE_PUBLIC_KEY", "").strip()
        and os.getenv("LANGFUSE_SECRET_KEY", "").strip()
    )


class LangfuseGenerationProbe:
    """Best-effort Langfuse generation observation for one model call."""

    def __init__(
        self,
        *,
        provider: str,
        model: str,
        base_url: str,
        streaming: bool,
        api_mode: str = "chat_completions",
    ) -> None:
        self._enabled = configured()
        self.provider = provider or "unknown"
        self.model = model or ""
        self.base_url = base_url or ""
        self.streaming = bool(streaming)
        self.api_mode = api_mode or "chat_completions"
        self.trace_id = (
            os.getenv("LANGFUSE_TRACE_ID", "").strip()
            or os.getenv("HERMES_RUN_ID", "").strip()
            or str(uuid.uuid4())
        )
        self.session_id = (
            os.getenv("LANGFUSE_SESSION_ID", "").strip()
            or os.getenv("HERMES_SESSION_ID", "").strip()
        )
        self.observation_id = str(uuid.uuid4())
        self.start_iso = _utcnow_iso()
        self._start = time.monotonic()

    def finish(self, *, status: str, error: BaseException | None = None) -> None:
        """Emit a generation observation, swallowing all ingestion failures."""
        if not self._enabled:
            return

        end_iso = _utcnow_iso()
        metadata: dict[str, Any] = {
            "provider": self.provider,
            "model": self.model,
            "base_url_host": base_url_host(self.base_url),
            "streaming": self.streaming,
            "status": status,
            "latency_ms": round((time.monotonic() - self._start) * 1000, 2),
            "api_mode": self.api_mode,
        }
        run_id = os.getenv("HERMES_RUN_ID", "").strip()
        if run_id:
            metadata["hermes_run_id"] = run_id
        if self.session_id:
            metadata["session_id"] = self.session_id
        if error is not None:
            metadata["error_class"] = error.__class__.__name__

        trace_body: dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "type": "trace-create",
            "timestamp": self.start_iso,
            "body": {
                "id": self.trace_id,
                "timestamp": self.start_iso,
                "name": "hermes-model-call",
                "metadata": {"source": "hermes-runtime"},
            },
        }
        if self.session_id:
            trace_body["body"]["sessionId"] = self.session_id

        observation_body: dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "type": "observation-create",
            "timestamp": end_iso,
            "body": {
                "id": self.observation_id,
                "traceId": self.trace_id,
                "type": "GENERATION",
                "name": "openai.chat.completions",
                "startTime": self.start_iso,
                "endTime": end_iso,
                "model": self.model,
                "level": "DEFAULT" if status == "success" else "ERROR",
                "statusMessage": None if error is None else str(error)[:300],
                "metadata": metadata,
            },
        }

        _send_ingestion([trace_body, observation_body])


def _send_ingestion(events: list[dict[str, Any]]) -> None:
    host = os.getenv("LANGFUSE_HOST", "").strip().rstrip("/")
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "").strip()
    secret_key = os.getenv("LANGFUSE_SECRET_KEY", "").strip()
    if not host or not public_key or not secret_key:
        return

    token = base64.b64encode(f"{public_key}:{secret_key}".encode()).decode()
    request = Request(
        f"{host}/api/public/ingestion",
        data=json.dumps({"batch": events}).encode(),
        headers={
            "authorization": f"Basic {token}",
            "content-type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=2.0) as response:
            if response.status >= 400:
                logger.warning("langfuse ingestion rejected batch: %s", response.status)
    except (OSError, URLError) as exc:
        logger.warning("langfuse ingestion unreachable: %s", exc)
