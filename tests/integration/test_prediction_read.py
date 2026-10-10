"""Read a saved prediction without extraction, gold, or a provider."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from fastapi.testclient import TestClient

from promoter_ai_extraction.api import create_app
from promoter_ai_extraction.models import (
    EvidenceItem,
    ExtractedValue,
    ExtractionRun,
    Property,
    PropertyResult,
    ScientificStatus,
    TechnicalFailure,
)
from promoter_ai_extraction.persistence import SCHEMA_VERSION, PredictionStore

_ROOT = Path(__file__).resolve().parents[2]
_UI = _ROOT / "src" / "promoter_ai_extraction" / "ui"
_PROPERTIES = ("TSS", "Caja -10", "Caja -35", "Factor sigma")
_ALLOWED = {"run_id", "paper_id", "promoter_name", "properties", "agent", "retrieval"}


class _ForbiddenBoundary:
    def embed(self, texts: list[str]) -> list[tuple[float, ...]]:
        raise AssertionError("embedder called")

    def generate(self, safe_input: object) -> object:
        raise AssertionError("backend called")

    def complete(self, messages: object) -> object:
        raise AssertionError("orchestrator called")


def _evidence() -> EvidenceItem:
    return EvidenceItem(
        fragment="The minus 10 box of promoter narnZp9 is TATAGT.",
        segment_id="txt:p:0003",
        source_type="body_text",
        location="lines:10-10",
    )


def _extracted(prop: Property, value: str) -> PropertyResult:
    item = ExtractedValue(
        value_raw=value,
        value_normalized=value,
        qualifier=None,
        derivation_note=None,
        evidence=(_evidence(),),
    )
    return PropertyResult(
        paper_id="SYNTH-READ-01",
        promoter_name="narnZp9",
        property=prop,
        status=ScientificStatus.EXTRACTED,
        values=(item,),
        candidate_values=(),
        evidence=(_evidence(),),
        abstention_reason=None,
    )


def _technical() -> TechnicalFailure:
    return TechnicalFailure(
        stage="extraction",
        code="INVALID_BACKEND_PAYLOAD",
        message="Backend returned mismatched evidence identifiers and fragments.",
        cause="ValidationError",
    )


def _run(*, technical_tss: bool) -> ExtractionRun:
    return ExtractionRun(
        run_id="SYNTH-READ-01__narnZp9",
        paper_id="SYNTH-READ-01",
        promoter_name="narnZp9",
        tss=_technical() if technical_tss else _extracted(Property.TSS, "-48"),
        caja_10=_extracted(Property.CAJA_10, "TATAGT"),
        caja_35=_extracted(Property.CAJA_35, "TTGATA"),
        sigma=_extracted(Property.FACTOR_SIGMA, "sigma32"),
    )


def _client(directory: Path) -> TestClient:
    app = create_app(
        backend=_ForbiddenBoundary(),
        prediction_dir=directory,
        embedder=_ForbiddenBoundary(),
        orchestrator=_ForbiddenBoundary(),
    )
    return TestClient(app)


def _save(directory: Path, run: ExtractionRun, fingerprint: dict[str, object]) -> Path:
    store = PredictionStore(directory)
    stored = store.save(run, document_hash="sha256:synthetic", system_fingerprint=fingerprint)
    assert not hasattr(stored, "code")
    return directory / f"{run.run_id}.json"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_get_guided_prediction_rebuilds_four_properties(tmp_path: Path) -> None:
    path = _save(
        tmp_path,
        _run(technical_tss=False),
        {"retrieval": {"embedding_model": "BAAI/bge-small-en-v1.5", "properties": {}}},
    )
    before = _sha(path)
    response = _client(tmp_path).get("/predictions/SYNTH-READ-01__narnZp9")
    assert response.status_code == 200
    body = response.json()
    assert set(body) <= _ALLOWED
    assert "file_path" not in response.text
    assert body["properties"]["TSS"]["kind"] == "scientific"
    assert body["properties"]["TSS"]["status"] == "EXTRACTED"
    assert body["properties"]["Caja -10"]["values"][0]["value_normalized"] == "TATAGT"
    assert body["properties"]["Caja -35"]["values"][0]["value_normalized"] == "TTGATA"
    assert body["properties"]["Factor sigma"]["values"][0]["value_normalized"] == "sigma32"
    assert body["retrieval"]["embedding_model"] == "BAAI/bge-small-en-v1.5"
    assert "agent" not in body
    assert _sha(path) == before


def test_get_agent_prediction_keeps_technical_tss(tmp_path: Path) -> None:
    _save(
        tmp_path,
        _run(technical_tss=True),
        {
            "agent": {
                "termination": "end_turn",
                "rounds": 3,
                "tool_executions": 8,
                "steps": [{"tool": "extract_property", "property": "TSS"}],
            }
        },
    )
    body = _client(tmp_path).get("/predictions/SYNTH-READ-01__narnZp9").json()
    assert body["properties"]["TSS"]["kind"] == "technical"
    assert body["properties"]["TSS"]["code"] == "INVALID_BACKEND_PAYLOAD"
    assert "status" not in body["properties"]["TSS"]
    assert body["agent"]["termination"] == "end_turn"
    assert "retrieval" not in body
    assert set(body["properties"]) == set(_PROPERTIES)


def test_missing_prediction_is_404(tmp_path: Path) -> None:
    response = _client(tmp_path).get("/predictions/SYNTH-MISSING__narnZp9")
    assert response.status_code == 404
    assert response.json()["code"] == "FILE_NOT_FOUND"


def test_invalid_run_id_is_rejected(tmp_path: Path) -> None:
    client = _client(tmp_path)
    for run_id in ("a..b", "paper:promoter", "bad%2Fid"):
        response = client.get("/predictions/" + run_id)
        assert response.status_code == 422
        assert response.json()["code"] == "INVALID_REQUEST"


def test_symlink_outside_the_store_is_not_read(tmp_path: Path) -> None:
    outside = tmp_path / "outside.json"
    outside.write_text('{"secret":"OUTSIDE_GOLD_MARKER"}', encoding="utf-8")
    store = tmp_path / "preds"
    store.mkdir()
    (store / "SYNTH-LINK__narnZp9.json").symlink_to(outside)
    response = _client(store).get("/predictions/SYNTH-LINK__narnZp9")
    assert response.status_code == 422
    assert response.json()["code"] == "INVALID_REQUEST"
    assert "OUTSIDE_GOLD_MARKER" not in response.text
    assert outside.read_text(encoding="utf-8").count("OUTSIDE_GOLD_MARKER") == 1


def test_corrupt_json_is_422(tmp_path: Path) -> None:
    (tmp_path / "SYNTH-BAD__narnZp9.json").write_text("{", encoding="utf-8")
    response = _client(tmp_path).get("/predictions/SYNTH-BAD__narnZp9")
    assert response.status_code == 422
    assert response.json()["code"] == "CORRUPT_RECORD"


def test_unsupported_schema_is_422(tmp_path: Path) -> None:
    path = _save(tmp_path, _run(technical_tss=False), {"retrieval": {}})
    record = json.loads(path.read_text(encoding="utf-8"))
    record["schema_version"] = SCHEMA_VERSION + 1
    path.write_text(json.dumps(record), encoding="utf-8")
    response = _client(tmp_path).get("/predictions/SYNTH-READ-01__narnZp9")
    assert response.status_code == 422
    assert response.json()["code"] == "UNSUPPORTED_SCHEMA"


def test_persisted_identity_must_match_the_request(tmp_path: Path) -> None:
    path = _save(tmp_path, _run(technical_tss=False), {"retrieval": {}})
    record = json.loads(path.read_text(encoding="utf-8"))
    record["run_id"] = "OTHER__narnZp9"
    path.write_text(json.dumps(record), encoding="utf-8")
    response = _client(tmp_path).get("/predictions/SYNTH-READ-01__narnZp9")
    assert response.status_code == 422
    assert response.json()["code"] == "CORRUPT_RECORD"


def test_read_does_not_open_gold_or_call_providers(tmp_path: Path) -> None:
    gold = tmp_path / "gold.json"
    gold.write_text('{"gold_value":"PRIVATE_GOLD_MARKER"}', encoding="utf-8")
    store = tmp_path / "preds"
    store.mkdir()
    _save(store, _run(technical_tss=False), {"retrieval": {"embedding_model": "local"}})
    response = _client(store).get("/predictions/SYNTH-READ-01__narnZp9")
    assert response.status_code == 200
    assert "PRIVATE_GOLD_MARKER" not in response.text
    assert "gold" not in response.json()
    assert gold.read_text(encoding="utf-8").count("PRIVATE_GOLD_MARKER") == 1


def test_existing_file_still_returns_409_on_post(tmp_path: Path) -> None:
    path = _save(tmp_path, _run(technical_tss=False), {"retrieval": {}})
    before = _sha(path)
    client = _client(tmp_path)
    loaded = client.get("/predictions/SYNTH-READ-01__narnZp9")
    posted = client.post(
        "/extract",
        json={
            "paper_id": "SYNTH-READ-01",
            "promoter_name": "narnZp9",
            "document_format": "TXT",
            "document": "synthetic",
        },
    )
    assert loaded.status_code == 200
    assert posted.status_code == 409
    assert posted.json()["code"] == "FILE_EXISTS"
    assert _sha(path) == before


def test_saved_result_page_reuses_the_card_renderer() -> None:
    page = (_UI / "index.html").read_text(encoding="utf-8")
    script = (_UI / "app.js").read_text(encoding="utf-8")
    assert 'id="load-saved"' in page
    assert "Consultar resultado guardado" in page
    assert 'type="button"' in page
    start = script.index("function loadSaved")
    body = script[start : script.index("function ", start + 1)]
    assert 'fetch("/predictions/"' in body
    assert "Resultado previamente guardado" in body
    assert "renderCards()" in body
    assert "renderDetail()" in body
    assert "renderTrace(body)" in body
    assert "persistedKey" in body
    assert "endpoint()" not in body
    load_rule = script[script.index("function canLoad") : script.index("function refreshRunButton")]
    assert "confirm-call" not in load_rule
    assert "state.document" not in load_rule
