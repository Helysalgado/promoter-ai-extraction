"""Anthropic Messages API adapter.

Implements ``ModelBackend``. Tests inject a fake client; production constructs
the official SDK client only after ``ANTHROPIC_API_KEY`` is present. No network
occurs unless ``generate`` is called with a live client.

Structured outputs use the current Messages shape ``output_config.format``
with ``type: json_schema`` (verified against the official docs and SDK 1.13).
The deprecated ``output_format`` field and the structured-outputs beta header
are not sent.
"""
from __future__ import annotations

import json
import os
from typing import Any, Mapping, Protocol

from promoter_ai_extraction.backends.openai_backend import (
    PROMPT_VERSION,
    SCHEMA_VERSION,
    _PAYLOAD_SCHEMA,
    _build_prompt,
    _is_context_limit_error,
    _map_payload,
    _redact,
    _require_positive_int,
)
from promoter_ai_extraction.extraction import (
    BackendFailure,
    RawPropertyPayload,
    SafeExtractionInput,
)

__all__ = [
    "CONTEXT_WINDOW_TOKENS",
    "DEFAULT_MAX_TOKENS",
    "INPUT_CHAR_BUDGET",
    "MODEL_ID",
    "PUBLISHED_MAX_OUTPUT_TOKENS",
    "AnthropicModelBackend",
]

PROVIDER = "anthropic"
API_NAME = "messages"
MODEL_ID = "claude-sonnet-5-5"
# Adapter default for this baseline. The published ceiling stays 128000.
DEFAULT_MAX_TOKENS = 4_096
# https://platform.claude.com/docs/en/models/sonnet-5-5/overview
CONTEXT_WINDOW_TOKENS = 1_000_000
PUBLISHED_MAX_OUTPUT_TOKENS = 128_000
# The installed SDK retries by default. This adapter does not.
SDK_MAX_RETRIES = 0

_SCHEMA_CHAR_OVERHEAD = len(json.dumps(_PAYLOAD_SCHEMA, separators=(",", ":")))
# Character-length fail-closed bound. Reserves the published max output, so a
# lower ``max_tokens`` does not widen the input budget.
INPUT_CHAR_BUDGET = (
    CONTEXT_WINDOW_TOKENS - PUBLISHED_MAX_OUTPUT_TOKENS - _SCHEMA_CHAR_OVERHEAD
)


class _MessagesClient(Protocol):
    messages: Any


class AnthropicModelBackend:
    """``ModelBackend`` adapter for Anthropic Messages + claude-sonnet-5-5."""

    def __init__(
        self,
        *,
        client: _MessagesClient | None = None,
        environ: Mapping[str, str] | None = None,
        max_output_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> None:
        self._client = client
        self._environ = environ if environ is not None else os.environ
        self._max_tokens = _require_positive_int(max_output_tokens)
        self._common: dict[str, Any] | None = None
        self._by_property: dict[str, dict[str, Any]] = {}

    def reproducibility_metadata(self) -> dict[str, Any]:
        return {
            "common": dict(self._common or {}),
            "by_property": {key: dict(value) for key, value in self._by_property.items()},
        }

    def generate(
        self, safe_input: SafeExtractionInput
    ) -> RawPropertyPayload | BackendFailure:
        secret = (self._environ.get("ANTHROPIC_API_KEY") or "").strip()
        if not secret:
            return _fail("MISSING_CREDENTIAL", "ANTHROPIC_API_KEY is not set.")

        prompt = _build_prompt(safe_input)
        if len(prompt) > INPUT_CHAR_BUDGET:
            return _fail(
                "DOCUMENT_TOO_LARGE",
                "The SafeExtractionInput exceeds the conservative character "
                "budget reserved from the published claude-sonnet-5-5 context "
                "window; the document was not truncated.",
            )

        request = _build_request(prompt, self._max_tokens)
        self._record(safe_input.property.value, request, snapshot=None)

        try:
            client = self._client or _live_client(secret)
            response = client.messages.create(**request)
        except TimeoutError:
            return _fail("TIMEOUT", "The Anthropic Messages API call timed out.")
        except Exception as exc:
            return _map_provider_exception(exc, secret)

        snapshot = getattr(response, "model", None)
        self._record(
            safe_input.property.value,
            request,
            snapshot=snapshot if isinstance(snapshot, str) else None,
        )
        classified = _classify_stop(response)
        if classified is not None:
            return classified
        output_text = _output_text(response)
        if output_text is None or not output_text.strip():
            return _fail("MALFORMED_RESPONSE", "The Messages API returned no JSON text.")
        try:
            parsed = json.loads(output_text)
        except json.JSONDecodeError:
            return _fail("MALFORMED_RESPONSE", "The Messages API output was not valid JSON.")
        mapped = _map_payload(parsed)
        if isinstance(mapped, BackendFailure):
            return BackendFailure(code=mapped.code, message=_redact(mapped.message, secret))
        return mapped

    def _record(
        self,
        property_label: str,
        request: dict[str, Any],
        *,
        snapshot: str | None,
    ) -> None:
        recorded = _fingerprint(request, snapshot=snapshot)
        self._common = recorded["common"]
        self._by_property[property_label] = recorded["by_property"]


def _live_client(secret: str) -> Any:
    from anthropic import Anthropic

    return Anthropic(api_key=secret, max_retries=SDK_MAX_RETRIES)


def _build_request(prompt: str, max_tokens: int) -> dict[str, Any]:
    return {
        "model": MODEL_ID,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
        "output_config": {
            "format": {
                "type": "json_schema",
                "schema": _PAYLOAD_SCHEMA,
            }
        },
    }


def _fingerprint(request: dict[str, Any], *, snapshot: str | None) -> dict[str, Any]:
    fmt = request["output_config"]["format"]
    cap = request["max_tokens"]
    return {
        "common": {
            "provider": PROVIDER,
            "model": MODEL_ID,
            "api": API_NAME,
            "prompt_version": PROMPT_VERSION,
            "schema_version": SCHEMA_VERSION,
            "generation": {
                "max_tokens": cap,
                "max_output_tokens": cap,
                "max_retries": SDK_MAX_RETRIES,
                "output_format": fmt["type"],
                "input_char_budget": INPUT_CHAR_BUDGET,
            },
        },
        "by_property": {
            "model_snapshot": snapshot,
            "system_fingerprint": None,
        },
    }


def _classify_stop(response: object) -> BackendFailure | None:
    reason = _stop_reason(response)
    if reason == "max_tokens":
        return _fail(
            "INCOMPLETE_RESPONSE",
            "The Messages API stopped because max_tokens was reached.",
        )
    if reason == "refusal":
        return _fail(
            "PROVIDER_ERROR",
            "The Messages API refused the request.",
        )
    if reason == "model_context_window_exceeded":
        return _fail(
            "DOCUMENT_TOO_LARGE",
            "The provider rejected the request as larger than the model context window.",
        )
    if reason != "end_turn":
        return _fail(
            "INCOMPLETE_RESPONSE",
            "The Messages API did not finish the response.",
        )
    return None


def _stop_reason(response: object) -> str | None:
    raw = getattr(response, "stop_reason", None)
    if raw is None:
        return None
    value = getattr(raw, "value", raw)
    if isinstance(value, str):
        return value
    return None


def _output_text(response: object) -> str | None:
    content = getattr(response, "content", None)
    if not isinstance(content, list):
        return None
    parts: list[str] = []
    for block in content:
        if getattr(block, "type", None) != "text":
            continue
        text = getattr(block, "text", None)
        if isinstance(text, str):
            parts.append(text)
    if not parts:
        return None
    return "".join(parts)


def _map_provider_exception(exc: BaseException, secret: str) -> BackendFailure:
    name = type(exc).__name__
    if "timeout" in name.lower():
        return _fail("TIMEOUT", "The Anthropic Messages API call timed out.")
    status = getattr(exc, "status_code", None)
    if name == "RateLimitError" or status == 429:
        return _fail(
            "RATE_LIMIT",
            f"The Anthropic Messages API rate limit was reached ({name}).",
        )
    if status == 400 and _mentions_schema(exc):
        return _fail(
            "SCHEMA_VIOLATION",
            "The Anthropic Messages API rejected the output schema.",
        )
    if _is_context_limit_error(exc):
        return _fail(
            "DOCUMENT_TOO_LARGE",
            "The provider rejected the request as larger than the model context window.",
        )
    return _fail("PROVIDER_ERROR", f"The Anthropic Messages API failed ({name}).")


def _mentions_schema(exc: BaseException) -> bool:
    chunks = [type(exc).__name__, str(exc)]
    body = getattr(exc, "body", None)
    if isinstance(body, str):
        chunks.append(body)
    elif isinstance(body, dict):
        chunks.append(json.dumps(body))
    return "schema" in " ".join(chunks).lower()


def _fail(code: str, message: str) -> BackendFailure:
    return BackendFailure(code=code, message=message)
