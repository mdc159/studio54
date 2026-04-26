"""Minimal caller-side Langfuse ingestion for Hermes model calls."""

from __future__ import annotations

import base64
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


def _env_first(*names: str) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return None


def _base_url_host(base_url: str | None) -> str | None:
    if not base_url:
        return None
    parsed = urlparse(base_url)
    return parsed.netloc or parsed.path or None


@dataclass
class LangfuseGenerationProbe:
    """Conservative Langfuse generation probe for one model call."""

    provider: str | None
    model: str | None
    base_url: str | None
    streaming: bool
    api_mode: str | None

    def __post_init__(self) -> None:
        self.host = os.getenv("LANGFUSE_HOST")
        self.public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        self.secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        self.started_at = time.time()
        self.trace_id = _env_first("LANGFUSE_TRACE_ID", "HERMES_RUN_ID") or str(uuid.uuid4())
        self.observation_id = str(uuid.uuid4())
        self.session_id = _env_first("LANGFUSE_SESSION_ID", "HERMES_SESSION_ID")
        self.hermes_run_id = os.getenv("HERMES_RUN_ID")

    @property
    def enabled(self) -> bool:
        return bool(self.host and self.public_key and self.secret_key)

    def finish(self, *, status: str, error: BaseException | None = None) -> None:
        if not self.enabled:
            return

        now = time.time()
        metadata: dict[str, Any] = {
            "provider": self.provider,
            "model": self.model,
            "base_url_host": _base_url_host(self.base_url),
            "streaming": self.streaming,
            "status": status,
            "latency_ms": round((now - self.started_at) * 1000, 2),
            "api_mode": self.api_mode,
        }
        if self.hermes_run_id:
            metadata["hermes_run_id"] = self.hermes_run_id
        if self.session_id:
            metadata["session_id"] = self.session_id
        if error is not None:
            metadata["error_class"] = error.__class__.__name__

        self._ingest(metadata=metadata, ended_at=now)

    def _ingest(self, *, metadata: dict[str, Any], ended_at: float) -> None:
        trace_body: dict[str, Any] = {
            "id": self.trace_id,
            "name": "hermes.model_call",
            "metadata": {
                "hermes_run_id": self.hermes_run_id,
                "provider": self.provider,
            },
        }
        if self.session_id:
            trace_body["sessionId"] = self.session_id

        observation_body: dict[str, Any] = {
            "id": self.observation_id,
            "traceId": self.trace_id,
            "type": "GENERATION",
            "name": "openai.chat.completions",
            "startTime": _iso_utc(self.started_at),
            "endTime": _iso_utc(ended_at),
            "model": self.model,
            "metadata": metadata,
        }

        payload = {
            "batch": [
                {
                    "id": str(uuid.uuid4()),
                    "type": "trace-create",
                    "timestamp": _iso_utc(self.started_at),
                    "body": trace_body,
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "observation-create",
                    "timestamp": _iso_utc(ended_at),
                    "body": observation_body,
                },
            ]
        }
        url = self.host.rstrip("/") + "/api/public/ingestion"
        auth = base64.b64encode(f"{self.public_key}:{self.secret_key}".encode("utf-8")).decode("ascii")
        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Basic {auth}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=2.0) as response:
                response.read()
        except (OSError, URLError) as exc:
            logger.warning("Langfuse ingestion failed: %s", exc)


def _iso_utc(timestamp: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(timestamp)) + f".{int(timestamp % 1 * 1000):03d}Z"
