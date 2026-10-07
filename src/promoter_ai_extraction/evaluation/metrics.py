"""Per-property metrics, coverage, and paper-grouped split validation (T030)."""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from promoter_ai_extraction.evaluation.comparison import (
    ComparisonOutcome,
    RowComparison,
)
from promoter_ai_extraction.models import Property, ScientificStatus

__all__ = [
    "POSITIVE_ONLY_LIMITATION",
    "EvaluationReport",
    "PropertyMetrics",
    "SplitValidationError",
    "aggregate_report",
    "validate_paper_grouped_splits",
]

POSITIVE_ONLY_LIMITATION = (
    "This report is limited to the current positive-only workset. "
    "It does not claim a complete documentary false-assertion rate "
    "or complete appropriateness of abstention."
)


@dataclass(frozen=True, slots=True)
class PropertyMetrics:
    property: Property
    n_targets: int
    n_predictions_with_value: int
    tp: int
    fp: int
    fn: int
    precision: float
    recall: float
    f1: float
    exact_row_accuracy: float
    recall_texto_explicito: float | None
    recall_imagen_only: float | None


@dataclass(frozen=True, slots=True)
class EvaluationReport:
    by_property: dict[Property, PropertyMetrics]
    evaluated_rows: int
    parse_failures: int
    technical_failures: int
    coverage: float
    limitation_note: str
    rows: tuple[RowComparison, ...]


@dataclass(frozen=True, slots=True)
class SplitValidationError:
    stage: str
    code: str
    message: str
    cause: str

    def __post_init__(self) -> None:
        if self.code in {status.value for status in ScientificStatus}:
            raise ValueError(
                "SplitValidationError.code must not equal a ScientificStatus value."
            )


def aggregate_report(
    rows: Iterable[RowComparison],
    *,
    parse_failures: int,
    technical_failures: int,
) -> EvaluationReport:
    scored = tuple(rows)
    by_property: dict[Property, PropertyMetrics] = {}
    for prop in Property:
        by_property[prop] = _metrics_for(prop, [row for row in scored if row.property is prop])
    evaluated = len(scored)
    coverage_denom = evaluated + technical_failures
    coverage = evaluated / coverage_denom if coverage_denom else 0.0
    return EvaluationReport(
        by_property=by_property,
        evaluated_rows=evaluated,
        parse_failures=parse_failures,
        technical_failures=technical_failures,
        coverage=coverage,
        limitation_note=POSITIVE_ONLY_LIMITATION,
        rows=scored,
    )


def validate_paper_grouped_splits(
    *,
    development_paper_ids: frozenset[str],
    test_paper_ids: frozenset[str],
) -> SplitValidationError | None:
    leaked = development_paper_ids & test_paper_ids
    if not leaked:
        return None
    leaked_list = ", ".join(sorted(leaked))
    return SplitValidationError(
        stage="split_validation",
        code="PAPER_SPLIT_LEAKAGE",
        message=(
            "Development and test splits share paper identifiers; "
            f"every row from one paper must stay on one side. Shared: {leaked_list}."
        ),
        cause="ValueError",
    )


def _metrics_for(prop: Property, rows: list[RowComparison]) -> PropertyMetrics:
    tp = sum(row.tp for row in rows)
    fp = sum(row.fp for row in rows)
    fn = sum(row.fn for row in rows)
    n_targets = len(rows)
    n_pred = sum(1 for row in rows if row.predicted_value_set)
    exact = sum(1 for row in rows if row.outcome is ComparisonOutcome.EXACT_MATCH)
    return PropertyMetrics(
        property=prop,
        n_targets=n_targets,
        n_predictions_with_value=n_pred,
        tp=tp,
        fp=fp,
        fn=fn,
        precision=_ratio(tp, tp + fp),
        recall=_ratio(tp, tp + fn),
        f1=_f1(tp, fp, fn),
        exact_row_accuracy=_ratio(exact, n_targets),
        recall_texto_explicito=_stratum_recall(rows, "texto_explicito"),
        recall_imagen_only=_stratum_recall(rows, "imagen_only"),
    )


def _stratum_recall(rows: list[RowComparison], modalidad: str) -> float | None:
    stratum = [row for row in rows if row.modalidad_origen == modalidad]
    if not stratum:
        return None
    tp = sum(row.tp for row in stratum)
    fn = sum(row.fn for row in stratum)
    return _ratio(tp, tp + fn)


def _ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _f1(tp: int, fp: int, fn: int) -> float:
    precision = _ratio(tp, tp + fp)
    recall = _ratio(tp, tp + fn)
    if precision == 0.0 and recall == 0.0:
        return 0.0
    denom = precision + recall
    if denom == 0.0:
        return 0.0
    return 2 * precision * recall / denom
