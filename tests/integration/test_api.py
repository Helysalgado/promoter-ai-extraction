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
from promoter_ai_extraction.retrieval import EmbedderUnavailable, MAX_RETRIEVED_CHARS

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


class _IdenticalEmbedder:
    """Same vector for every text, so a short fixture still keeps every segment."""

    model_id = "synthetic-identical"

    def embed(self, texts: list[str]) -> list[tuple[float, ...]]:
        return [(1.0, 0.0) for _ in texts]


def _client(
    tmp_path: Path,
    backend: CountingBackend | ScriptedBackend | None = None,
    embedder: object | None = None,
) -> TestClient:
    app = create_app(
        backend=backend,
        prediction_dir=tmp_path,
        embedder=embedder or _IdenticalEmbedder(),
    )
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
    app = create_app(backend=backend, prediction_dir=tmp_path, embedder=_IdenticalEmbedder())
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


class _PhraseEmbedder:
    model_id = "synthetic-phrase"

    def embed(self, texts: list[str]) -> list[tuple[float, ...]]:
        vectors: list[tuple[float, ...]] = []
        for text in texts:
            folded = text.casefold()
            if "transcription start site of this promoter" in folded:
                vectors.append((1.0, 0.0, 0.0, 0.0))
            elif "minus 10 box of this promoter" in folded:
                vectors.append((0.0, 1.0, 0.0, 0.0))
            elif "minus 35 box of this promoter" in folded:
                vectors.append((0.0, 0.0, 1.0, 0.0))
            elif "sigma factor of this promoter" in folded:
                vectors.append((0.0, 0.0, 0.0, 1.0))
            else:
                vectors.append((0.0, 0.0, 0.0, 0.0))
        return vectors


class _RecordingBackend:
    def __init__(self, inner: ScriptedBackend) -> None:
        self._inner = inner
        self.inputs: list[SafeExtractionInput] = []

    def generate(self, safe_input: SafeExtractionInput):
        self.inputs.append(safe_input)
        return self._inner.generate(safe_input)


def test_extract_retrieves_each_property_without_sending_a_far_paragraph(tmp_path: Path) -> None:
    anchor = "The promoter WidgetP, also called radC, is identified here."
    neighbor = "Nearby regulatory context."
    planted = {
        Property.TSS: "The transcription start site of this promoter is -42.",
        Property.CAJA_10: "The minus 10 box of this promoter is CATAAT.",
        Property.CAJA_35: "The minus 35 box of this promoter is TTGAAA.",
        Property.FACTOR_SIGMA: "The sigma factor of this promoter is RpoD.",
    }
    far = "FAR_SEGMENT_TEXT is unrelated metabolism."
    document = "\n\n".join([anchor, neighbor, *planted.values(), far])
    ids = {
        text: f"txt:p:{index:04d}"
        for index, text in enumerate([anchor, neighbor, *planted.values(), far])
    }

    def _cited(prop: Property) -> RawPropertyPayload:
        if prop is Property.CAJA_10:
            return _abstention()
        fragment = planted[prop]
        return RawPropertyPayload(
            status="EXTRACTED",
            values=(
                RawValuePayload(
                    value_raw="-42" if prop is Property.TSS else "kept",
                    qualifier=None,
                    evidence_segment_ids=(ids[fragment],),
                    evidence_fragments=(fragment,),
                ),
            ),
            candidates=(),
            abstention_reason=None,
            result_evidence=(),
        )

    backend = _RecordingBackend(
        ScriptedBackend({prop: _cited(prop) for prop in Property})
    )
    response = _client(tmp_path, backend, embedder=_PhraseEmbedder()).post(
        "/extract",
        json=_body(
            paper_id="PMC77",
            promoter_name="WidgetP",
            paper_gene_synonym="radC",
            document=document,
        ),
    )
    assert response.status_code == 200
    body = response.json()
    assert len(backend.inputs) == 4
    by_property = {item.property: item for item in backend.inputs}
    retrieval = body["retrieval"]["properties"]
    for prop, fragment in planted.items():
        seen = {segment.segment_id for segment in by_property[prop].document_segments}
        assert ids[fragment] in seen
        assert ids[anchor] in seen
        assert ids[neighbor] in seen
        assert retrieval[prop.value]["mode"] == "retrieved"
        assert ids[fragment] in retrieval[prop.value]["segment_ids"]
        assert ids[anchor] in retrieval[prop.value]["segment_ids"]
    caja = body["properties"]["Caja -10"]
    assert caja["kind"] == "scientific"
    assert caja["status"] == "NOT_FOUND"
    assert far not in response.text
    stored = (tmp_path / "PMC77__WidgetP.json").read_text(encoding="utf-8")
    assert far not in stored
    assert "PMC77" in stored
    assert '"retrieval"' in stored


def test_over_budget_segment_is_insufficient_retrieval_not_not_found(tmp_path: Path) -> None:
    backend = CountingBackend(_four())
    response = _client(tmp_path, backend).post(
        "/extract",
        json=_body(document="a" * (MAX_RETRIEVED_CHARS + 1), paper_id="PMC12"),
    )
    assert response.status_code == 200
    assert backend.calls == 0
    for slot in response.json()["properties"].values():
        assert slot["kind"] == "technical"
        assert slot["code"] == "INSUFFICIENT_RETRIEVAL"
        assert "status" not in slot
    stored = (tmp_path / "PMC12__lacZp1.json").read_text(encoding="utf-8")
    assert "a" * 100 not in stored
    assert "INSUFFICIENT_RETRIEVAL" in stored


def test_embedder_failure_does_not_call_the_provider(tmp_path: Path) -> None:
    class _Boom:
        def embed(self, texts: list[str]) -> list[tuple[float, ...]]:
            raise EmbedderUnavailable("hidden-model-path")

    backend = CountingBackend(_four())
    response = _client(tmp_path, backend, embedder=_Boom()).post("/extract", json=_body())
    assert response.status_code == 503
    assert response.json()["code"] == "EMBEDDER_UNAVAILABLE"
    assert "hidden-model-path" not in response.text
    assert backend.calls == 0
    assert list(tmp_path.glob("*.json")) == []


def test_index_failure_does_not_call_the_provider(tmp_path: Path) -> None:
    class _Empty:
        def embed(self, texts: list[str]) -> list[tuple[float, ...]]:
            return []

    backend = CountingBackend(_four())
    response = _client(tmp_path, backend, embedder=_Empty()).post("/extract", json=_body())
    assert response.status_code == 500
    assert response.json()["code"] == "RETRIEVAL_ERROR"
    assert backend.calls == 0
    assert list(tmp_path.glob("*.json")) == []


def test_health_does_not_load_embeddings(tmp_path: Path) -> None:
    class _Boom:
        def embed(self, texts: list[str]) -> list[tuple[float, ...]]:
            raise AssertionError("health must not embed")

    app = create_app(prediction_dir=tmp_path, embedder=_Boom())
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
