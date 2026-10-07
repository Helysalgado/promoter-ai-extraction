"""Persist-before-gold ordering for EvaluationService (T032/T033)."""
from __future__ import annotations

from pathlib import Path

from promoter_ai_extraction.evaluation.gold_loader import GoldDataset, GoldLoader, GoldLoadError
from promoter_ai_extraction.evaluation.metrics import EvaluationReport
from promoter_ai_extraction.evaluation.service import EvaluationError, EvaluationService
from promoter_ai_extraction.models import Property
from promoter_ai_extraction.persistence import (
    PersistedPredictionRef,
    PersistenceFailure,
    PredictionStore,
    VerifiedPersistedPrediction,
)
from synthetic_gold import make_run, persist_verified, write_synthetic_gold


class CountingGoldLoader(GoldLoader):
    def __init__(self) -> None:
        self.calls = 0

    def load(self, source: object, gold_path: Path) -> GoldDataset | GoldLoadError:
        self.calls += 1
        return super().load(source, gold_path)


def test_in_memory_run_is_rejected_without_gold_access(tmp_path: Path) -> None:
    loader = CountingGoldLoader()
    service = EvaluationService(PredictionStore(tmp_path / "predictions"), loader=loader)
    gold = write_synthetic_gold(
        tmp_path / "gold.xlsx",
        [
            {
                "ID_paper": "PMC12345",
                "Nombre_promotor": "lacZp1",
                "Propiedad": "TSS",
                "GT_para_referencia": "-42",
                "Modalidad_origen": "texto_explicito",
            }
        ],
    )
    outcome = service.evaluate(make_run(), gold)
    assert isinstance(outcome, EvaluationError)
    assert outcome.code == "MISSING_VERIFIED_PERSISTENCE"
    assert loader.calls == 0


def test_failed_persistence_records_zero_gold_loader_calls(tmp_path: Path) -> None:
    loader = CountingGoldLoader()
    store = PredictionStore(tmp_path / "predictions")
    service = EvaluationService(store, loader=loader)
    missing = PersistedPredictionRef(
        run_id="missing-run",
        file_path=str(tmp_path / "predictions" / "missing-run.json"),
        schema_version=1,
        content_hash="sha256:deadbeef",
    )
    gold = write_synthetic_gold(
        tmp_path / "gold.xlsx",
        [
            {
                "ID_paper": "PMC12345",
                "Nombre_promotor": "lacZp1",
                "Propiedad": "TSS",
                "GT_para_referencia": "-42",
            }
        ],
    )
    outcome = service.evaluate(missing, gold)
    assert isinstance(outcome, EvaluationError)
    assert outcome.code in {"FILE_NOT_FOUND", "HASH_MISMATCH", "CORRUPT_RECORD"}
    assert loader.calls == 0
    assert gold.exists()


def test_verified_ref_then_gold_then_report(tmp_path: Path) -> None:
    events: list[str] = []
    store = PredictionStore(tmp_path / "predictions")
    loader = CountingGoldLoader()
    service = EvaluationService(store, loader=loader)
    events.append("extract")
    verified = persist_verified(tmp_path, make_run(run_id="eval-order"))
    events.append("verified")
    gold = write_synthetic_gold(
        tmp_path / "gold.xlsx",
        [
            {
                "ID_paper": "PMC12345",
                "Nombre_promotor": "lacZp1",
                "Propiedad": "TSS",
                "GT_para_referencia": "-42",
                "Modalidad_origen": "texto_explicito",
            }
        ],
    )
    report = service.evaluate(verified.ref, gold)
    events.append("gold")
    assert isinstance(report, EvaluationReport)
    assert events == ["extract", "verified", "gold"]
    assert loader.calls == 1
    tss = report.by_property[Property.TSS]
    assert tss.tp == 1
    assert tss.exact_row_accuracy == 1.0
    assert isinstance(verified, VerifiedPersistedPrediction)


def test_evaluate_does_not_accept_persistence_failure(tmp_path: Path) -> None:
    loader = CountingGoldLoader()
    service = EvaluationService(PredictionStore(tmp_path / "predictions"), loader=loader)
    failure = PersistenceFailure(
        stage="write",
        code="FILE_EXISTS",
        message="already written",
        cause="FileExistsError",
    )
    gold = tmp_path / "gold.xlsx"
    gold.write_bytes(b"not-opened")
    outcome = service.evaluate(failure, gold)
    assert isinstance(outcome, EvaluationError)
    assert loader.calls == 0
