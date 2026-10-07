"""Failing tests for evaluator-only GoldLoader (T023).

Coverage:
- load requires VerifiedPersistedPrediction before opening any workbook;
- ExtractionRun in memory is rejected without touching the gold path;
- synthetic Hoja1 / row-4 headers / identity keys / raw cell + storage type;
- missing/corrupt workbooks remain technical GoldLoadError;
- fixture paths stay under tmp_path and never mention SUBSET_GOLD.xlsx.
"""
from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook

from synthetic_gold import make_run, persist_verified, write_synthetic_gold
from promoter_ai_extraction.evaluation.gold_loader import (
    GoldLoadError,
    GoldLoader,
    GoldRecord,
)
from promoter_ai_extraction.models import Property, ScientificStatus
from promoter_ai_extraction.persistence import PersistenceFailure, PersistedPredictionRef


def _row(
    *,
    paper_id: str = "PMC12345",
    promoter: str = "lacZp1",
    prop: str = "TSS",
    gt: object = "-42",
    modalidad: str = "texto_explicito",
) -> dict[str, object]:
    return {
        "Fila_origen": 1,
        "ID_promotor": "ECK1200",
        "Nombre_promotor": promoter,
        "Sinonimo_gen_en_este_paper": "lacZ",
        "ID_paper": paper_id,
        "Propiedad": prop,
        "Valor_RegulonDB": "hidden",
        "Modalidad_origen": modalidad,
        "GT_para_referencia": gt,
        "Evidencia": "curator-only",
    }


def test_load_requires_verified_prediction_not_extraction_run(tmp_path: Path) -> None:
    gold_path = tmp_path / "missing.xlsx"
    outcome = GoldLoader().load(make_run(), gold_path)
    assert isinstance(outcome, GoldLoadError)
    assert outcome.code == "MISSING_VERIFIED_PERSISTENCE"
    assert not gold_path.exists()


def test_load_rejects_unverified_ref_without_opening_file(tmp_path: Path) -> None:
    gold_path = tmp_path / "never-opened.xlsx"
    fake_ref = PersistedPredictionRef(
        run_id="nope",
        file_path=str(tmp_path / "predictions" / "nope.json"),
        schema_version=1,
        content_hash="sha256:00",
    )
    outcome = GoldLoader().load(fake_ref, gold_path)
    assert isinstance(outcome, GoldLoadError)
    assert outcome.code == "MISSING_VERIFIED_PERSISTENCE"
    assert not gold_path.exists()


def test_load_rejects_persistence_failure_without_opening_file(tmp_path: Path) -> None:
    gold_path = tmp_path / "never-opened.xlsx"
    failure = PersistenceFailure(
        stage="write",
        code="WRITE_ERROR",
        message="not persisted",
        cause="OSError",
    )
    outcome = GoldLoader().load(failure, gold_path)
    assert isinstance(outcome, GoldLoadError)
    assert outcome.code == "MISSING_VERIFIED_PERSISTENCE"
    assert not gold_path.exists()


def test_verified_persistence_then_gold_access(tmp_path: Path) -> None:
    verified = persist_verified(tmp_path)
    gold_path = write_synthetic_gold(tmp_path / "gold.xlsx", [_row()])
    dataset = GoldLoader().load(verified, gold_path)
    assert not isinstance(dataset, GoldLoadError)
    assert len(dataset.records) == 1
    record = dataset.records[0]
    assert isinstance(record, GoldRecord)
    assert record.paper_id == "PMC12345"
    assert record.promoter_name == "lacZp1"
    assert record.property == Property.TSS
    assert record.gold_value_raw == "-42"
    assert record.storage_type == "text"
    assert record.modalidad_origen == "texto_explicito"


def test_numeric_tss_cell_preserves_storage_type(tmp_path: Path) -> None:
    verified = persist_verified(tmp_path)
    gold_path = write_synthetic_gold(tmp_path / "gold.xlsx", [_row(gt=-42)])
    dataset = GoldLoader().load(verified, gold_path)
    assert not isinstance(dataset, GoldLoadError)
    record = dataset.records[0]
    assert record.gold_value_raw == -42
    assert record.storage_type == "numeric"


def test_unknown_property_label_is_technical_failure(tmp_path: Path) -> None:
    verified = persist_verified(tmp_path)
    gold_path = write_synthetic_gold(
        tmp_path / "gold.xlsx", [_row(prop="not-a-property")]
    )
    outcome = GoldLoader().load(verified, gold_path)
    assert isinstance(outcome, GoldLoadError)
    assert outcome.code not in {status.value for status in ScientificStatus}


def test_missing_workbook_is_technical_failure(tmp_path: Path) -> None:
    verified = persist_verified(tmp_path)
    outcome = GoldLoader().load(verified, tmp_path / "absent.xlsx")
    assert isinstance(outcome, GoldLoadError)
    assert outcome.code == "FILE_NOT_FOUND"


def test_corrupt_workbook_is_technical_failure(tmp_path: Path) -> None:
    verified = persist_verified(tmp_path)
    gold_path = tmp_path / "corrupt.xlsx"
    gold_path.write_text("not an xlsx", encoding="utf-8")
    outcome = GoldLoader().load(verified, gold_path)
    assert isinstance(outcome, GoldLoadError)
    assert outcome.code == "CORRUPT_WORKBOOK"


def test_missing_sheet_is_technical_failure(tmp_path: Path) -> None:
    verified = persist_verified(tmp_path)
    gold_path = tmp_path / "wrong-sheet.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.title = "Other"
    workbook.save(gold_path)
    outcome = GoldLoader().load(verified, gold_path)
    assert isinstance(outcome, GoldLoadError)
    assert outcome.code == "MISSING_SHEET"


def test_missing_headers_is_technical_failure(tmp_path: Path) -> None:
    verified = persist_verified(tmp_path)
    gold_path = tmp_path / "no-headers.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.title = "Hoja1"
    sheet["A4"] = "not-the-required-headers"
    workbook.save(gold_path)
    outcome = GoldLoader().load(verified, gold_path)
    assert isinstance(outcome, GoldLoadError)
    assert outcome.code == "MISSING_HEADERS"


def test_loader_does_not_build_extraction_request(tmp_path: Path) -> None:
    verified = persist_verified(tmp_path)
    gold_path = write_synthetic_gold(tmp_path / "gold.xlsx", [_row()])
    dataset = GoldLoader().load(verified, gold_path)
    assert not isinstance(dataset, GoldLoadError)
    assert not hasattr(dataset, "document")
    assert all(not hasattr(record, "document") for record in dataset.records)


def test_fixture_path_is_tmp_and_not_real_gold(tmp_path: Path) -> None:
    gold_path = write_synthetic_gold(tmp_path / "gold.xlsx", [_row()])
    resolved = str(gold_path.resolve())
    assert str(tmp_path.resolve()) in resolved
    assert "SUBSET_GOLD.xlsx" not in resolved


def test_gold_load_error_code_is_not_scientific() -> None:
    scientific = {status.value for status in ScientificStatus}
    for code in (
        "MISSING_VERIFIED_PERSISTENCE",
        "FILE_NOT_FOUND",
        "CORRUPT_WORKBOOK",
        "MISSING_SHEET",
        "MISSING_HEADERS",
        "UNKNOWN_PROPERTY",
    ):
        assert code not in scientific
