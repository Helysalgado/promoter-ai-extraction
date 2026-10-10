"""OpenAI Responses API adapter (T038).

Implements ``ModelBackend``. Tests inject a fake client; production constructs
the official SDK client only after ``OPENAI_API_KEY`` is present. No network
occurs unless ``generate`` is called with a live client.
"""
from __future__ import annotations

import json
import os
from typing import Any, Mapping, Protocol

from promoter_ai_extraction.extraction import (
    BackendFailure,
    RawCandidatePayload,
    RawPropertyPayload,
    RawValuePayload,
    SafeExtractionInput,
)
from promoter_ai_extraction.models import ScientificStatus

__all__ = [
    "CONTEXT_WINDOW_TOKENS",
    "INPUT_CHAR_BUDGET",
    "MAX_OUTPUT_TOKENS",
    "MODEL_ID",
    "OpenAIModelBackend",
    "PROMPT_VERSION",
    "SCHEMA_VERSION",
]

PROVIDER = "openai"
API_NAME = "responses"
MODEL_ID = "gpt-6.1-sol"
PROMPT_VERSION = "safe-extraction-v1"
SCHEMA_VERSION = "raw-property-payload-v1"
# Published window for gpt-6.1-sol:
# https://developers.openai.com/api/docs/models/gpt-6.1-sol
CONTEXT_WINDOW_TOKENS = 1_050_000
MAX_OUTPUT_TOKENS = 128_000
# The installed SDK retries by default. This adapter does not.
SDK_MAX_RETRIES = 0

_STATUS_VALUES = [status.value for status in ScientificStatus]
_SCIENTIFIC = frozenset(_STATUS_VALUES)
_TOP_KEYS = frozenset(
    {"status", "values", "candidates", "abstention_reason", "result_evidence"}
)
_VALUE_KEYS = frozenset(
    {"value_raw", "qualifier", "evidence_segment_ids", "evidence_fragments"}
)
_CANDIDATE_KEYS = frozenset(
    {"candidate_raw", "rule_violated", "evidence_segment_id", "evidence_fragment"}
)
_EVIDENCE_KEYS = frozenset({"segment_id", "fragment"})
_CONTEXT_MARKERS = (
    "context_length",
    "context_window",
    "context length",
    "context window",
    "maximum context",
    "max context",
    "token limit",
)

_PAYLOAD_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "status",
        "values",
        "candidates",
        "abstention_reason",
        "result_evidence",
    ],
    "properties": {
        "status": {"type": "string", "enum": _STATUS_VALUES},
        "values": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "value_raw",
                    "qualifier",
                    "evidence_segment_ids",
                    "evidence_fragments",
                ],
                "properties": {
                    "value_raw": {"type": "string"},
                    "qualifier": {"type": ["string", "null"]},
                    "evidence_segment_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "evidence_fragments": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
            },
        },
        "candidates": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "candidate_raw",
                    "rule_violated",
                    "evidence_segment_id",
                    "evidence_fragment",
                ],
                "properties": {
                    "candidate_raw": {"type": "string"},
                    "rule_violated": {"type": "string"},
                    "evidence_segment_id": {"type": ["string", "null"]},
                    "evidence_fragment": {"type": ["string", "null"]},
                },
            },
        },
        "abstention_reason": {"type": ["string", "null"]},
        "result_evidence": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["segment_id", "fragment"],
                "properties": {
                    "segment_id": {"type": "string"},
                    "fragment": {"type": "string"},
                },
            },
        },
    },
}

# Character-length fail-closed bound, not a token count. Reserves the published
# max output and the measured JSON-schema payload that travels with the request.
# Prompt instructions are already inside the prompt string.
_SCHEMA_CHAR_OVERHEAD = len(json.dumps(_PAYLOAD_SCHEMA, separators=(",", ":")))
INPUT_CHAR_BUDGET = CONTEXT_WINDOW_TOKENS - MAX_OUTPUT_TOKENS - _SCHEMA_CHAR_OVERHEAD


class _ResponsesClient(Protocol):
    responses: Any


class OpenAIModelBackend:
    """``ModelBackend`` adapter for OpenAI Responses API + gpt-6.1-sol."""

    def __init__(
        self,
        *,
        client: _ResponsesClient | None = None,
        environ: Mapping[str, str] | None = None,
        max_output_tokens: int = MAX_OUTPUT_TOKENS,
    ) -> None:
        self._client = client
        self._environ = environ if environ is not None else os.environ
        self._max_output_tokens = _require_positive_int(max_output_tokens)
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
        secret = (self._environ.get("OPENAI_API_KEY") or "").strip()
        if not secret:
            return _fail("MISSING_CREDENTIAL", "OPENAI_API_KEY is not set.")

        prompt = _build_prompt(safe_input)
        if len(prompt) > INPUT_CHAR_BUDGET:
            return _fail(
                "DOCUMENT_TOO_LARGE",
                "The SafeExtractionInput exceeds the conservative character "
                "budget reserved from the published gpt-6.1-sol context window; "
                "the document was not truncated.",
            )

        request = _build_request(prompt, self._max_output_tokens)
        self._record_fingerprint(
            safe_input.property.value,
            request,
            snapshot=None,
            system_fingerprint=None,
        )

        try:
            client = self._client or _live_client(secret)
            response = client.responses.create(**request)
        except TimeoutError:
            return _fail("TIMEOUT", "The OpenAI Responses API call timed out.")
        except Exception as exc:
            return _map_provider_exception(exc, secret)

        snapshot = getattr(response, "model", None)
        fingerprint = getattr(response, "system_fingerprint", None)
        self._record_fingerprint(
            safe_input.property.value,
            request,
            snapshot=snapshot if isinstance(snapshot, str) else None,
            system_fingerprint=fingerprint if isinstance(fingerprint, str) else None,
        )
        classified = _classify_response_state(response)
        if classified is not None:
            return classified
        output_text = getattr(response, "output_text", None)
        if not isinstance(output_text, str) or not output_text.strip():
            return _fail("MALFORMED_RESPONSE", "The Responses API returned no JSON text.")
        try:
            parsed = json.loads(output_text)
        except json.JSONDecodeError:
            return _fail("MALFORMED_RESPONSE", "The Responses API output was not valid JSON.")
        mapped = _map_payload(parsed)
        if isinstance(mapped, BackendFailure):
            mapped = BackendFailure(
                code=mapped.code,
                message=_redact(mapped.message, secret),
            )
        return mapped

    def _record_fingerprint(
        self,
        property_label: str,
        request: dict[str, Any],
        *,
        snapshot: str | None,
        system_fingerprint: str | None,
    ) -> None:
        recorded = _fingerprint(
            request, snapshot=snapshot, system_fingerprint=system_fingerprint
        )
        self._common = recorded["common"]
        self._by_property[property_label] = recorded["by_property"]


def _require_positive_int(value: int) -> int:
    """Accept only a positive integer. ``bool`` is rejected as an ``int`` subclass."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError("max_output_tokens must be a positive integer.")
    return value


def _live_client(secret: str) -> Any:
    from openai import OpenAI

    return OpenAI(api_key=secret, max_retries=SDK_MAX_RETRIES)


def _build_prompt(safe_input: SafeExtractionInput) -> str:
    lines = [
        "Extract one promoter property from the supplied document segments only.",
        "Do not use sources outside these segments.",
        f"paper_id: {safe_input.paper_id}",
        f"promoter_name: {safe_input.promoter_name}",
        f"promoter_id: {safe_input.promoter_id or ''}",
        f"paper_gene_synonym: {safe_input.paper_gene_synonym or ''}",
        f"property: {safe_input.property.value}",
        "segments:",
    ]
    for segment in safe_input.document_segments:
        lines.append(
            f"[{segment.segment_id} source_type={segment.source_type} "
            f"location={segment.location or ''}]"
        )
        lines.append(segment.text)
    return "\n".join(lines)


def _build_request(prompt: str, max_output_tokens: int = MAX_OUTPUT_TOKENS) -> dict[str, Any]:
    return {
        "model": MODEL_ID,
        "input": prompt,
        "store": False,
        "truncation": "disabled",
        "max_output_tokens": max_output_tokens,
        "text": {
            "format": {
                "type": "json_schema",
                "name": "raw_property_payload",
                "strict": True,
                "schema": _PAYLOAD_SCHEMA,
            }
        },
    }


def _fingerprint(
    request: dict[str, Any],
    *,
    snapshot: str | None,
    system_fingerprint: str | None,
) -> dict[str, Any]:
    fmt = request["text"]["format"]
    return {
        "common": {
            "provider": PROVIDER,
            "model": MODEL_ID,
            "api": API_NAME,
            "prompt_version": PROMPT_VERSION,
            "schema_version": SCHEMA_VERSION,
            "generation": {
                "max_output_tokens": request["max_output_tokens"],
                "max_retries": SDK_MAX_RETRIES,
                "text_format": fmt["type"],
                "strict": fmt["strict"],
                "store": request["store"],
                "truncation": request["truncation"],
                "input_char_budget": INPUT_CHAR_BUDGET,
            },
        },
        "by_property": {
            "model_snapshot": snapshot,
            "system_fingerprint": system_fingerprint,
        },
    }


def _classify_response_state(response: object) -> BackendFailure | None:
    error = getattr(response, "error", None)
    if error:
        return _fail("PROVIDER_ERROR", "The Responses API returned an error.")
    status = getattr(response, "status", None)
    incomplete = getattr(response, "incomplete_details", None)
    if status == "incomplete" or incomplete:
        return _fail(
            "INCOMPLETE_RESPONSE",
            "The Responses API returned an incomplete response.",
        )
    if status != "completed":
        return _fail("PROVIDER_ERROR", "The Responses API did not complete the response.")
    return None


def _map_payload(parsed: object) -> RawPropertyPayload | BackendFailure:
    if not isinstance(parsed, dict):
        return _fail("SCHEMA_VIOLATION", "Structured output was not an object.")
    extra = set(parsed.keys()) - _TOP_KEYS
    if extra:
        return _fail("SCHEMA_VIOLATION", "Structured output has unexpected fields.")
    if any(key not in parsed for key in _TOP_KEYS):
        return _fail("SCHEMA_VIOLATION", "Structured output is missing required fields.")
    status = parsed["status"]
    if not isinstance(status, str) or status not in _SCIENTIFIC:
        return _fail("SCHEMA_VIOLATION", "Structured output has an invalid status.")
    values = parsed["values"]
    candidates = parsed["candidates"]
    evidence = parsed["result_evidence"]
    if not isinstance(values, list) or not isinstance(candidates, list) or not isinstance(evidence, list):
        return _fail("SCHEMA_VIOLATION", "Structured output collections are not lists.")
    try:
        mapped_values = tuple(_map_value(item) for item in values)
        mapped_candidates = tuple(_map_candidate(item) for item in candidates)
        mapped_evidence = tuple(_map_evidence(item) for item in evidence)
    except (TypeError, KeyError, ValueError):
        return _fail("SCHEMA_VIOLATION", "Structured output fields do not match the payload contract.")
    abstention = parsed["abstention_reason"]
    if abstention is not None and not isinstance(abstention, str):
        return _fail("SCHEMA_VIOLATION", "abstention_reason must be a string or null.")
    return RawPropertyPayload(
        status=status,
        values=mapped_values,
        candidates=mapped_candidates,
        abstention_reason=abstention,
        result_evidence=mapped_evidence,
    )


def _require_object_keys(item: object, allowed: frozenset[str]) -> dict[str, object]:
    if not isinstance(item, dict):
        raise TypeError("object")
    if set(item.keys()) - allowed:
        raise ValueError("unexpected field")
    if any(key not in item for key in allowed):
        raise KeyError("missing field")
    return item


def _require_str_tuple(values: object) -> tuple[str, ...]:
    if not isinstance(values, list):
        raise TypeError("list")
    if any(not isinstance(part, str) for part in values):
        raise TypeError("string item")
    return tuple(values)


def _map_value(item: object) -> RawValuePayload:
    payload = _require_object_keys(item, _VALUE_KEYS)
    value_raw = payload["value_raw"]
    if not isinstance(value_raw, str):
        raise TypeError("value_raw")
    qualifier = payload["qualifier"]
    if qualifier is not None and not isinstance(qualifier, str):
        raise TypeError("qualifier")
    return RawValuePayload(
        value_raw=value_raw,
        qualifier=qualifier,
        evidence_segment_ids=_require_str_tuple(payload["evidence_segment_ids"]),
        evidence_fragments=_require_str_tuple(payload["evidence_fragments"]),
    )


def _map_candidate(item: object) -> RawCandidatePayload:
    payload = _require_object_keys(item, _CANDIDATE_KEYS)
    candidate_raw = payload["candidate_raw"]
    rule_violated = payload["rule_violated"]
    evidence_segment_id = payload["evidence_segment_id"]
    evidence_fragment = payload["evidence_fragment"]
    if not isinstance(candidate_raw, str) or not isinstance(rule_violated, str):
        raise TypeError("candidate strings")
    if evidence_segment_id is not None and not isinstance(evidence_segment_id, str):
        raise TypeError("evidence_segment_id")
    if evidence_fragment is not None and not isinstance(evidence_fragment, str):
        raise TypeError("evidence_fragment")
    return RawCandidatePayload(
        candidate_raw=candidate_raw,
        rule_violated=rule_violated,
        evidence_segment_id=evidence_segment_id,
        evidence_fragment=evidence_fragment,
    )


def _map_evidence(item: object) -> tuple[str, str]:
    payload = _require_object_keys(item, _EVIDENCE_KEYS)
    segment_id = payload["segment_id"]
    fragment = payload["fragment"]
    if not isinstance(segment_id, str) or not isinstance(fragment, str):
        raise TypeError("evidence strings")
    return (segment_id, fragment)


def _map_provider_exception(exc: BaseException, secret: str) -> BackendFailure:
    name = type(exc).__name__
    if "timeout" in name.lower() or _looks_like_timeout(exc):
        return _fail("TIMEOUT", "The OpenAI Responses API call timed out.")
    if _is_context_limit_error(exc):
        return _fail(
            "DOCUMENT_TOO_LARGE",
            "The provider rejected the request as larger than the model context window.",
        )
    return _fail("PROVIDER_ERROR", f"The OpenAI Responses API failed ({name}).")


def _looks_like_timeout(exc: BaseException) -> bool:
    return "timeout" in _redact(str(exc), "").lower()


def _is_context_limit_error(exc: BaseException) -> bool:
    structured = _structured_error_text(exc)
    if _looks_like_context_limit(structured):
        return True
    return _looks_like_context_limit(str(exc))


def _structured_error_text(exc: BaseException) -> str:
    chunks: list[str] = []
    for attr in ("code", "type", "param"):
        value = getattr(exc, attr, None)
        if isinstance(value, str):
            chunks.append(value)
    chunks.extend(_flatten_error_body(getattr(exc, "body", None)))
    return " ".join(chunks)


def _flatten_error_body(body: object) -> list[str]:
    if isinstance(body, str):
        return [body]
    if not isinstance(body, dict):
        return []
    found: list[str] = []
    for key in ("code", "type", "param", "message"):
        value = body.get(key)
        if isinstance(value, str):
            found.append(value)
    nested = body.get("error")
    if nested is not None:
        found.extend(_flatten_error_body(nested))
    return found


def _looks_like_context_limit(text: str) -> bool:
    lowered = text.lower()
    collapsed = lowered.replace(" ", "_")
    return any(marker in lowered or marker in collapsed for marker in _CONTEXT_MARKERS)


def _fail(code: str, message: str) -> BackendFailure:
    return BackendFailure(code=code, message=message)


def _redact(text: str, secret: str) -> str:
    if secret:
        return text.replace(secret, "[redacted]")
    return text
