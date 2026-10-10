"""Local baseline runner tests — T040 (RED) / T041 (GREEN).

RED: collection fails because ``promoter_ai_extraction.baseline`` does not exist.
After T041 the tests pass using only synthetic papers, a T039-safe manifest,
and a synthetic gold workbook under ``tmp_path``.

Coverage:
- AC-19/AC-20 persist-before-gold and immutable predictions
- AC-21 comparison unit paper × promoter × property
- AC-23 per-property report
- AC-24 texto_explicito strata without extractor access
- AC-26 positive-only limitation
- AC-28/AC-29 safe manifest only; gold/evaluator fields never reach the backend
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import asdict
from pathlib import Path

import pytest

from promoter_ai_extraction.baseline import BaselineRunner
from promoter_ai_extraction.boundary import BoundaryViolation
from promoter_ai_extraction.evaluation.gold_loader import GoldLoader
from promoter_ai_extraction.evaluation.metrics import POSITIVE_ONLY_LIMITATION, EvaluationReport
from promoter_ai_extraction.extraction import (
    BackendFailure,
    RawPropertyPayload,
    RawValuePayload,
    SafeExtractionInput,
)
from promoter_ai_extraction.models import Property, ScientificStatus, TechnicalFailure
from promoter_ai_extraction.persistence import PersistenceFailure
from fakes import ScriptedBackend
from synthetic_gold import write_synthetic_gold

_BODY = (
    "The promoter lacZp1 TSS is -42 with Caja -10 TATAAT, "
    "Caja -35 TTGACA, and sigma70."
)
_FORBIDDEN = (
    "GT_para_referencia",
    "SUBSET_GOLD",
    "Modalidad_origen",
    "gold_path",
    "split",
)
_REPO = Path(__file__).resolve().parents[2]


class RecordingBackend(ScriptedBackend):
    def __init__(self, responses: dict[Property, RawPropertyPayload | BackendFailure]) -> None:
        super().__init__(responses)
        self.received: list[SafeExtractionInput] = []

    def generate(self, safe_input: SafeExtractionInput) -> RawPropertyPayload | BackendFailure:
        self.received.append(safe_input)
        return super().generate(safe_input)


def _extracted(value: str, segment_id: str) -> RawPropertyPayload:
    return RawPropertyPayload(
        status="EXTRACTED",
        values=(
            RawValuePayload(
                value_raw=value,
                qualifier=None,
                evidence_segment_ids=(segment_id,),
                evidence_fragments=(_BODY,),
            ),
        ),
        candidates=(),
        abstention_reason=None,
        result_evidence=(),
    )


def _abstention(segment_id: str) -> RawPropertyPayload:
    return RawPropertyPayload(
        status="INSUFFICIENT_EVIDENCE",
        values=(),
        candidates=(),
        abstention_reason="No extractable value in the supplied segments.",
        result_evidence=((segment_id, _BODY),),
    )


def _gold_rows() -> list[dict[str, str]]:
    return [
        {
            "ID_paper": "PMC12345",
            "Nombre_promotor": "lacZp1",
            "Propiedad": "TSS",
            "GT_para_referencia": "-42",
            "Modalidad_origen": "texto_explicito",
        },
        {
            "ID_paper": "PMC12345",
            "Nombre_promotor": "lacZp1",
            "Propiedad": "Caja -10",
            "GT_para_referencia": "TATAAT",
            "Modalidad_origen": "texto_explicito",
        },
        {
            "ID_paper": "PMC12345",
            "Nombre_promotor": "lacZp1",
            "Propiedad": "Caja -35",
            "GT_para_referencia": "TTGACA",
            "Modalidad_origen": "texto_explicito",
        },
        {
            "ID_paper": "PMC12345",
            "Nombre_promotor": "lacZp1",
            "Propiedad": "Factor sigma",
            "GT_para_referencia": "sigma70",
            "Modalidad_origen": "texto_explicito",
        },
    ]


def _write_layout(tmp_path: Path) -> tuple[Path, Path, Path, Path, Path]:
    documents = tmp_path / "papers"
    documents.mkdir()
    (documents / "PMC12345.txt").write_text(_BODY, encoding="utf-8")
    manifest = tmp_path / "safe-manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "document_path": "PMC12345.txt",
                        "document_format": "TXT",
                        "paper_id": "PMC12345",
                        "promoter_id": None,
                        "promoter_name": "lacZp1",
                        "paper_gene_synonym": None,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    gold = write_synthetic_gold(tmp_path / "gold.xlsx", _gold_rows())
    predictions = tmp_path / "predictions"
    report = tmp_path / "report.json"
    return manifest, documents, gold, predictions, report


def _matching_backend() -> RecordingBackend:
    return RecordingBackend(
        {
            Property.TSS: _extracted("-42", "txt:p:0000"),
            Property.CAJA_10: _extracted("TATAAT", "txt:p:0000"),
            Property.CAJA_35: _extracted("TTGACA", "txt:p:0000"),
            Property.FACTOR_SIGMA: _extracted("sigma70", "txt:p:0000"),
        }
    )


def test_runner_extracts_from_safe_manifest_and_writes_report(tmp_path: Path) -> None:
    manifest, documents, gold, predictions, report = _write_layout(tmp_path)
    backend = _matching_backend()
    outcome = BaselineRunner(backend=backend).run(
        manifest=manifest,
        documents=documents,
        gold=gold,
        predictions=predictions,
        report=report,
    )
    assert isinstance(outcome, EvaluationReport)
    assert outcome.evaluated_rows == 4
    assert outcome.parse_failures == 0
    assert outcome.technical_failures == 0
    assert outcome.limitation_note == POSITIVE_ONLY_LIMITATION
    for prop in Property:
        metrics = outcome.by_property[prop]
        assert metrics.tp == 1
        assert metrics.fp == 0
        assert metrics.fn == 0
        assert metrics.recall_texto_explicito == pytest.approx(1.0)
        assert metrics.recall_imagen_only is None
    assert {(row.paper_id, row.promoter_name, row.property) for row in outcome.rows} == {
        ("PMC12345", "lacZp1", prop) for prop in Property
    }
    assert report.is_file()
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["evaluated_rows"] == 4
    assert "false-assertion" in payload["limitation_note"]


def test_backend_never_receives_gold_or_evaluator_fields(tmp_path: Path) -> None:
    manifest, documents, gold, predictions, report = _write_layout(tmp_path)
    backend = _matching_backend()
    BaselineRunner(backend=backend).run(
        manifest=manifest,
        documents=documents,
        gold=gold,
        predictions=predictions,
        report=report,
    )
    assert len(backend.received) == 4
    for safe in backend.received:
        assert isinstance(safe, SafeExtractionInput)
        blob = json.dumps(asdict(safe), default=str)
        for token in _FORBIDDEN:
            assert token not in blob
        assert not hasattr(safe, "gold_path")


def test_gold_is_opened_only_after_prediction_files_exist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest, documents, gold, predictions, report = _write_layout(tmp_path)
    events: list[str] = []
    original = GoldLoader.load

    def tracked(self: GoldLoader, source: object, gold_path: Path) -> object:
        events.append("gold")
        assert list(predictions.glob("*.json")), "gold opened before persistence"
        return original(self, source, gold_path)

    monkeypatch.setattr(GoldLoader, "load", tracked)
    BaselineRunner(backend=_matching_backend()).run(
        manifest=manifest,
        documents=documents,
        gold=gold,
        predictions=predictions,
        report=report,
    )
    assert events == ["gold"]
    assert list(predictions.glob("*.json"))


def test_persisted_predictions_are_immutable(tmp_path: Path) -> None:
    manifest, documents, gold, predictions, report = _write_layout(tmp_path)
    runner = BaselineRunner(backend=_matching_backend())
    first = runner.run(
        manifest=manifest,
        documents=documents,
        gold=gold,
        predictions=predictions,
        report=report,
    )
    assert isinstance(first, EvaluationReport)
    snapshots = {
        path: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(predictions.glob("*.json"))
    }
    assert snapshots
    second = runner.run(
        manifest=manifest,
        documents=documents,
        gold=gold,
        predictions=predictions,
        report=report,
    )
    assert isinstance(second, PersistenceFailure)
    for path, digest in snapshots.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest


def test_prediction_outputs_are_local_and_conventional_dir_is_gitignored(
    tmp_path: Path,
) -> None:
    manifest, documents, gold, predictions, report = _write_layout(tmp_path)
    BaselineRunner(backend=_matching_backend()).run(
        manifest=manifest,
        documents=documents,
        gold=gold,
        predictions=predictions,
        report=report,
    )
    assert predictions.is_dir()
    assert all(path.is_relative_to(tmp_path) for path in predictions.glob("*.json"))
    ignored = subprocess.run(
        ["git", "check-ignore", "-q", "predictions/"],
        cwd=_REPO,
        check=False,
    )
    assert ignored.returncode == 0


def test_leaky_manifest_is_rejected_without_opening_gold(tmp_path: Path) -> None:
    manifest, documents, gold, predictions, report = _write_layout(tmp_path)
    leaky = json.loads(manifest.read_text(encoding="utf-8"))
    leaky["cases"][0]["GT_para_referencia"] = "-42"
    manifest.write_text(json.dumps(leaky), encoding="utf-8")
    missing_gold = tmp_path / "does-not-exist.xlsx"
    try:
        outcome = BaselineRunner(backend=_matching_backend()).run(
            manifest=manifest,
            documents=documents,
            gold=missing_gold,
            predictions=predictions,
            report=report,
        )
    except BoundaryViolation as exc:
        assert exc.code == "FORBIDDEN_FIELD"
        assert not list(predictions.glob("*.json"))
        return
    raise AssertionError(f"leaky manifest must not run extraction: {outcome!r}")


def test_technical_failure_is_not_scientific_abstention(tmp_path: Path) -> None:
    manifest, documents, gold, predictions, report = _write_layout(tmp_path)
    backend = RecordingBackend(
        {
            Property.TSS: _extracted("-42", "txt:p:0000"),
            Property.CAJA_10: _abstention("txt:p:0000"),
            Property.CAJA_35: BackendFailure(code="TIMEOUT", message="synthetic timeout"),
            Property.FACTOR_SIGMA: _extracted("sigma70", "txt:p:0000"),
        }
    )
    outcome = BaselineRunner(backend=backend).run(
        manifest=manifest,
        documents=documents,
        gold=gold,
        predictions=predictions,
        report=report,
    )
    assert isinstance(outcome, EvaluationReport)
    assert outcome.technical_failures >= 1
    scientific = {status.value for status in ScientificStatus}
    assert outcome.by_property[Property.CAJA_10].n_predictions_with_value == 0
    persisted = json.loads(next(predictions.glob("*.json")).read_text(encoding="utf-8"))
    caja_35 = persisted["caja_35"]
    assert caja_35["type"] == "technical_failure"
    assert caja_35["code"] == "TIMEOUT"
    assert caja_35["code"] not in scientific
    caja_10 = persisted["caja_10"]
    assert caja_10["type"] == "property_result"
    assert caja_10["status"] == "INSUFFICIENT_EVIDENCE"


def _rewrite_document_path(manifest: Path, document_path: str) -> None:
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["cases"][0]["document_path"] = document_path
    manifest.write_text(json.dumps(payload), encoding="utf-8")


def test_relative_path_inside_documents_is_accepted(tmp_path: Path) -> None:
    manifest, documents, gold, predictions, report = _write_layout(tmp_path)
    nested = documents / "nested"
    nested.mkdir()
    (nested / "PMC12345.txt").write_text(_BODY, encoding="utf-8")
    _rewrite_document_path(manifest, "nested/PMC12345.txt")
    outcome = BaselineRunner(backend=_matching_backend()).run(
        manifest=manifest,
        documents=documents,
        gold=gold,
        predictions=predictions,
        report=report,
    )
    assert isinstance(outcome, EvaluationReport)
    assert outcome.evaluated_rows == 4


def test_dotdot_that_stays_inside_documents_is_accepted(tmp_path: Path) -> None:
    manifest, documents, gold, predictions, report = _write_layout(tmp_path)
    (documents / "sub").mkdir()
    _rewrite_document_path(manifest, "sub/../PMC12345.txt")
    outcome = BaselineRunner(backend=_matching_backend()).run(
        manifest=manifest,
        documents=documents,
        gold=gold,
        predictions=predictions,
        report=report,
    )
    assert isinstance(outcome, EvaluationReport)


def test_absolute_document_path_is_rejected_before_open(tmp_path: Path) -> None:
    manifest, documents, gold, predictions, report = _write_layout(tmp_path)
    outside = tmp_path / "outside.txt"
    outside.write_text(_BODY, encoding="utf-8")
    _rewrite_document_path(manifest, str(outside))
    backend = _matching_backend()
    outcome = BaselineRunner(backend=backend).run(
        manifest=manifest,
        documents=documents,
        gold=gold,
        predictions=predictions,
        report=report,
    )
    assert isinstance(outcome, TechnicalFailure)
    assert outcome.code == "PATH_OUTSIDE_ROOT"
    assert outcome.code not in {status.value for status in ScientificStatus}
    assert backend.received == []
    assert not list(predictions.glob("*.json"))


def test_parent_escape_is_rejected_before_open(tmp_path: Path) -> None:
    manifest, documents, gold, predictions, report = _write_layout(tmp_path)
    secret = tmp_path / "secret.txt"
    secret.write_text("GT_para_referencia -42", encoding="utf-8")
    _rewrite_document_path(manifest, "../secret.txt")
    backend = _matching_backend()
    outcome = BaselineRunner(backend=backend).run(
        manifest=manifest,
        documents=documents,
        gold=gold,
        predictions=predictions,
        report=report,
    )
    assert isinstance(outcome, TechnicalFailure)
    assert outcome.code == "PATH_OUTSIDE_ROOT"
    assert backend.received == []
    assert not list(predictions.glob("*.json"))


def test_symlink_escape_is_rejected_before_open(tmp_path: Path) -> None:
    manifest, documents, gold, predictions, report = _write_layout(tmp_path)
    secret = tmp_path / "secret.txt"
    secret.write_text(_BODY, encoding="utf-8")
    link = documents / "linked.txt"
    link.symlink_to(secret)
    _rewrite_document_path(manifest, "linked.txt")
    backend = _matching_backend()
    outcome = BaselineRunner(backend=backend).run(
        manifest=manifest,
        documents=documents,
        gold=gold,
        predictions=predictions,
        report=report,
    )
    assert isinstance(outcome, TechnicalFailure)
    assert outcome.code == "PATH_OUTSIDE_ROOT"
    assert backend.received == []
    assert not list(predictions.glob("*.json"))
