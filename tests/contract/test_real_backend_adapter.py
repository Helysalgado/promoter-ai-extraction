"""Contract tests for OpenAIModelBackend (T037/T038).

No network. A fake Responses client records the request and returns canned output.
"""
from __future__ import annotations

import json
import os
from types import SimpleNamespace

import pytest

from promoter_ai_extraction.backends.openai_backend import (
    CONTEXT_WINDOW_TOKENS,
    MAX_OUTPUT_TOKENS,
    MODEL_ID,
    OpenAIModelBackend,
)
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
_FAKE_KEY = "sk-test-not-a-real-key-do-not-leak"
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


def _completed_response(**overrides: object) -> SimpleNamespace:
    payload = dict(
        output_text=json.dumps(_valid_payload()),
        model=MODEL_ID,
        status="completed",
        error=None,
        incomplete_details=None,
    )
    payload.update(overrides)
    return SimpleNamespace(**payload)


class FakeResponsesClient:
    def __init__(self, handler: object) -> None:
        self.calls: list[dict[str, object]] = []
        self._handler = handler
        self.responses = self

    def create(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        return self._handler(kwargs)


def _backend(handler: object, monkeypatch: pytest.MonkeyPatch) -> OpenAIModelBackend:
    monkeypatch.setenv("OPENAI_API_KEY", _FAKE_KEY)
    return OpenAIModelBackend(client=FakeResponsesClient(handler))


def test_responses_request_uses_strict_json_schema(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(kwargs: dict[str, object]) -> object:
        return _completed_response()

    monkeypatch.setenv("OPENAI_API_KEY", _FAKE_KEY)
    fake = FakeResponsesClient(handler)
    outcome = OpenAIModelBackend(client=fake).generate(_safe_input())
    assert isinstance(outcome, RawPropertyPayload)
    assert len(fake.calls) == 1
    request = fake.calls[0]
    assert request["model"] == MODEL_ID
    assert request["truncation"] == "disabled"
    text = request["text"]
    assert isinstance(text, dict)
    fmt = text["format"]
    assert isinstance(fmt, dict)
    assert fmt["type"] == "json_schema"
    assert fmt["strict"] is True
    assert "schema" in fmt
    schema = fmt["schema"]
    assert isinstance(schema, dict)
    assert schema.get("additionalProperties") is False
    for field in ("status", "values", "candidates", "abstention_reason", "result_evidence"):
        assert field in schema["properties"]
        assert field in schema["required"]
    assert "response_format" not in request
    assert not request.get("tools")


def test_prompt_uses_only_safe_extraction_input(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[str] = []

    def handler(kwargs: dict[str, object]) -> object:
        captured.append(json.dumps(kwargs))
        return _completed_response()

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
    outcome = _backend(
        lambda kwargs: _completed_response(),
        monkeypatch,
    ).generate(_safe_input())
    assert isinstance(outcome, RawPropertyPayload)
    assert outcome.status == "EXTRACTED"
    assert outcome.values[0].value_raw == "-42"
    assert outcome.values[0].evidence_segment_ids == ("txt:p:0000",)
    assert outcome.abstention_reason is None
    assert outcome.candidates == ()


def test_schema_violation_is_backend_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    outcome = _backend(
        lambda kwargs: _completed_response(output_text=json.dumps({"status": "EXTRACTED"})),
        monkeypatch,
    ).generate(_safe_input())
    assert isinstance(outcome, BackendFailure)
    assert outcome.code == "SCHEMA_VIOLATION"
    assert _FAKE_KEY not in outcome.message


def test_unexpected_payload_field_is_schema_violation(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = _valid_payload()
    payload["gold_value"] = "-42"
    outcome = _backend(
        lambda kwargs: _completed_response(output_text=json.dumps(payload)),
        monkeypatch,
    ).generate(_safe_input())
    assert isinstance(outcome, BackendFailure)
    assert outcome.code == "SCHEMA_VIOLATION"


def test_non_string_value_raw_is_schema_violation(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = _valid_payload()
    values = payload["values"]
    assert isinstance(values, list)
    first = values[0]
    assert isinstance(first, dict)
    first["value_raw"] = -42
    outcome = _backend(
        lambda kwargs: _completed_response(output_text=json.dumps(payload)),
        monkeypatch,
    ).generate(_safe_input())
    assert isinstance(outcome, BackendFailure)
    assert outcome.code == "SCHEMA_VIOLATION"


def test_malformed_response_is_backend_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    outcome = _backend(
        lambda kwargs: _completed_response(output_text="not-json{"),
        monkeypatch,
    ).generate(_safe_input())
    assert isinstance(outcome, BackendFailure)
    assert outcome.code == "MALFORMED_RESPONSE"
    assert _FAKE_KEY not in outcome.message


def test_incomplete_status_with_parseable_json_is_technical_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    outcome = _backend(
        lambda kwargs: SimpleNamespace(
            output_text=json.dumps(_valid_payload()),
            model=MODEL_ID,
            status="incomplete",
            error=None,
            incomplete_details=SimpleNamespace(reason="max_output_tokens"),
        ),
        monkeypatch,
    ).generate(_safe_input())
    assert isinstance(outcome, BackendFailure)
    assert outcome.code == "INCOMPLETE_RESPONSE"
    assert outcome.code not in _SCIENTIFIC


def test_response_error_object_is_provider_error(monkeypatch: pytest.MonkeyPatch) -> None:
    outcome = _backend(
        lambda kwargs: SimpleNamespace(
            output_text=json.dumps(_valid_payload()),
            model=MODEL_ID,
            status="failed",
            error=SimpleNamespace(code="server_error", message=f"boom {_FAKE_KEY}"),
            incomplete_details=None,
        ),
        monkeypatch,
    ).generate(_safe_input())
    assert isinstance(outcome, BackendFailure)
    assert outcome.code == "PROVIDER_ERROR"
    assert outcome.code not in _SCIENTIFIC
    assert _FAKE_KEY not in outcome.message


def test_provider_error_is_backend_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(kwargs: dict[str, object]) -> object:
        raise RuntimeError(f"upstream 500 using {_FAKE_KEY}")

    outcome = _backend(handler, monkeypatch).generate(_safe_input())
    assert isinstance(outcome, BackendFailure)
    assert outcome.code == "PROVIDER_ERROR"
    assert _FAKE_KEY not in outcome.message
    assert _FAKE_KEY not in outcome.code


def test_structured_context_limit_error_is_document_too_large(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class StructuredContextError(Exception):
        def __init__(self) -> None:
            super().__init__("Request too large for this model.")
            self.status_code = 400
            self.code = "context_length_exceeded"
            self.body = {
                "error": {
                    "code": "context_length_exceeded",
                    "type": "invalid_request_error",
                }
            }

    def handler(kwargs: dict[str, object]) -> object:
        raise StructuredContextError()

    outcome = _backend(handler, monkeypatch).generate(_safe_input())
    assert isinstance(outcome, BackendFailure)
    assert outcome.code == "DOCUMENT_TOO_LARGE"


def test_timeout_is_backend_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(kwargs: dict[str, object]) -> object:
        raise TimeoutError("read timed out")

    outcome = _backend(handler, monkeypatch).generate(_safe_input())
    assert isinstance(outcome, BackendFailure)
    assert outcome.code == "TIMEOUT"


def test_missing_credential_is_backend_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    fake = FakeResponsesClient(lambda kwargs: pytest.fail("must not call the API"))
    outcome = OpenAIModelBackend(client=fake).generate(_safe_input())
    assert isinstance(outcome, BackendFailure)
    assert outcome.code == "MISSING_CREDENTIAL"
    assert fake.calls == []


def test_injected_environ_is_passed_to_openai_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    captured: dict[str, object] = {}

    class FakeOpenAI:
        def __init__(self, **kwargs: object) -> None:
            captured.update(kwargs)
            raise RuntimeError("constructed; do not call network")

    monkeypatch.setattr("openai.OpenAI", FakeOpenAI)
    outcome = OpenAIModelBackend(environ={"OPENAI_API_KEY": _FAKE_KEY}).generate(_safe_input())
    assert captured.get("api_key") == _FAKE_KEY
    assert "OPENAI_API_KEY" not in os.environ
    assert isinstance(outcome, BackendFailure)
    assert _FAKE_KEY not in outcome.message


def test_document_too_large_does_not_call_api(monkeypatch: pytest.MonkeyPatch) -> None:
    huge = SafeDocumentSegment(
        segment_id="txt:p:0000",
        text="A" * (CONTEXT_WINDOW_TOKENS + 1),
        source_type="body_text",
        location=None,
    )
    safe = SafeExtractionInput(
        paper_id="PMC1",
        promoter_name="pX",
        promoter_id=None,
        paper_gene_synonym=None,
        property=Property.TSS,
        document_segments=(huge,),
    )
    fake = FakeResponsesClient(lambda kwargs: pytest.fail("must not truncate or send"))
    monkeypatch.setenv("OPENAI_API_KEY", _FAKE_KEY)
    outcome = OpenAIModelBackend(client=fake).generate(safe)
    assert isinstance(outcome, BackendFailure)
    assert outcome.code == "DOCUMENT_TOO_LARGE"
    assert fake.calls == []


def test_preflight_reserves_output_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    """Chars just under the published window must still fail once output is reserved.

    This is a character-length fail-closed bound, not a token count.
    """
    almost_window = SafeDocumentSegment(
        segment_id="txt:p:0000",
        text="A" * (CONTEXT_WINDOW_TOKENS - 1_000),
        source_type="body_text",
        location=None,
    )
    safe = SafeExtractionInput(
        paper_id="PMC1",
        promoter_name="pX",
        promoter_id=None,
        paper_gene_synonym=None,
        property=Property.TSS,
        document_segments=(almost_window,),
    )
    fake = FakeResponsesClient(lambda kwargs: pytest.fail("must reserve output budget"))
    monkeypatch.setenv("OPENAI_API_KEY", _FAKE_KEY)
    outcome = OpenAIModelBackend(client=fake).generate(safe)
    assert isinstance(outcome, BackendFailure)
    assert outcome.code == "DOCUMENT_TOO_LARGE"
    assert fake.calls == []
    assert CONTEXT_WINDOW_TOKENS - 1_000 > CONTEXT_WINDOW_TOKENS - MAX_OUTPUT_TOKENS


def test_extractor_turns_schema_failure_into_technical_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    backend = _backend(
        lambda kwargs: _completed_response(output_text="{"),
        monkeypatch,
    )
    extractor = PropertyExtractor(backend=backend, validator=OutputValidator())
    from promoter_ai_extraction.boundary import ExtractionRequest
    from promoter_ai_extraction.documents import DocumentSegment, LoadedDocument

    request = ExtractionRequest(
        document=LoadedDocument(
            paper_id="PMC12345",
            format="TXT",
            segments=(
                DocumentSegment("txt:p:0000", "The TSS of lacZp1 is -42.", "body_text", "lines:1-1"),
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


def test_reproducibility_metadata_excludes_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    backend = _backend(
        lambda kwargs: _completed_response(
            model="gpt-6.1-sol-2026-09-29",
            system_fingerprint="fp_test",
        ),
        monkeypatch,
    )
    outcome = backend.generate(_safe_input())
    assert isinstance(outcome, RawPropertyPayload)
    meta = backend.reproducibility_metadata()
    common = meta["common"]
    assert common["provider"] == "openai"
    assert common["model"] == MODEL_ID
    assert common["api"] == "responses"
    assert "prompt_version" in common
    assert "schema_version" in common
    assert common["generation"]["truncation"] == "disabled"
    assert "document_hash" not in common
    by_property = meta["by_property"]
    assert by_property["TSS"]["model_snapshot"] == "gpt-6.1-sol-2026-09-29"
    assert by_property["TSS"]["system_fingerprint"] == "fp_test"
    dumped = json.dumps(meta)
    assert _FAKE_KEY not in dumped
    assert "OPENAI_API_KEY" not in dumped


def test_response_metadata_is_not_copied_across_properties(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshots = iter(["snap-tss", "snap-caja10"])
    fingerprints = iter(["fp-tss", "fp-caja10"])

    def handler(kwargs: dict[str, object]) -> object:
        return _completed_response(
            model=next(snapshots),
            system_fingerprint=next(fingerprints),
        )

    backend = _backend(handler, monkeypatch)
    assert isinstance(backend.generate(_safe_input(Property.TSS)), RawPropertyPayload)
    assert isinstance(backend.generate(_safe_input(Property.CAJA_10)), RawPropertyPayload)
    by_property = backend.reproducibility_metadata()["by_property"]
    assert by_property["TSS"]["model_snapshot"] == "snap-tss"
    assert by_property["Caja -10"]["model_snapshot"] == "snap-caja10"
    assert by_property["TSS"]["system_fingerprint"] != by_property["Caja -10"]["system_fingerprint"]
    assert "Caja -35" not in by_property


def test_no_fallback_model_in_request(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeResponsesClient(lambda kwargs: _completed_response())
    monkeypatch.setenv("OPENAI_API_KEY", _FAKE_KEY)
    OpenAIModelBackend(client=fake).generate(_safe_input())
    assert fake.calls[0]["model"] == "gpt-6.1-sol"


def test_default_output_cap_stays_published_maximum(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeResponsesClient(lambda kwargs: _completed_response())
    monkeypatch.setenv("OPENAI_API_KEY", _FAKE_KEY)
    backend = OpenAIModelBackend(client=fake)
    assert isinstance(backend.generate(_safe_input()), RawPropertyPayload)
    assert len(fake.calls) == 1
    assert fake.calls[0]["max_output_tokens"] == MAX_OUTPUT_TOKENS
    generation = backend.reproducibility_metadata()["common"]["generation"]
    assert generation["max_output_tokens"] == MAX_OUTPUT_TOKENS
    assert generation["max_retries"] == 0


def test_configured_output_cap_is_sent_and_recorded(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeResponsesClient(lambda kwargs: _completed_response())
    monkeypatch.setenv("OPENAI_API_KEY", _FAKE_KEY)
    backend = OpenAIModelBackend(client=fake, max_output_tokens=4096)
    assert isinstance(backend.generate(_safe_input()), RawPropertyPayload)
    assert fake.calls[0]["max_output_tokens"] == 4096
    generation = backend.reproducibility_metadata()["common"]["generation"]
    assert generation["max_output_tokens"] == 4096
    assert generation["max_retries"] == 0


@pytest.mark.parametrize("invalid", [0, -1, True])
def test_output_cap_rejects_non_positive_integers(invalid: object) -> None:
    with pytest.raises(ValueError):
        OpenAIModelBackend(max_output_tokens=invalid)  # type: ignore[arg-type]


def test_live_client_sets_max_retries_to_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class _CapturingClient:
        def __init__(self, **kwargs: object) -> None:
            captured.update(kwargs)

    monkeypatch.setattr("openai.OpenAI", _CapturingClient)
    from promoter_ai_extraction.backends.openai_backend import _live_client

    _live_client(_FAKE_KEY)
    assert captured["max_retries"] == 0
    assert _FAKE_KEY not in json.dumps({key: value for key, value in captured.items() if key != "api_key"})
