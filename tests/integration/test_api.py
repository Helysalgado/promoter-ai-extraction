"""HTTP contract for the minimal FastAPI extract service. Synthetic inputs only."""
from __future__ import annotations

import inspect
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from fakes import ScriptedBackend
from promoter_ai_extraction.api import (
    HTTP_MAX_OUTPUT_TOKENS,
    MAX_DOCUMENT_CHARS,
    create_app,
)
from promoter_ai_extraction.extraction import (
    BackendFailure,
    RawPropertyPayload,
    RawValuePayload,
    SafeExtractionInput,
)
from promoter_ai_extraction.models import Property

_PARA = "The promoter lacZp1 TSS is -42."
_HIDDEN = "UNIQUE_NOT_IN_EVIDENCE"
_DOCUMENT = f"{_PARA}\n\n{_HIDDEN}\n"


def _extracted(value: str) -> RawPropertyPayload:
    return RawPropertyPayload(
        status="EXTRACTED",
        values=(
            RawValuePayload(
                value_raw=value,
                qualifier=None,
                evidence_segment_ids=("txt:p:0000",),
                evidence_fragments=(_PARA,),
            ),
        ),
        candidates=(),
        abstention_reason=None,
        result_evidence=(),
    )


def _abstention() -> RawPropertyPayload:
    return RawPropertyPayload(
        status="NOT_FOUND",
        values=(),
        candidates=(),
        abstention_reason="The paper does not name this property.",
        result_evidence=(),
    )


def _four(
    *,
    tss: RawPropertyPayload | BackendFailure | None = None,
    caja_10: RawPropertyPayload | BackendFailure | None = None,
    caja_35: RawPropertyPayload | BackendFailure | None = None,
    sigma: RawPropertyPayload | BackendFailure | None = None,
) -> ScriptedBackend:
    return ScriptedBackend(
        {
            Property.TSS: tss or _extracted("-42"),
            Property.CAJA_10: caja_10 or _extracted("TATAAT"),
            Property.CAJA_35: caja_35 or _extracted("TTGACA"),
            Property.FACTOR_SIGMA: sigma or _extracted("sigma70"),
        }
    )


class CountingBackend:
    """Counts generate calls around a scripted backend."""

    def __init__(self, inner: ScriptedBackend, *, delay_s: float = 0.0) -> None:
        self._inner = inner
        self._delay_s = delay_s
        self.calls = 0
        self._lock = threading.Lock()

    def generate(self, safe_input: SafeExtractionInput):
        with self._lock:
            self.calls += 1
        if self._delay_s:
            time.sleep(self._delay_s)
        return self._inner.generate(safe_input)


def _body(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "paper_id": "PMC12345",
        "promoter_name": "lacZp1",
        "document_format": "TXT",
        "document": _DOCUMENT,
    }
    payload.update(overrides)
    return payload


def _client(tmp_path: Path, backend: CountingBackend | ScriptedBackend | None = None) -> TestClient:
    app = create_app(backend=backend, prediction_dir=tmp_path)
    return TestClient(app)


def test_health_reports_version_without_a_backend(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    response = _client(tmp_path).get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["software_version"]
    assert "sk-" not in response.text


def test_extract_returns_four_properties_with_evidence(tmp_path: Path) -> None:
    backend = CountingBackend(_four())
    response = _client(tmp_path, backend).post("/extract", json=_body())
    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == "PMC12345__lacZp1"
    assert body["paper_id"] == "PMC12345"
    assert set(body["properties"]) == {"TSS", "Caja -10", "Caja -35", "Factor sigma"}
    tss = body["properties"]["TSS"]
    assert tss["kind"] == "scientific"
    assert tss["status"] == "EXTRACTED"
    value = tss["values"][0]
    assert value["value_raw"] == "-42"
    assert value["value_normalized"] == "-42"
    evidence = value["evidence"][0]
    assert evidence["segment_id"] == "txt:p:0000"
    assert evidence["location"] == "lines:1-1"
    assert evidence["fragment"] == _PARA
    assert _HIDDEN not in response.text
    assert "file_path" not in response.text
    assert backend.calls == 4
    stored = list(tmp_path.glob("*.json"))
    assert len(stored) == 1


def test_scientific_abstention_has_no_accepted_values(tmp_path: Path) -> None:
    backend = _four(caja_10=_abstention())
    response = _client(tmp_path, backend).post("/extract", json=_body(paper_id="PMC9"))
    slot = response.json()["properties"]["Caja -10"]
    assert response.status_code == 200
    assert slot["kind"] == "scientific"
    assert slot["status"] == "NOT_FOUND"
    assert slot["values"] == []
    assert slot["abstention_reason"]


def test_technical_failure_stays_distinct_from_abstention(tmp_path: Path) -> None:
    backend = _four(caja_35=BackendFailure(code="TIMEOUT", message="timed out"))
    response = _client(tmp_path, backend).post("/extract", json=_body(paper_id="PMC8"))
    slot = response.json()["properties"]["Caja -35"]
    assert response.status_code == 200
    assert slot["kind"] == "technical"
    assert slot["code"] == "TIMEOUT"
    assert "status" not in slot


def test_forbidden_and_unknown_fields_do_not_call_the_backend(tmp_path: Path) -> None:
    backend = CountingBackend(_four())
    response = _client(tmp_path, backend).post(
        "/extract",
        json=_body(gold="secret-target", document_path="/etc/passwd", api_key="sk-should-not-echo"),
    )
    assert response.status_code == 422
    assert backend.calls == 0
    assert "sk-should-not-echo" not in response.text
    assert "secret-target" not in response.text
    assert "/etc/passwd" not in response.text
    fields = set(response.json()["fields"])
    assert "gold" in fields
    assert "document_path" in fields


def test_empty_document_is_rejected_before_extraction(tmp_path: Path) -> None:
    backend = CountingBackend(_four())
    response = _client(tmp_path, backend).post("/extract", json=_body(document="  \n"))
    assert response.status_code == 422
    assert response.json()["code"] == "EMPTY_DOCUMENT"
    assert backend.calls == 0


def test_malformed_xml_is_a_technical_rejection(tmp_path: Path) -> None:
    backend = CountingBackend(_four())
    response = _client(tmp_path, backend).post(
        "/extract",
        json=_body(document_format="TEI/XML", document="<tei"),
    )
    assert response.status_code == 422
    assert response.json()["code"] == "MALFORMED_XML"
    assert backend.calls == 0


def test_missing_credential_is_503_and_does_not_fall_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-a-real-key")
    created: list[str] = []

    class _OpenAI:
        def __init__(self, max_output_tokens: int) -> None:
            created.append("openai")

    class _Anthropic:
        def __init__(self, max_output_tokens: int) -> None:
            created.append("anthropic")

    monkeypatch.setattr("promoter_ai_extraction.api.OpenAIModelBackend", _OpenAI)
    monkeypatch.setattr("promoter_ai_extraction.api.AnthropicModelBackend", _Anthropic)
    response = _client(tmp_path).post("/extract", json=_body(provider="anthropic"))
    assert response.status_code == 503
    assert response.json()["code"] == "MISSING_CREDENTIAL"
    assert "sk-test" not in response.text
    assert created == []


def test_provider_selection_uses_only_the_requested_backend(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-not-a-real-key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    inner = _four()
    created: list[tuple[str, int]] = []

    class _OpenAI:
        def __init__(self, max_output_tokens: int) -> None:
            created.append(("openai", max_output_tokens))

    class _Anthropic:
        def __init__(self, max_output_tokens: int) -> None:
            created.append(("anthropic", max_output_tokens))

        def generate(self, safe_input: SafeExtractionInput):
            return inner.generate(safe_input)

    monkeypatch.setattr("promoter_ai_extraction.api.OpenAIModelBackend", _OpenAI)
    monkeypatch.setattr("promoter_ai_extraction.api.AnthropicModelBackend", _Anthropic)
    response = _client(tmp_path).post(
        "/extract",
        json=_body(provider="anthropic", paper_id="PMC7", max_output_tokens=4096),
    )
    assert response.status_code == 200
    assert created == [("anthropic", 4096)]


def test_openai_omitted_output_limit_is_4096(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-a-real-key")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    inner = _four()
    created: list[int] = []

    class _OpenAI:
        def __init__(self, max_output_tokens: int) -> None:
            created.append(max_output_tokens)

        def generate(self, safe_input: SafeExtractionInput):
            return inner.generate(safe_input)

    monkeypatch.setattr("promoter_ai_extraction.api.OpenAIModelBackend", _OpenAI)
    response = _client(tmp_path).post("/extract", json=_body(provider="openai", paper_id="PMC4"))
    assert response.status_code == 200
    assert created == [HTTP_MAX_OUTPUT_TOKENS]
    assert created == [4096]


def test_duplicate_prediction_is_409_without_another_call(tmp_path: Path) -> None:
    backend = CountingBackend(_four())
    client = _client(tmp_path, backend)
    first = client.post("/extract", json=_body())
    second = client.post("/extract", json=_body())
    assert first.status_code == 200
    assert second.status_code == 409
    assert second.json()["code"] == "FILE_EXISTS"
    assert str(tmp_path) not in second.text
    assert backend.calls == 4


def test_concurrent_requests_do_not_overwrite_or_double_call(tmp_path: Path) -> None:
    backend = CountingBackend(_four(), delay_s=0.2)
    app = create_app(backend=backend, prediction_dir=tmp_path)
    start = threading.Barrier(2)

    def post() -> int:
        start.wait()
        with TestClient(app) as client:
            return client.post("/extract", json=_body(paper_id="PMC6")).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        codes = sorted(pool.map(lambda _: post(), range(2)))
    assert codes == [200, 409]
    assert backend.calls == 4
    stored = list(tmp_path.glob("*.json"))
    assert len(stored) == 1
    assert stored[0].read_text(encoding="utf-8").count('"run_id"') == 1


def test_document_and_generation_limits_are_server_defined(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert MAX_DOCUMENT_CHARS == 100_000
    assert HTTP_MAX_OUTPUT_TOKENS == 4_096
    backend = CountingBackend(_four())
    client = _client(tmp_path, backend)
    huge = client.post("/extract", json=_body(document="a" * 100_001))
    assert huge.status_code == 413
    assert huge.json()["code"] == "DOCUMENT_TOO_LARGE"
    zero = client.post("/extract", json=_body(max_output_tokens=0, paper_id="PMC5"))
    assert zero.status_code == 422
    invalid = client.post("/extract", json=_body(max_output_tokens="many", paper_id="PMC3"))
    assert invalid.status_code == 422
    assert backend.calls == 0

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-a-real-key")
    created: list[int] = []

    class _OpenAI:
        def __init__(self, max_output_tokens: int) -> None:
            created.append(max_output_tokens)

    monkeypatch.setattr("promoter_ai_extraction.api.OpenAIModelBackend", _OpenAI)
    over = _client(tmp_path).post("/extract", json=_body(max_output_tokens=128_000, paper_id="PMC2"))
    assert over.status_code == 422
    assert over.json()["code"] == "LIMIT_EXCEEDED"
    assert created == []


def test_http_path_does_not_import_gold_or_pass_it_to_the_backend(tmp_path: Path) -> None:
    import promoter_ai_extraction.api as api

    source = inspect.getsource(api)
    assert "gold_loader" not in source
    assert "EvaluationService" not in source
    assert set(SafeExtractionInput.__dataclass_fields__) == {
        "paper_id",
        "promoter_name",
        "promoter_id",
        "paper_gene_synonym",
        "property",
        "document_segments",
    }
    response = _client(tmp_path, _four()).post(
        "/extract",
        json=_body(promoter_id="RDB1", paper_gene_synonym="lacZ"),
    )
    assert response.status_code == 200
    assert "GT_para_referencia" not in response.text
