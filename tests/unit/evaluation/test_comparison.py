"""Set-comparison tests — T027 (RED) / T028 (GREEN).

Compares normalized gold and predicted value sets for one
paper × promoter × property. Fixtures are synthetic frozensets.
"""
from __future__ import annotations

import pytest

from promoter_ai_extraction.evaluation.comparison import (
    ComparisonOutcome,
    RowComparison,
    compare_sets,
    predicted_value_set,
)
from promoter_ai_extraction.models import (
    CandidateRejectionReason,
    EvidenceItem,
    ExtractedValue,
    Property,
    PropertyResult,
    RejectedCandidate,
    ScientificStatus,
    TechnicalFailure,
)


def _row(
    gold: frozenset[str],
    predicted: frozenset[str],
    *,
    property: Property = Property.CAJA_10,
) -> RowComparison:
    return compare_sets(
        paper_id="PMC1",
        promoter_name="lacZp1",
        property=property,
        gold_value_set=gold,
        predicted_value_set=predicted,
        modalidad_origen="texto_explicito",
    )


def test_exact_single_value_is_exact_match() -> None:
    row = _row(frozenset({"-42"}), frozenset({"-42"}), property=Property.TSS)
    assert row.outcome is ComparisonOutcome.EXACT_MATCH
    assert (row.tp, row.fp, row.fn) == (1, 0, 0)
    assert row.paper_id == "PMC1"
    assert row.promoter_name == "lacZp1"
    assert row.property is Property.TSS


def test_exact_set_match_for_two_caja10_values() -> None:
    gold = frozenset({"TAATAA", "TATAAT"})
    row = _row(gold, frozenset({"TATAAT", "TAATAA"}))
    assert row.outcome is ComparisonOutcome.EXACT_MATCH
    assert (row.tp, row.fp, row.fn) == (2, 0, 0)


def test_partial_match_recovers_subset_without_extras() -> None:
    gold = frozenset({"TAATAA", "TATAAT"})
    row = _row(gold, frozenset({"TAATAA"}))
    assert row.outcome is ComparisonOutcome.PARTIAL_MATCH
    assert (row.tp, row.fp, row.fn) == (1, 0, 1)


def test_extra_value_adds_unsupported_prediction() -> None:
    gold = frozenset({"TAATAA"})
    row = _row(gold, frozenset({"TAATAA", "TATAAT"}))
    assert row.outcome is ComparisonOutcome.EXTRA_VALUE
    assert (row.tp, row.fp, row.fn) == (1, 1, 0)


def test_extra_and_miss_is_extra_value_not_exact() -> None:
    gold = frozenset({"TAATAA", "TATAAT"})
    row = _row(gold, frozenset({"TAATAA", "TTGACA"}))
    assert row.outcome is ComparisonOutcome.EXTRA_VALUE
    assert (row.tp, row.fp, row.fn) == (1, 1, 1)


def test_wrong_value_has_empty_intersection() -> None:
    row = _row(frozenset({"-42"}), frozenset({"-41"}), property=Property.TSS)
    assert row.outcome is ComparisonOutcome.WRONG_VALUE
    assert (row.tp, row.fp, row.fn) == (0, 1, 1)


def test_miss_when_prediction_is_empty() -> None:
    row = _row(frozenset({"-42"}), frozenset(), property=Property.TSS)
    assert row.outcome is ComparisonOutcome.MISS
    assert (row.tp, row.fp, row.fn) == (0, 0, 1)


@pytest.mark.parametrize(
    "status",
    [
        ScientificStatus.NOT_FOUND,
        ScientificStatus.INSUFFICIENT_EVIDENCE,
        ScientificStatus.UNSUPPORTED_MODALITY,
        ScientificStatus.AMBIGUOUS,
    ],
)
def test_abstention_on_positive_target_is_miss(status: ScientificStatus) -> None:
    result = PropertyResult(
        paper_id="PMC1",
        promoter_name="lacZp1",
        property=Property.TSS,
        status=status,
        values=(),
        candidate_values=(),
        evidence=(),
        abstention_reason="synthetic abstention",
    )
    predicted = predicted_value_set(result)
    assert predicted == frozenset()
    row = _row(frozenset({"-42"}), predicted, property=Property.TSS)
    assert row.outcome is ComparisonOutcome.MISS
    assert row.fn == 1
    assert row.fp == 0


def test_rejected_candidate_does_not_count_as_prediction() -> None:
    evidence = EvidenceItem("frag", "seg:1", "body_text", "line 1")
    result = PropertyResult(
        paper_id="PMC1",
        promoter_name="lacZp1",
        property=Property.TSS,
        status=ScientificStatus.NOT_FOUND,
        values=(),
        candidate_values=(
            RejectedCandidate(
                candidate_raw="-99",
                rejection_reason=CandidateRejectionReason.INVALID_CANDIDATE,
                evidence=evidence,
                rule_violated="synthetic",
            ),
        ),
        evidence=(),
        abstention_reason="no accepted value",
    )
    assert predicted_value_set(result) == frozenset()


def test_extracted_values_form_the_predicted_set() -> None:
    evidence = EvidenceItem("The TSS was at -42.", "seg:1", "body_text", "line 1")
    result = PropertyResult(
        paper_id="PMC1",
        promoter_name="lacZp1",
        property=Property.TSS,
        status=ScientificStatus.EXTRACTED,
        values=(
            ExtractedValue("-42", "-42", None, None, (evidence,)),
        ),
        candidate_values=(),
        evidence=(evidence,),
        abstention_reason=None,
    )
    assert predicted_value_set(result) == frozenset({"-42"})


def test_technical_failure_has_no_predicted_set() -> None:
    failure = TechnicalFailure(
        stage="extraction",
        code="BACKEND_ERROR",
        message="backend failed",
        cause="TimeoutError",
    )
    assert predicted_value_set(failure) is None
