"""Normalized-set comparison for one paper × promoter × property (T028)."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from promoter_ai_extraction.models import (
    Property,
    PropertyAttempt,
    ScientificStatus,
    TechnicalFailure,
)

__all__ = [
    "ComparisonOutcome",
    "RowComparison",
    "compare_sets",
    "predicted_value_set",
]


class ComparisonOutcome(StrEnum):
    """Row-level comparison category from the evaluation contract §15."""

    EXACT_MATCH = "EXACT_MATCH"
    PARTIAL_MATCH = "PARTIAL_MATCH"
    WRONG_VALUE = "WRONG_VALUE"
    MISS = "MISS"
    EXTRA_VALUE = "EXTRA_VALUE"


@dataclass(frozen=True, slots=True)
class RowComparison:
    """Scored comparison for one paper × promoter × property unit."""

    paper_id: str
    promoter_name: str
    property: Property
    outcome: ComparisonOutcome
    tp: int
    fp: int
    fn: int
    gold_value_set: frozenset[str]
    predicted_value_set: frozenset[str]
    modalidad_origen: str | None


def predicted_value_set(attempt: PropertyAttempt) -> frozenset[str] | None:
    """Accepted predicted values, or None when the attempt is a technical failure.

    Rejected candidates never contribute. Abstention yields an empty set.
    """
    if isinstance(attempt, TechnicalFailure):
        return None
    if attempt.status is not ScientificStatus.EXTRACTED:
        return frozenset()
    return frozenset(value.value_normalized for value in attempt.values)


def compare_sets(
    *,
    paper_id: str,
    promoter_name: str,
    property: Property,
    gold_value_set: frozenset[str],
    predicted_value_set: frozenset[str],
    modalidad_origen: str | None = None,
) -> RowComparison:
    """Score two already-normalized value sets (evaluation contract §14–§16)."""
    tp = len(gold_value_set & predicted_value_set)
    fp = len(predicted_value_set - gold_value_set)
    fn = len(gold_value_set - predicted_value_set)
    outcome = _classify(gold_value_set, predicted_value_set, tp, fp, fn)
    return RowComparison(
        paper_id=paper_id,
        promoter_name=promoter_name,
        property=property,
        outcome=outcome,
        tp=tp,
        fp=fp,
        fn=fn,
        gold_value_set=gold_value_set,
        predicted_value_set=predicted_value_set,
        modalidad_origen=modalidad_origen,
    )


def _classify(
    gold: frozenset[str],
    predicted: frozenset[str],
    tp: int,
    fp: int,
    fn: int,
) -> ComparisonOutcome:
    if not predicted:
        return ComparisonOutcome.MISS
    if gold == predicted:
        return ComparisonOutcome.EXACT_MATCH
    if fp == 0 and tp > 0 and fn > 0:
        return ComparisonOutcome.PARTIAL_MATCH
    if tp > 0 and fp > 0:
        return ComparisonOutcome.EXTRA_VALUE
    return ComparisonOutcome.WRONG_VALUE
