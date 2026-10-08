"""Contract tests for persist-before-gold and extractor isolation (T023/T024)."""
from __future__ import annotations

import ast
from pathlib import Path

from promoter_ai_extraction.boundary import ExtractionRequest
from promoter_ai_extraction.documents import DocumentSegment, LoadedDocument
from promoter_ai_extraction.evaluation.gold_loader import GoldLoadError, GoldLoader
from promoter_ai_extraction.extraction import PropertyExtractor, SafeExtractionInput
from promoter_ai_extraction.models import Property, ScientificStatus
from promoter_ai_extraction.validation import OutputValidator
from fakes import CaptureBackend
from synthetic_gold import make_run, persist_verified, write_synthetic_gold
from promoter_ai_extraction.extraction import RawPropertyPayload, RawValuePayload


_SRC = Path(__file__).resolve().parents[2] / "src" / "promoter_ai_extraction"
_EXTRACTION_MODULES = (
    "__init__.py",
    "boundary.py",
    "documents.py",
    "extraction.py",
    "models.py",
    "normalization.py",
    "validation.py",
    "persistence.py",
    "backends/__init__.py",
    "backends/openai_backend.py",
)


def test_in_memory_run_does_not_open_missing_gold(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist.xlsx"
    outcome = GoldLoader().load(make_run(), missing)
    assert isinstance(outcome, GoldLoadError)
    assert outcome.code == "MISSING_VERIFIED_PERSISTENCE"
    assert not missing.exists()


def test_persist_verified_reference_then_gold_access(tmp_path: Path) -> None:
    events: list[str] = []
    run = make_run(run_id="order-run")
    events.append("extract")
    verified = persist_verified(tmp_path, run)
    events.append("verified")
    gold_path = write_synthetic_gold(
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
    dataset = GoldLoader().load(verified, gold_path)
    events.append("gold")
    assert not isinstance(dataset, GoldLoadError)
    assert events == ["extract", "verified", "gold"]
    assert dataset.records[0].gold_value_raw == "-42"


def test_extraction_modules_do_not_import_gold_loader() -> None:
    forbidden = ("promoter_ai_extraction.evaluation", "gold_loader", "GoldLoader")
    for name in _EXTRACTION_MODULES:
        tree = ast.parse((_SRC / name).read_text(encoding="utf-8"), filename=name)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    joined = alias.name
                    assert "evaluation" not in joined
                    assert "gold_loader" not in joined
                    assert alias.name != "GoldLoader"
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for token in forbidden:
                    assert token not in module
                    assert all(token not in (alias.name or "") for alias in node.names)


def test_safe_extraction_input_has_no_gold_fields() -> None:
    names = set(SafeExtractionInput.__dataclass_fields__)
    assert "gold_path" not in names
    assert "gold" not in names
    assert "GT_para_referencia" not in names


def test_backend_payload_has_no_gold_path() -> None:
    document = LoadedDocument(
        paper_id="PMC12345",
        format="TXT",
        segments=(
            DocumentSegment(
                segment_id="txt:p:0001",
                text="The TSS was mapped to -42 upstream of the ATG.",
                source_type="body_text",
                location="line 1",
            ),
        ),
        document_hash="ab" * 32,
    )
    payload = RawPropertyPayload(
        status="EXTRACTED",
        values=(
            RawValuePayload(
                value_raw="-42",
                qualifier=None,
                evidence_segment_ids=("txt:p:0001",),
                evidence_fragments=("The TSS was mapped to -42 upstream of the ATG.",),
            ),
        ),
        candidates=(),
        abstention_reason=None,
        result_evidence=(),
    )
    capture = CaptureBackend(response=payload)
    extractor = PropertyExtractor(backend=capture, validator=OutputValidator())
    request = ExtractionRequest(
        document=document,
        paper_id="PMC12345",
        promoter_id=None,
        promoter_name="lacZp1",
        paper_gene_synonym=None,
        property=Property.TSS,
    )
    extractor.extract(request)
    received = capture.received[0]
    assert isinstance(received, SafeExtractionInput)
    assert not hasattr(received, "gold_path")
    payload_text = str(received)
    assert "GT_para_referencia" not in payload_text
    assert "SUBSET_GOLD" not in payload_text


def test_gold_load_error_is_not_scientific_status() -> None:
    scientific = {status.value for status in ScientificStatus}
    error = GoldLoadError(
        stage="gold_load",
        code="FILE_NOT_FOUND",
        message="missing",
        cause="FileNotFoundError",
    )
    assert error.code not in scientific
