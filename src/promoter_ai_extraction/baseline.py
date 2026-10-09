"""Local baseline runner: safe manifest → extract → persist → evaluate (T041/T042).

No UI and no HTTP service. Gold is reachable only through
``GuidedBaselineApplication``, which persists before ``EvaluationService``
opens the workbook.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from promoter_ai_extraction import __version__
from promoter_ai_extraction.application import GuidedBaselineApplication
from promoter_ai_extraction.backends import OpenAIModelBackend
from promoter_ai_extraction.boundary import BoundaryViolation, DevelopmentCase
from promoter_ai_extraction.documents import DocumentSource
from promoter_ai_extraction.evaluation.gold_parser import PARSER_VERSION
from promoter_ai_extraction.evaluation.metrics import EvaluationReport, aggregate_report
from promoter_ai_extraction.evaluation.report import serialize_benchmark_report
from promoter_ai_extraction.evaluation.service import EvaluationError
from promoter_ai_extraction.extraction import ModelBackend
from promoter_ai_extraction.manifest import DevelopmentManifestLoader, ManifestLoadError
from promoter_ai_extraction.models import Property, TechnicalFailure
from promoter_ai_extraction.persistence import PersistenceFailure

__all__ = ["BaselineRunner", "main"]


class BaselineRunner:
    """Path-based runner for leakage-safe local baseline cases."""

    def __init__(self, backend: ModelBackend) -> None:
        self._backend = backend
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
        _write_report(report, combined, backend=self._backend)
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


def main(
    argv: list[str] | None = None,
    *,
    backend: ModelBackend | None = None,
) -> int:
    parser = argparse.ArgumentParser(
        prog="promoter_ai_extraction.baseline",
        description="Run the leakage-safe guided extraction baseline locally.",
    )
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--documents", type=Path, required=True)
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)

    if backend is None:
        secret = (os.environ.get("OPENAI_API_KEY") or "").strip()
        if not secret:
            print("MISSING_CREDENTIAL: OPENAI_API_KEY is not set.", file=sys.stderr)
            return 1
        active: ModelBackend = OpenAIModelBackend()
    else:
        active = backend
    try:
        outcome = BaselineRunner(active).run(
            manifest=args.manifest,
            documents=args.documents,
            gold=args.gold,
            predictions=args.predictions,
            report=args.report,
        )
    except BoundaryViolation as exc:
        print(_failure_message(exc), file=sys.stderr)
        return 1
    if isinstance(outcome, EvaluationReport):
        return 0
    print(_failure_message(outcome), file=sys.stderr)
    return 1


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
    tf_by: dict[Property, int] = {prop: 0 for prop in Property}
    tf_gold: dict[Property, int] = {prop: 0 for prop in Property}
    for item in reports:
        for prop, count in item.technical_failures_by_property.items():
            tf_by[prop] += count
        for prop, count in item.technical_failure_gold_values.items():
            tf_gold[prop] += count
    return aggregate_report(
        scored,
        parse_failures=sum(item.parse_failures for item in reports),
        technical_failures=sum(item.technical_failures for item in reports),
        technical_failures_by_property=tf_by,
        technical_failure_gold_values=tf_gold,
    )


def _write_report(
    path: Path, report: EvaluationReport, *, backend: ModelBackend
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = serialize_benchmark_report(
        report,
        software_version=__version__,
        parser_version=PARSER_VERSION,
        model_versions=_model_versions(backend),
    )
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _model_versions(backend: ModelBackend) -> dict[str, object]:
    getter = getattr(backend, "reproducibility_metadata", None)
    if not callable(getter):
        return {}
    raw = getter()
    if not isinstance(raw, dict):
        return {}
    common = raw.get("common")
    if isinstance(common, dict):
        return dict(common)
    return {}


def _failure_message(outcome: object) -> str:
    stage = getattr(outcome, "stage", None)
    code = getattr(outcome, "code", type(outcome).__name__)
    message = getattr(outcome, "message", str(outcome))
    if stage:
        return f"{stage}: {code}: {message}"
    return f"{code}: {message}"


if __name__ == "__main__":
    raise SystemExit(main())
