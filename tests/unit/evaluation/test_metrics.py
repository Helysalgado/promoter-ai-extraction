"""Metrics and split-validation tests — T029 (RED) / T030 (GREEN)."""
from __future__ import annotations

import pytest

from promoter_ai_extraction.evaluation.comparison import (
    ComparisonOutcome,
    RowComparison,
    compare_sets,
)
from promoter_ai_extraction.evaluation.metrics import (
    POSITIVE_ONLY_LIMITATION,
    SplitValidationError,
    aggregate_report,
    validate_paper_grouped_splits,
)
from promoter_ai_extraction.models import Property


def _cmp(
    paper_id: str,
    promoter: str,
    prop: Property,
    gold: frozenset[str],
    predicted: frozenset[str],
    modalidad: str | None = "texto_explicito",
) -> RowComparison:
    return compare_sets(
        paper_id=paper_id,
        promoter_name=promoter,
        property=prop,
        gold_value_set=gold,
        predicted_value_set=predicted,
        modalidad_origen=modalidad,
    )


def test_precision_recall_f1_and_exact_row_accuracy() -> None:
    rows = (
        _cmp("P1", "pr1", Property.TSS, frozenset({"-42"}), frozenset({"-42"})),
        _cmp("P1", "pr2", Property.TSS, frozenset({"-10"}), frozenset({"-11"})),
        _cmp("P2", "pr1", Property.TSS, frozenset({"-7"}), frozenset()),
    )
    report = aggregate_report(rows, parse_failures=0, technical_failures=0)
    tss = report.by_property[Property.TSS]
    assert tss.n_targets == 3
    assert tss.n_predictions_with_value == 2
    assert (tss.tp, tss.fp, tss.fn) == (1, 1, 2)
    assert tss.precision == pytest.approx(0.5)
    assert tss.recall == pytest.approx(1 / 3)
    assert tss.f1 == pytest.approx(0.4)
    assert tss.exact_row_accuracy == pytest.approx(1 / 3)


def test_metrics_are_separated_by_property() -> None:
    rows = (
        _cmp("P1", "pr1", Property.TSS, frozenset({"-42"}), frozenset({"-42"})),
        _cmp("P1", "pr1", Property.CAJA_10, frozenset({"TATAAT"}), frozenset()),
    )
    report = aggregate_report(rows, parse_failures=0, technical_failures=0)
    assert report.by_property[Property.TSS].recall == pytest.approx(1.0)
    assert report.by_property[Property.CAJA_10].recall == pytest.approx(0.0)
    assert report.by_property[Property.CAJA_35].n_targets == 0
    assert report.by_property[Property.FACTOR_SIGMA].n_targets == 0


def test_modality_strata_recall() -> None:
    rows = (
        _cmp(
            "P1",
            "pr1",
            Property.TSS,
            frozenset({"-42"}),
            frozenset({"-42"}),
            "texto_explicito",
        ),
        _cmp(
            "P2",
            "pr1",
            Property.TSS,
            frozenset({"-10"}),
            frozenset(),
            "imagen_only",
        ),
        _cmp(
            "P3",
            "pr1",
            Property.TSS,
            frozenset({"-7"}),
            frozenset({"-7"}),
            "imagen_only",
        ),
    )
    report = aggregate_report(rows, parse_failures=0, technical_failures=0)
    tss = report.by_property[Property.TSS]
    assert tss.recall == pytest.approx(2 / 3)
    assert tss.recall_texto_explicito == pytest.approx(1.0)
    assert tss.recall_imagen_only == pytest.approx(0.5)


def test_coverage_and_failure_counts_stay_separate() -> None:
    rows = (
        _cmp("P1", "pr1", Property.TSS, frozenset({"-42"}), frozenset({"-42"})),
    )
    report = aggregate_report(rows, parse_failures=2, technical_failures=3)
    assert report.evaluated_rows == 1
    assert report.parse_failures == 2
    assert report.technical_failures == 3
    assert report.coverage == pytest.approx(1 / 4)


def test_positive_only_limitation_is_stated() -> None:
    report = aggregate_report((), parse_failures=0, technical_failures=0)
    assert POSITIVE_ONLY_LIMITATION in report.limitation_note
    assert "false-assertion" in report.limitation_note
    assert "abstention" in report.limitation_note


def test_split_validator_rejects_paper_in_both_sides() -> None:
    error = validate_paper_grouped_splits(
        development_paper_ids=frozenset({"P1", "P2"}),
        test_paper_ids=frozenset({"P2", "P3"}),
    )
    assert isinstance(error, SplitValidationError)
    assert error.code == "PAPER_SPLIT_LEAKAGE"
    assert "P2" in error.message


def test_split_validator_accepts_disjoint_papers() -> None:
    outcome = validate_paper_grouped_splits(
        development_paper_ids=frozenset({"P1"}),
        test_paper_ids=frozenset({"P2"}),
    )
    assert outcome is None


def test_zero_denominator_metrics_are_zero() -> None:
    report = aggregate_report((), parse_failures=0, technical_failures=0)
    tss = report.by_property[Property.TSS]
    assert tss.precision == 0.0
    assert tss.recall == 0.0
    assert tss.f1 == 0.0
    assert tss.exact_row_accuracy == 0.0
