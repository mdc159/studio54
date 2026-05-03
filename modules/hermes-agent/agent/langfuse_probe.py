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


def _env_first(*names: str) -> str:
    for name in names:
        value = os.getenv(name, "").strip()
        if value:
            return value
    return ""


def _capture_content_enabled() -> bool:
    value = os.getenv("LANGFUSE_CAPTURE_CONTENT", "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _content_max_chars() -> int:
    raw = os.getenv("LANGFUSE_CONTENT_MAX_CHARS", "").strip()
    if not raw:
        return 32768
    try:
        parsed = int(raw)
    except ValueError:
        return 32768
    return max(parsed, 0)


def _capped_payload(value: Any, *, max_chars: int, label: str) -> tuple[Any, dict[str, Any]]:
    if value is None:
        return None, {}

    if isinstance(value, str):
        text = value
        payload: Any = text
    else:
        try:
            text = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
            payload = value
        except (TypeError, ValueError):
            text = str(value)
            payload = text

    if len(text) > max_chars:
        return text[:max_chars], {
            f"{label}_truncated": True,
            f"{label}_original_chars": len(text),
            f"{label}_max_chars": max_chars,
        }
    return payload, {f"{label}_chars": len(text)}


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
        input: Any | None = None,
    ) -> None:
        self._enabled = configured()
        self.enabled = self._enabled
        self.provider = provider or "unknown"
        self.model = model or ""
        self.base_url = base_url or ""
        self.streaming = bool(streaming)
        self.api_mode = api_mode or "chat_completions"
        self.input = input
        self.capture_content = _capture_content_enabled()
        self.content_max_chars = _content_max_chars()
        self.trace_id = _env_first("LANGFUSE_TRACE_ID", "HERMES_RUN_ID", "PAPERCLIP_RUN_ID") or str(uuid.uuid4())
        self.session_id = _env_first("LANGFUSE_SESSION_ID", "HERMES_SESSION_ID")
        self.observation_id = str(uuid.uuid4())
        self.start_iso = _utcnow_iso()
        self._start = time.monotonic()

    def finish(
        self,
        *,
        status: str,
        error: BaseException | None = None,
        output: Any | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Emit a generation observation, swallowing all ingestion failures."""
        if not self._enabled:
            return
        try:
            self._finish(
                status=status,
                error=error,
                output=output,
                extra_metadata=metadata,
            )
        except Exception as exc:  # noqa: BLE001 - tracing must never fail a run.
            logger.warning("langfuse probe failed: %s", exc)

    def _finish(
        self,
        *,
        status: str,
        error: BaseException | None,
        output: Any | None,
        extra_metadata: dict[str, Any] | None,
    ) -> None:
        end_iso = _utcnow_iso()
        metadata: dict[str, Any] = {
            "provider": self.provider,
            "model": self.model,
            "base_url_host": base_url_host(self.base_url),
            "streaming": self.streaming,
            "status": status,
            "latency_ms": round((time.monotonic() - self._start) * 1000, 2),
            "api_mode": self.api_mode,
            "content_capture_enabled": self.capture_content,
        }

        for env_name, metadata_name in (
            ("HERMES_RUN_ID", "hermes_run_id"),
            ("PAPERCLIP_RUN_ID", "paperclip_run_id"),
            ("PAPERCLIP_COMPANY_ID", "paperclip_company_id"),
            ("PAPERCLIP_AGENT_ID", "paperclip_agent_id"),
            ("PAPERCLIP_TASK_ID", "paperclip_task_id"),
        ):
            value = os.getenv(env_name, "").strip()
            if value:
                metadata[metadata_name] = value
        if self.session_id:
            metadata["session_id"] = self.session_id
        if error is not None:
            metadata["error_class"] = error.__class__.__name__
        if extra_metadata:
            metadata.update(extra_metadata)

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
        if self.capture_content:
            input_payload, input_metadata = _capped_payload(
                self.input,
                max_chars=self.content_max_chars,
                label="input",
            )
            output_payload, output_metadata = _capped_payload(
                output,
                max_chars=self.content_max_chars,
                label="output",
            )
            metadata.update(input_metadata)
            metadata.update(output_metadata)
            if input_payload is not None:
                observation_body["body"]["input"] = input_payload
            if output_payload is not None:
                observation_body["body"]["output"] = output_payload

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
