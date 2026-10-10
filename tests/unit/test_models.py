"""Domain-contract tests for promoter_ai_extraction.models (T003/T004).

RED: these tests fail until T004 implements the domain contracts.

Covers:
  - Property enum (four properties)
  - ScientificStatus enum (five statuses, INVALID_CANDIDATE is NOT one of them)
  - CandidateRejectionReason (INVALID_CANDIDATE label)
  - EvidenceItem (fragment, segment_id, source_type, location fields)
  - ExtractedValue (value_raw, value_normalized, qualifier, derivation_note, evidence)
  - RejectedCandidate (candidate_raw, rejection_reason, evidence, rule_violated)
  - PropertyResult (identity + status + values + candidates + abstention)
  - TechnicalFailure (stage, code, message, cause)
  - PropertyAttempt (union alias for PropertyResult | TechnicalFailure)
  - Immutability of all frozen dataclasses
  - StrEnum membership checks and string-value equality
"""

from __future__ import annotations

import dataclasses
import pytest

from promoter_ai_extraction.models import (
    Property,
    ScientificStatus,
    CandidateRejectionReason,
    EvidenceItem,
    ExtractedValue,
    RejectedCandidate,
    PropertyResult,
    TechnicalFailure,
    PropertyAttempt,
)


# ---------------------------------------------------------------------------
# Property enum
# ---------------------------------------------------------------------------

class TestPropertyEnum:
    def test_four_properties_exist(self) -> None:
        members = {p.value for p in Property}
        assert "TSS" in members
        assert "Caja -10" in members
        assert "Caja -35" in members
        assert "Factor sigma" in members

    def test_exactly_four_members(self) -> None:
        assert len(Property) == 4

    def test_property_is_str(self) -> None:
        for prop in Property:
            assert isinstance(prop, str), f"{prop!r} should be str (StrEnum)"

    def test_property_names_canonical(self) -> None:
        assert Property.TSS.value == "TSS"
        assert Property.CAJA_10.value == "Caja -10"
        assert Property.CAJA_35.value == "Caja -35"
        assert Property.FACTOR_SIGMA.value == "Factor sigma"


# ---------------------------------------------------------------------------
# ScientificStatus enum
# ---------------------------------------------------------------------------

class TestScientificStatusEnum:
    def test_five_statuses_exist(self) -> None:
        assert len(ScientificStatus) == 5

    def test_extracted_status(self) -> None:
        assert ScientificStatus.EXTRACTED in ScientificStatus

    def test_not_found_status(self) -> None:
        assert ScientificStatus.NOT_FOUND in ScientificStatus

    def test_insufficient_evidence_status(self) -> None:
        assert ScientificStatus.INSUFFICIENT_EVIDENCE in ScientificStatus

    def test_unsupported_modality_status(self) -> None:
        assert ScientificStatus.UNSUPPORTED_MODALITY in ScientificStatus

    def test_ambiguous_status(self) -> None:
        assert ScientificStatus.AMBIGUOUS in ScientificStatus

    def test_invalid_candidate_is_not_a_scientific_status(self) -> None:
        """INVALID_CANDIDATE is a candidate-level diagnostic, NOT a ScientificStatus."""
        status_values = {s.value for s in ScientificStatus}
        assert "INVALID_CANDIDATE" not in status_values

    def test_status_is_str(self) -> None:
        for s in ScientificStatus:
            assert isinstance(s, str), f"{s!r} should be str (StrEnum)"


# ---------------------------------------------------------------------------
# CandidateRejectionReason — INVALID_CANDIDATE label lives here
# ---------------------------------------------------------------------------

class TestCandidateRejectionReason:
    def test_invalid_candidate_rejection_reason_exists(self) -> None:
        assert CandidateRejectionReason.INVALID_CANDIDATE is not None

    def test_invalid_candidate_has_string_value(self) -> None:
        assert isinstance(CandidateRejectionReason.INVALID_CANDIDATE, str)

    def test_invalid_candidate_value_is_not_empty(self) -> None:
        assert len(str(CandidateRejectionReason.INVALID_CANDIDATE)) > 0


# ---------------------------------------------------------------------------
# EvidenceItem
# ---------------------------------------------------------------------------

class TestEvidenceItem:
    def _make_item(self) -> EvidenceItem:
        return EvidenceItem(
            fragment="The TSS for promoter P is at position +1.",
            segment_id="seg-001",
            source_type="text",
            location="section:Results paragraph:2",
        )

    def test_evidence_item_can_be_created(self) -> None:
        item = self._make_item()
        assert item.fragment == "The TSS for promoter P is at position +1."
        assert item.segment_id == "seg-001"
        assert item.source_type == "text"
        assert item.location == "section:Results paragraph:2"

    def test_evidence_item_is_frozen(self) -> None:
        item = self._make_item()
        with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
            item.fragment = "modified"  # type: ignore[misc]

    def test_evidence_item_location_can_be_none(self) -> None:
        item = EvidenceItem(
            fragment="some text",
            segment_id="seg-002",
            source_type="caption",
            location=None,
        )
        assert item.location is None

    def test_evidence_item_is_hashable(self) -> None:
        item = self._make_item()
        # Frozen dataclasses should be hashable.
        _ = {item}


# ---------------------------------------------------------------------------
# ExtractedValue
# ---------------------------------------------------------------------------

class TestExtractedValue:
    def _make_evidence(self) -> EvidenceItem:
        return EvidenceItem(
            fragment="TSS at +1",
            segment_id="seg-001",
            source_type="text",
            location=None,
        )

    def test_extracted_value_basic(self) -> None:
        ev = ExtractedValue(
            value_raw="+1",
            value_normalized="+1",
            qualifier=None,
            derivation_note=None,
            evidence=(self._make_evidence(),),
        )
        assert ev.value_raw == "+1"
        assert ev.value_normalized == "+1"
        assert ev.qualifier is None
        assert ev.derivation_note is None
        assert len(ev.evidence) == 1

    def test_extracted_value_with_qualifier(self) -> None:
        ev = ExtractedValue(
            value_raw="putative TTGACA",
            value_normalized="TTGACA",
            qualifier="putative",
            derivation_note="qualifier stripped for normalization",
            evidence=(self._make_evidence(),),
        )
        assert ev.qualifier == "putative"
        assert ev.derivation_note == "qualifier stripped for normalization"

    def test_extracted_value_raw_and_normalized_can_differ(self) -> None:
        ev = ExtractedValue(
            value_raw="TATAAT\nTA",  # typographic line break in raw
            value_normalized="TATAATTA",
            qualifier=None,
            derivation_note="typographic line break removed",
            evidence=(self._make_evidence(),),
        )
        assert ev.value_raw != ev.value_normalized

    def test_extracted_value_is_frozen(self) -> None:
        ev = ExtractedValue(
            value_raw="x",
            value_normalized="x",
            qualifier=None,
            derivation_note=None,
            evidence=(self._make_evidence(),),
        )
        with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
            ev.value_raw = "y"  # type: ignore[misc]

    def test_extracted_value_accepts_zero_evidence(self) -> None:
        """ExtractedValue construction does NOT enforce non-empty evidence at the model
        layer; cardinality is the responsibility of OutputValidator (T013/T014).
        The model must accept an empty tuple without error."""
        ev = ExtractedValue(
            value_raw="x",
            value_normalized="x",
            qualifier=None,
            derivation_note=None,
            evidence=(),
        )
        assert ev.evidence == ()


# ---------------------------------------------------------------------------
# RejectedCandidate
# ---------------------------------------------------------------------------

class TestRejectedCandidate:
    def test_rejected_candidate_basic(self) -> None:
        rc = RejectedCandidate(
            candidate_raw="GCXYZ",
            rejection_reason=CandidateRejectionReason.INVALID_CANDIDATE,
            evidence=None,
            rule_violated="non-nucleotide characters present",
        )
        assert rc.candidate_raw == "GCXYZ"
        assert rc.rejection_reason == CandidateRejectionReason.INVALID_CANDIDATE
        assert rc.evidence is None
        assert rc.rule_violated == "non-nucleotide characters present"

    def test_rejected_candidate_is_frozen(self) -> None:
        rc = RejectedCandidate(
            candidate_raw="x",
            rejection_reason=CandidateRejectionReason.INVALID_CANDIDATE,
            evidence=None,
            rule_violated="reason",
        )
        with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
            rc.candidate_raw = "y"  # type: ignore[misc]

    def test_rejected_candidate_rejection_reason_is_not_scientific_status(self) -> None:
        """Rejection reason must not be a ScientificStatus value."""
        rc = RejectedCandidate(
            candidate_raw="x",
            rejection_reason=CandidateRejectionReason.INVALID_CANDIDATE,
            evidence=None,
            rule_violated="test",
        )
        scientific_status_values = {s.value for s in ScientificStatus}
        assert str(rc.rejection_reason) not in scientific_status_values


# ---------------------------------------------------------------------------
# PropertyResult
# ---------------------------------------------------------------------------

class TestPropertyResult:
    def _make_evidence(self) -> EvidenceItem:
        return EvidenceItem(
            fragment="TSS at +1",
            segment_id="seg-001",
            source_type="text",
            location=None,
        )

    def _make_value(self) -> ExtractedValue:
        return ExtractedValue(
            value_raw="+1",
            value_normalized="+1",
            qualifier=None,
            derivation_note=None,
            evidence=(self._make_evidence(),),
        )

    def test_extracted_result(self) -> None:
        result = PropertyResult(
            paper_id="PMID12345",
            promoter_name="pA",
            property=Property.TSS,
            status=ScientificStatus.EXTRACTED,
            values=(self._make_value(),),
            candidate_values=(),
            evidence=(),
            abstention_reason=None,
        )
        assert result.paper_id == "PMID12345"
        assert result.promoter_name == "pA"
        assert result.property == Property.TSS
        assert result.status == ScientificStatus.EXTRACTED
        assert len(result.values) == 1
        assert result.abstention_reason is None

    def test_not_found_result_has_no_values(self) -> None:
        result = PropertyResult(
            paper_id="PMID12345",
            promoter_name="pA",
            property=Property.CAJA_10,
            status=ScientificStatus.NOT_FOUND,
            values=(),
            candidate_values=(),
            evidence=(),
            abstention_reason="No Caja -10 evidence found in the supplied document.",
        )
        assert result.status == ScientificStatus.NOT_FOUND
        assert len(result.values) == 0
        assert result.abstention_reason is not None

    def test_insufficient_evidence_result(self) -> None:
        ev = self._make_evidence()
        result = PropertyResult(
            paper_id="PMID12345",
            promoter_name="pA",
            property=Property.CAJA_35,
            status=ScientificStatus.INSUFFICIENT_EVIDENCE,
            values=(),
            candidate_values=(),
            evidence=(ev,),
            abstention_reason="Relevant text found but no value could be confirmed.",
        )
        assert result.status == ScientificStatus.INSUFFICIENT_EVIDENCE
        assert len(result.values) == 0
        assert len(result.evidence) == 1

    def test_ambiguous_result_may_have_rejected_candidates(self) -> None:
        rc = RejectedCandidate(
            candidate_raw="X",
            rejection_reason=CandidateRejectionReason.INVALID_CANDIDATE,
            evidence=None,
            rule_violated="ambiguous association",
        )
        result = PropertyResult(
            paper_id="PMID12345",
            promoter_name="pA",
            property=Property.FACTOR_SIGMA,
            status=ScientificStatus.AMBIGUOUS,
            values=(),
            candidate_values=(rc,),
            evidence=(),
            abstention_reason="Multiple promoters mentioned; cannot assign sigma to pA specifically.",
        )
        assert result.status == ScientificStatus.AMBIGUOUS
        assert len(result.values) == 0
        assert len(result.candidate_values) == 1

    def test_multiple_values_stay_separate(self) -> None:
        v1 = self._make_value()
        v2 = ExtractedValue(
            value_raw="TATAAT",
            value_normalized="TATAAT",
            qualifier=None,
            derivation_note=None,
            evidence=(self._make_evidence(),),
        )
        result = PropertyResult(
            paper_id="PMID12345",
            promoter_name="pA",
            property=Property.CAJA_10,
            status=ScientificStatus.EXTRACTED,
            values=(v1, v2),
            candidate_values=(),
            evidence=(),
            abstention_reason=None,
        )
        assert len(result.values) == 2
        assert result.values[0] is not result.values[1]

    def test_property_result_is_frozen(self) -> None:
        result = PropertyResult(
            paper_id="p",
            promoter_name="n",
            property=Property.TSS,
            status=ScientificStatus.NOT_FOUND,
            values=(),
            candidate_values=(),
            evidence=(),
            abstention_reason=None,
        )
        with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
            result.paper_id = "other"  # type: ignore[misc]

    def test_invalid_candidate_does_not_appear_in_values(self) -> None:
        """AC-30: a rejected candidate must not be promoted to accepted values."""
        rc = RejectedCandidate(
            candidate_raw="x",
            rejection_reason=CandidateRejectionReason.INVALID_CANDIDATE,
            evidence=None,
            rule_violated="test rule",
        )
        result = PropertyResult(
            paper_id="PMID12345",
            promoter_name="pA",
            property=Property.TSS,
            status=ScientificStatus.NOT_FOUND,
            values=(),
            candidate_values=(rc,),
            evidence=(),
            abstention_reason="No value found.",
        )
        # No accepted value should come from a rejected candidate.
        assert len(result.values) == 0
        assert len(result.candidate_values) == 1


# ---------------------------------------------------------------------------
# TechnicalFailure
# ---------------------------------------------------------------------------

class TestTechnicalFailure:
    def test_technical_failure_basic(self) -> None:
        tf = TechnicalFailure(
            stage="document_loading",
            code="UNREADABLE_INPUT",
            message="The supplied file could not be read.",
            cause="FileNotFoundError",
        )
        assert tf.stage == "document_loading"
        assert tf.code == "UNREADABLE_INPUT"
        assert tf.message == "The supplied file could not be read."
        assert tf.cause == "FileNotFoundError"

    def test_technical_failure_is_frozen(self) -> None:
        tf = TechnicalFailure(
            stage="parsing",
            code="MALFORMED_XML",
            message="XML parse error.",
            cause="ParseError",
        )
        with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
            tf.code = "OTHER"  # type: ignore[misc]

    def test_technical_failure_code_is_not_a_scientific_status(self) -> None:
        """Constitution principle 6: technical failure stays distinct from scientific abstention."""
        tf = TechnicalFailure(
            stage="extraction",
            code="BACKEND_ERROR",
            message="Model call failed.",
            cause="TimeoutError",
        )
        scientific_status_values = {s.value for s in ScientificStatus}
        assert tf.code not in scientific_status_values

    def test_technical_failure_not_found_code_is_distinct(self) -> None:
        """NOT_FOUND is a scientific status; a technical failure must not use it as its code."""
        tf = TechnicalFailure(
            stage="validation",
            code="VALIDATION_FAILED",
            message="Output contract violated.",
            cause="ValidationError",
        )
        assert tf.code != "NOT_FOUND"
        assert tf.code != "INSUFFICIENT_EVIDENCE"

    # ------------------------------------------------------------------
    # Finding #1: __post_init__ must MECHANICALLY reject scientific codes.
    # These tests should be RED until __post_init__ is added.
    # ------------------------------------------------------------------

    @pytest.mark.parametrize("bad_code", [s.value for s in ScientificStatus])
    def test_technical_failure_rejects_scientific_status_code(self, bad_code: str) -> None:
        """TechnicalFailure.__post_init__ must raise ValueError (or similar) when
        the code equals any ScientificStatus value — constitution principle 6."""
        with pytest.raises((ValueError, TypeError)):
            TechnicalFailure(
                stage="extraction",
                code=bad_code,  # e.g. "NOT_FOUND", "EXTRACTED", …
                message="Should be rejected.",
                cause="Test",
            )

    def test_technical_failure_arbitrary_code_is_allowed(self) -> None:
        """Non-scientific stable codes must still construct without error."""
        tf = TechnicalFailure(
            stage="loading",
            code="UNREADABLE_INPUT",
            message="Cannot read file.",
            cause="OSError",
        )
        assert tf.code == "UNREADABLE_INPUT"


# ---------------------------------------------------------------------------
# PropertyAttempt — union type
# ---------------------------------------------------------------------------

class TestPropertyAttempt:
    def test_property_result_is_valid_attempt(self) -> None:
        result = PropertyResult(
            paper_id="PMID12345",
            promoter_name="pA",
            property=Property.TSS,
            status=ScientificStatus.NOT_FOUND,
            values=(),
            candidate_values=(),
            evidence=(),
            abstention_reason="Not found.",
        )
        # PropertyAttempt is a type alias; the object must be an instance of
        # PropertyResult or TechnicalFailure.
        assert isinstance(result, PropertyResult)

    def test_technical_failure_is_valid_attempt(self) -> None:
        tf = TechnicalFailure(
            stage="extraction",
            code="BACKEND_ERROR",
            message="Error.",
            cause="IOError",
        )
        assert isinstance(tf, TechnicalFailure)

    def test_property_attempt_type_exists(self) -> None:
        """PropertyAttempt must be importable (it may be a type alias or Union)."""
        # Simply importing it (done at module top) is sufficient evidence.
        assert PropertyAttempt is not None
