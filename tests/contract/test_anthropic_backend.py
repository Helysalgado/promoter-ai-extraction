"""Contract tests for AnthropicModelBackend.

No network. A fake Messages client records the request and returns canned output.
"""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from promoter_ai_extraction.backends.anthropic_backend import (
    CONTEXT_WINDOW_TOKENS,
    DEFAULT_MAX_TOKENS,
    MODEL_ID,
    PUBLISHED_MAX_OUTPUT_TOKENS,
    AnthropicModelBackend,
)
from promoter_ai_extraction.boundary import ExtractionRequest
from promoter_ai_extraction.documents import DocumentSegment, LoadedDocument
from promoter_ai_extraction.extraction import (
    BackendFailure,
    PropertyExtractor,
    RawPropertyPayload,
    SafeDocumentSegment,
    SafeExtractionInput,
)
from promoter_ai_extraction.models import Property, ScientificStatus, TechnicalFailure
from promoter_ai_extraction.validation import OutputValidator

_SEG = SafeDocumentSegment(
    segment_id="txt:p:0000",
    text="The TSS of lacZp1 is -42.",
    source_type="body_text",
    location="lines:1-1",
)
_FAKE_KEY = "sk-ant-test-not-a-real-key-do-not-leak"
_FORBIDDEN = (
    "GT_para_referencia",
    "SUBSET_GOLD",
    "Modalidad_origen",
    "texto_explicito",
    "imagen_only",
    "Valor_verificado_manualmente",
    "Valor_RegulonDB",
    "gold-set",
    "expected target",
)
_SCIENTIFIC = {status.value for status in ScientificStatus}


def _safe_input(prop: Property = Property.TSS) -> SafeExtractionInput:
    return SafeExtractionInput(
        paper_id="PMC12345",
        promoter_name="lacZp1",
        promoter_id="ECK1200",
        paper_gene_synonym="lacZ",
        property=prop,
        document_segments=(_SEG,),
    )


def _valid_payload() -> dict[str, object]:
    return {
        "status": "EXTRACTED",
        "values": [
            {
                "value_raw": "-42",
                "qualifier": None,
                "evidence_segment_ids": ["txt:p:0000"],
                "evidence_fragments": ["The TSS of lacZp1 is -42."],
            }
        ],
        "candidates": [],
        "abstention_reason": None,
        "result_evidence": [],
    }


def _message(**overrides: object) -> SimpleNamespace:
    payload = dict(
        model=MODEL_ID,
        stop_reason="end_turn",
        content=[SimpleNamespace(type="text", text=json.dumps(_valid_payload()))],
    )
    payload.update(overrides)
    return SimpleNamespace(**payload)


class FakeMessagesClient:
    def __init__(self, handler: object) -> None:
        self.calls: list[dict[str, object]] = []
        self._handler = handler
        self.messages = self

    def create(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        return self._handler(kwargs)


def _backend(handler: object, monkeypatch: pytest.MonkeyPatch) -> AnthropicModelBackend:
    monkeypatch.setenv("ANTHROPIC_API_KEY", _FAKE_KEY)
    return AnthropicModelBackend(client=FakeMessagesClient(handler))


def test_messages_request_uses_strict_json_schema(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", _FAKE_KEY)
    fake = FakeMessagesClient(lambda kwargs: _message())
    outcome = AnthropicModelBackend(client=fake).generate(_safe_input())
    assert isinstance(outcome, RawPropertyPayload)
    assert len(fake.calls) == 1
    request = fake.calls[0]
    assert request["model"] == "claude-sonnet-5-5"
    assert request["max_tokens"] == DEFAULT_MAX_TOKENS
    messages = request["messages"]
    assert isinstance(messages, list)
    assert messages[0]["role"] == "user"
    output_config = request["output_config"]
    assert isinstance(output_config, dict)
    fmt = output_config["format"]
    assert isinstance(fmt, dict)
    assert fmt["type"] == "json_schema"
    schema = fmt["schema"]
    assert isinstance(schema, dict)
    assert schema.get("additionalProperties") is False
    for field in ("status", "values", "candidates", "abstention_reason", "result_evidence"):
        assert field in schema["properties"]
        assert field in schema["required"]
    assert "output_format" not in request
    assert "tools" not in request
    assert "betas" not in request
    extra = request.get("extra_headers")
    assert not extra or "structured-outputs" not in json.dumps(extra)


def test_prompt_uses_only_safe_extraction_input(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[str] = []

    def handler(kwargs: dict[str, object]) -> object:
        captured.append(json.dumps(kwargs))
        return _message()

    outcome = _backend(handler, monkeypatch).generate(_safe_input())
    assert isinstance(outcome, RawPropertyPayload)
    blob = captured[0]
    assert "PMC12345" in blob
    assert "lacZp1" in blob
    assert "ECK1200" in blob
    assert "lacZ" in blob
    assert "TSS" in blob
    assert "txt:p:0000" in blob
    assert "The TSS of lacZp1 is -42." in blob
    lowered = blob.lower()
    for token in _FORBIDDEN:
        assert token.lower() not in lowered
    assert _FAKE_KEY not in blob


def test_valid_response_maps_to_raw_property_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    outcome = _backend(lambda kwargs: _message(), monkeypatch).generate(_safe_input())
    assert isinstance(outcome, RawPropertyPayload)
    assert outcome.status == "EXTRACTED"
    assert outcome.values[0].value_raw == "-42"
    assert outcome.values[0].evidence_segment_ids == ("txt:p:0000",)
    assert outcome.abstention_reason is None


def test_thinking_blocks_are_not_parsed_as_the_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    message = _message(
        content=[
            SimpleNamespace(type="thinking", thinking="gold TSS is -12"),
            SimpleNamespace(type="text", text=json.dumps(_valid_payload())),
        ]
    )
    backend = _backend(lambda kwargs: message, monkeypatch)
    outcome = backend.generate(_safe_input())
    assert isinstance(outcome, RawPropertyPayload)
    assert outcome.values[0].value_raw == "-42"
    assert "gold TSS" not in json.dumps(backend.reproducibility_metadata())


def test_malformed_text_is_backend_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    outcome = _backend(
        lambda kwargs: _message(content=[SimpleNamespace(type="text", text="not-json")]),
        monkeypatch,
    ).generate(_safe_input())
    assert isinstance(outcome, BackendFailure)
    assert outcome.code == "MALFORMED_RESPONSE"
    assert outcome.code not in _SCIENTIFIC
    assert _FAKE_KEY not in outcome.message


def test_schema_violation_is_backend_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    outcome = _backend(
        lambda kwargs: _message(
            content=[SimpleNamespace(type="text", text=json.dumps({"status": "EXTRACTED"}))]
        ),
        monkeypatch,
    ).generate(_safe_input())
    assert isinstance(outcome, BackendFailure)
    assert outcome.code == "SCHEMA_VIOLATION"
    assert _FAKE_KEY not in outcome.message


def test_max_tokens_stop_is_incomplete_even_when_json_parses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    outcome = _backend(
        lambda kwargs: _message(stop_reason="max_tokens"),
        monkeypatch,
    ).generate(_safe_input())
    assert isinstance(outcome, BackendFailure)
    assert outcome.code == "INCOMPLETE_RESPONSE"
    assert outcome.code not in _SCIENTIFIC


def test_refusal_is_technical_not_scientific(monkeypatch: pytest.MonkeyPatch) -> None:
    refused = _valid_payload()
    refused["status"] = "NOT_FOUND"
    outcome = _backend(
        lambda kwargs: _message(
            stop_reason="refusal",
            content=[SimpleNamespace(type="text", text=json.dumps(refused))],
        ),
        monkeypatch,
    ).generate(_safe_input())
    assert isinstance(outcome, BackendFailure)
    assert outcome.code not in _SCIENTIFIC
    assert not isinstance(outcome, RawPropertyPayload)


def test_rate_limit_is_technical_and_does_not_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    class RateLimitError(Exception):
        status_code = 429

    def handler(kwargs: dict[str, object]) -> object:
        raise RateLimitError(f"slow down {_FAKE_KEY}")

    fake = FakeMessagesClient(handler)
    monkeypatch.setenv("ANTHROPIC_API_KEY", _FAKE_KEY)
    outcome = AnthropicModelBackend(client=fake).generate(_safe_input())
    assert isinstance(outcome, BackendFailure)
    assert outcome.code == "RATE_LIMIT"
    assert outcome.code not in _SCIENTIFIC
    assert len(fake.calls) == 1
    assert _FAKE_KEY not in outcome.message


def test_provider_error_redacts_credential(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(kwargs: dict[str, object]) -> object:
        raise RuntimeError(f"provider blew up {_FAKE_KEY}")

    outcome = _backend(handler, monkeypatch).generate(_safe_input())
    assert isinstance(outcome, BackendFailure)
    assert outcome.code == "PROVIDER_ERROR"
    assert _FAKE_KEY not in outcome.message


def test_schema_api_error_is_technical(monkeypatch: pytest.MonkeyPatch) -> None:
    class SchemaError(Exception):
        status_code = 400

        def __str__(self) -> str:
            return f"output schema rejected {_FAKE_KEY}"

    outcome = _backend(lambda kwargs: (_ for _ in ()).throw(SchemaError()), monkeypatch).generate(
        _safe_input()
    )
    assert isinstance(outcome, BackendFailure)
    assert outcome.code == "SCHEMA_VIOLATION"
    assert _FAKE_KEY not in outcome.message


def test_missing_credential_does_not_call_the_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    fake = FakeMessagesClient(lambda kwargs: pytest.fail("must not call"))
    outcome = AnthropicModelBackend(client=fake).generate(_safe_input())
    assert isinstance(outcome, BackendFailure)
    assert outcome.code == "MISSING_CREDENTIAL"
    assert fake.calls == []
    assert "sk-ant" not in outcome.message


def test_document_over_budget_is_not_sent(monkeypatch: pytest.MonkeyPatch) -> None:
    huge = SafeExtractionInput(
        paper_id="PMC1",
        promoter_name="pX",
        promoter_id=None,
        paper_gene_synonym=None,
        property=Property.TSS,
        document_segments=(
            SafeDocumentSegment(
                segment_id="txt:p:0000",
                text="A" * (CONTEXT_WINDOW_TOKENS - 1_000),
                source_type="body_text",
                location=None,
            ),
        ),
    )
    fake = FakeMessagesClient(lambda kwargs: pytest.fail("must not send an oversized prompt"))
    monkeypatch.setenv("ANTHROPIC_API_KEY", _FAKE_KEY)
    outcome = AnthropicModelBackend(client=fake).generate(huge)
    assert isinstance(outcome, BackendFailure)
    assert outcome.code == "DOCUMENT_TOO_LARGE"
    assert fake.calls == []
    assert CONTEXT_WINDOW_TOKENS - 1_000 > CONTEXT_WINDOW_TOKENS - PUBLISHED_MAX_OUTPUT_TOKENS


def test_reproducibility_records_provider_model_and_effective_params(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    backend = _backend(lambda kwargs: _message(model="claude-sonnet-5-5-20261001"), monkeypatch)
    backend_capped = AnthropicModelBackend(
        client=FakeMessagesClient(lambda kwargs: _message()),
        max_output_tokens=4096,
    )
    monkeypatch.setenv("ANTHROPIC_API_KEY", _FAKE_KEY)
    assert isinstance(backend.generate(_safe_input()), RawPropertyPayload)
    common = backend.reproducibility_metadata()["common"]
    assert common["provider"] == "anthropic"
    assert common["model"] == MODEL_ID
    assert common["api"] == "messages"
    generation = common["generation"]
    assert generation["max_tokens"] == DEFAULT_MAX_TOKENS
    assert generation["max_output_tokens"] == DEFAULT_MAX_TOKENS
    assert generation["max_retries"] == 0
    assert generation["output_format"] == "json_schema"
    blob = json.dumps(backend.reproducibility_metadata())
    assert _FAKE_KEY not in blob
    assert isinstance(backend_capped.generate(_safe_input(Property.CAJA_10)), RawPropertyPayload)
    capped = backend_capped.reproducibility_metadata()
    assert capped["common"]["generation"]["max_tokens"] == 4096
    assert capped["by_property"]["Caja -10"]["model_snapshot"] == MODEL_ID


def test_no_fallback_model_and_single_call_on_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeMessagesClient(lambda kwargs: (_ for _ in ()).throw(RuntimeError("down")))
    monkeypatch.setenv("ANTHROPIC_API_KEY", _FAKE_KEY)
    AnthropicModelBackend(client=fake).generate(_safe_input())
    assert len(fake.calls) == 1
    assert fake.calls[0]["model"] == "claude-sonnet-5-5"


@pytest.mark.parametrize("invalid", [0, -1, True])
def test_output_cap_rejects_non_positive_integers(invalid: object) -> None:
    with pytest.raises(ValueError):
        AnthropicModelBackend(max_output_tokens=invalid)  # type: ignore[arg-type]


def test_live_client_sets_max_retries_to_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class _CapturingClient:
        def __init__(self, **kwargs: object) -> None:
            captured.update(kwargs)

    monkeypatch.setattr("anthropic.Anthropic", _CapturingClient)
    from promoter_ai_extraction.backends.anthropic_backend import _live_client

    _live_client(_FAKE_KEY)
    assert captured["max_retries"] == 0
    assert captured["api_key"] == _FAKE_KEY
    public = {key: value for key, value in captured.items() if key != "api_key"}
    assert _FAKE_KEY not in json.dumps(public)


def test_extractor_keeps_schema_failure_technical(monkeypatch: pytest.MonkeyPatch) -> None:
    backend = _backend(
        lambda kwargs: _message(content=[SimpleNamespace(type="text", text="{")]),
        monkeypatch,
    )
    extractor = PropertyExtractor(backend=backend, validator=OutputValidator())
    request = ExtractionRequest(
        document=LoadedDocument(
            paper_id="PMC12345",
            format="TXT",
            segments=(
                DocumentSegment(
                    "txt:p:0000",
                    "The TSS of lacZp1 is -42.",
                    "body_text",
                    "lines:1-1",
                ),
            ),
            document_hash="ab" * 32,
        ),
        paper_id="PMC12345",
        promoter_name="lacZp1",
        promoter_id="ECK1200",
        paper_gene_synonym="lacZ",
        property=Property.TSS,
    )
    outcome = extractor.extract(request)
    assert isinstance(outcome, TechnicalFailure)
    assert outcome.code not in _SCIENTIFIC
    assert _FAKE_KEY not in outcome.message
