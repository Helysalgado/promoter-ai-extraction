"""Local baseline runner: safe manifest → extract → persist → evaluate (T041).

No UI and no HTTP service. Gold is reachable only through
``GuidedBaselineApplication``, which persists before ``EvaluationService``
opens the workbook.
"""
from __future__ import annotations

import json
from pathlib import Path

from promoter_ai_extraction.application import GuidedBaselineApplication
from promoter_ai_extraction.boundary import DevelopmentCase
from promoter_ai_extraction.documents import DocumentSource
from promoter_ai_extraction.evaluation.metrics import EvaluationReport, aggregate_report
from promoter_ai_extraction.evaluation.service import EvaluationError
from promoter_ai_extraction.extraction import ModelBackend
from promoter_ai_extraction.manifest import DevelopmentManifestLoader, ManifestLoadError
from promoter_ai_extraction.models import TechnicalFailure
from promoter_ai_extraction.persistence import PersistenceFailure

__all__ = ["BaselineRunner"]


class BaselineRunner:
    """Path-based runner for leakage-safe local baseline cases."""

    def __init__(self, backend: ModelBackend) -> None:
        self._manifests = DevelopmentManifestLoader()
        self._application = GuidedBaselineApplication(backend)

    def run(
        self,
        *,
        manifest: Path,
        documents: Path,
        gold: Path,
        predictions: Path,
        report: Path,
    ) -> (
        EvaluationReport
        | TechnicalFailure
        | PersistenceFailure
        | EvaluationError
        | ManifestLoadError
    ):
        loaded = self._manifests.load(manifest)
        if isinstance(loaded, ManifestLoadError):
            return loaded

        outcomes: list[EvaluationReport] = []
        for case in loaded.cases:
            outcome = self._run_case(
                case,
                documents=documents,
                gold=gold,
                predictions=predictions,
            )
            if not isinstance(outcome, EvaluationReport):
                return outcome
            outcomes.append(outcome)

        combined = _combine_reports(outcomes)
        _write_report(report, combined)
        return combined

    def _run_case(
        self,
        case: DevelopmentCase,
        *,
        documents: Path,
        gold: Path,
        predictions: Path,
    ) -> EvaluationReport | TechnicalFailure | PersistenceFailure | EvaluationError:
        resolved = _resolve_document(documents, case.document_path)
        if isinstance(resolved, TechnicalFailure):
            return resolved
        source = DocumentSource(
            paper_id=case.paper_id,
            path=resolved,
            content=None,
            format=case.document_format,
        )
        return self._application.run(
            source=source,
            promoter_name=case.promoter_name,
            gold_path=gold,
            prediction_dir=predictions,
            run_id=_run_id(case),
            promoter_id=case.promoter_id,
            paper_gene_synonym=case.paper_gene_synonym,
        )


def _path_outside_root() -> TechnicalFailure:
    return TechnicalFailure(
        stage="document_loading",
        code="PATH_OUTSIDE_ROOT",
        message="The document path must be a relative path inside the documents directory.",
        cause="ValueError",
    )


def _resolve_document(documents: Path, referenced: Path) -> Path | TechnicalFailure:
    if referenced.is_absolute():
        return _path_outside_root()
    try:
        root = documents.resolve()
        candidate = (documents / referenced).resolve()
    except OSError:
        return TechnicalFailure(
            stage="document_loading",
            code="PATH_OUTSIDE_ROOT",
            message="The document path could not be resolved inside the documents directory.",
            cause="OSError",
        )
    if not candidate.is_relative_to(root):
        return _path_outside_root()
    return candidate


def _run_id(case: DevelopmentCase) -> str:
    return f"{case.paper_id}__{case.promoter_name}"


def _combine_reports(reports: list[EvaluationReport]) -> EvaluationReport:
    if len(reports) == 1:
        return reports[0]
    scored = tuple(row for item in reports for row in item.rows)
    return aggregate_report(
        scored,
        parse_failures=sum(item.parse_failures for item in reports),
        technical_failures=sum(item.technical_failures for item in reports),
    )


def _write_report(path: Path, report: EvaluationReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "evaluated_rows": report.evaluated_rows,
        "parse_failures": report.parse_failures,
        "technical_failures": report.technical_failures,
        "coverage": report.coverage,
        "limitation_note": report.limitation_note,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
