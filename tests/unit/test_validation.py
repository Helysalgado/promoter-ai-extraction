"""Failing tests for OutputValidator (T013).

RED: collection fails because promoter_ai_extraction.validation does not
exist yet.  After T014 implementation all tests pass (GREEN).

Coverage:
- AC-05: every accepted value is linked to evidence from the supplied document.
- AC-09: multiple values, each with individual evidence, are valid.
- AC-11: AMBIGUOUS result with zero values and candidates is valid.
- AC-12: INSUFFICIENT_EVIDENCE with zero values is valid.
- AC-13: UNSUPPORTED_MODALITY with zero values is valid.
- AC-17: validator accepts well-formed results.
- AC-18: validator rejects: empty EXTRACTED, value without evidence, abstention
  with accepted values.
- AC-30: INVALID_CANDIDATE stays in candidate_values, never in values.
- Constitution principle 6: validation failure is a TechnicalFailure, not a
  scientific abstention.
- Identity match: paper_id, promoter_name, and property must match request.
- Evidence grounding: segment_id in each EvidenceItem must exist in document.
"""
from __future__ import annotations

import pytest

from promoter_ai_extraction.documents import DocumentSegment, LoadedDocument
from promoter_ai_extraction.boundary import ExtractionRequest
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
from promoter_ai_extraction.validation import OutputValidator


# ─── Helpers ─────────────────────────────────────────────────────────────────

_SEG_ID = "txt:p:0001"
_SEG_TEXT = "The TSS was mapped to -42 upstream of the ATG start codon."


def _make_document(
    paper_id: str = "PMC12345",
    seg_id: str = _SEG_ID,
    seg_text: str = _SEG_TEXT,
) -> LoadedDocument:
    return LoadedDocument(
        paper_id=paper_id,
        format="TXT",
        segments=(
            DocumentSegment(
                segment_id=seg_id,
                text=seg_text,
                source_type="body_text",
                location="line 1",
            ),
        ),
        document_hash="deadbeef" * 8,
    )


def _make_evidence(
    seg_id: str = _SEG_ID,
    fragment: str = "TSS was mapped to -42",
) -> EvidenceItem:
    return EvidenceItem(
        fragment=fragment,
        segment_id=seg_id,
        source_type="body_text",
        location="line 1",
    )


def _make_value(
    raw: str = "-42",
    normalized: str = "-42",
    seg_id: str = _SEG_ID,
) -> ExtractedValue:
    return ExtractedValue(
        value_raw=raw,
        value_normalized=normalized,
        qualifier=None,
        derivation_note=None,
        evidence=(_make_evidence(seg_id=seg_id),),
    )


def _make_request(
    document: LoadedDocument | None = None,
    paper_id: str = "PMC12345",
    promoter_name: str = "lacZp1",
    prop: Property = Property.TSS,
) -> ExtractionRequest:
    doc = document or _make_document(paper_id=paper_id)
    return ExtractionRequest(
        document=doc,
        paper_id=paper_id,
        promoter_id=None,
        promoter_name=promoter_name,
        paper_gene_synonym=None,
        property=prop,
    )


def _make_extracted_result(
    paper_id: str = "PMC12345",
    promoter_name: str = "lacZp1",
    prop: Property = Property.TSS,
    values: tuple[ExtractedValue, ...] | None = None,
) -> PropertyResult:
    v = values if values is not None else (_make_value(),)
    return PropertyResult(
        paper_id=paper_id,
        promoter_name=promoter_name,
        property=prop,
        status=ScientificStatus.EXTRACTED,
        values=v,
        candidate_values=(),
        evidence=(),
        abstention_reason=None,
    )


def _make_abstention_result(
    status: ScientificStatus = ScientificStatus.NOT_FOUND,
    paper_id: str = "PMC12345",
    promoter_name: str = "lacZp1",
    prop: Property = Property.TSS,
    result_evidence: tuple[EvidenceItem, ...] = (),
    candidates: tuple[RejectedCandidate, ...] = (),
) -> PropertyResult:
    return PropertyResult(
        paper_id=paper_id,
        promoter_name=promoter_name,
        property=prop,
        status=status,
        values=(),
        candidate_values=candidates,
        evidence=result_evidence,
        abstention_reason="No evidence found for this property.",
    )


# ─── Tests: valid (AC-17) ─────────────────────────────────────────────────────


class TestValidatorAcceptsValidResults:
    """OutputValidator returns the PropertyResult unchanged for valid inputs."""

    def test_valid_extracted_result_returned(self) -> None:
        """AC-17: well-formed EXTRACTED result passes validation."""
        document = _make_document()
        request = _make_request(document=document)
        result = _make_extracted_result()
        validator = OutputValidator()
        validated = validator.validate(result, request, document)
        assert isinstance(validated, PropertyResult)
        assert validated.status == ScientificStatus.EXTRACTED

    def test_not_found_with_zero_values_accepted(self) -> None:
        """AC-17: NOT_FOUND with empty values is valid."""
        document = _make_document()
        request = _make_request(document=document)
        result = _make_abstention_result(status=ScientificStatus.NOT_FOUND)
        validator = OutputValidator()
        validated = validator.validate(result, request, document)
        assert isinstance(validated, PropertyResult)
        assert validated.status == ScientificStatus.NOT_FOUND

    def test_insufficient_evidence_with_zero_values_accepted(self) -> None:
        """AC-12 / AC-17: INSUFFICIENT_EVIDENCE with empty values is valid."""
        document = _make_document()
        request = _make_request(document=document)
        result_ev = (_make_evidence(),)
        result = _make_abstention_result(
            status=ScientificStatus.INSUFFICIENT_EVIDENCE,
            result_evidence=result_ev,
        )
        validator = OutputValidator()
        validated = validator.validate(result, request, document)
        assert isinstance(validated, PropertyResult)

    def test_ambiguous_with_zero_values_and_candidates_accepted(self) -> None:
        """AC-11 / AC-17: AMBIGUOUS with zero values and some candidates is valid."""
        document = _make_document()
        request = _make_request(document=document)
        candidate = RejectedCandidate(
            candidate_raw="-42",
            rejection_reason=CandidateRejectionReason.INVALID_CANDIDATE,
            evidence=_make_evidence(),
            rule_violated="ambiguous promoter association",
        )
        result = _make_abstention_result(
            status=ScientificStatus.AMBIGUOUS,
            result_evidence=(_make_evidence(),),
            candidates=(candidate,),
        )
        validator = OutputValidator()
        validated = validator.validate(result, request, document)
        assert isinstance(validated, PropertyResult)

    def test_unsupported_modality_with_zero_values_accepted(self) -> None:
        """AC-13 / AC-17: UNSUPPORTED_MODALITY with documentary pointer is valid."""
        document = _make_document()
        request = _make_request(document=document)
        result = _make_abstention_result(
            status=ScientificStatus.UNSUPPORTED_MODALITY,
            result_evidence=(_make_evidence(),),
        )
        validator = OutputValidator()
        validated = validator.validate(result, request, document)
        assert isinstance(validated, PropertyResult)

    def test_multiple_values_each_with_evidence_accepted(self) -> None:
        """AC-09 / AC-17: multiple accepted values, each with evidence, are valid."""
        document = LoadedDocument(
            paper_id="PMC12345",
            format="TXT",
            segments=(
                DocumentSegment(
                    segment_id="txt:p:0001",
                    text="TSS-A at -42.",
                    source_type="body_text",
                    location="line 1",
                ),
                DocumentSegment(
                    segment_id="txt:p:0002",
                    text="TSS-B at -38.",
                    source_type="body_text",
                    location="line 2",
                ),
            ),
            document_hash="cafe" * 16,
        )
        request = _make_request(document=document)
        val_a = ExtractedValue(
            value_raw="-42",
            value_normalized="-42",
            qualifier=None,
            derivation_note=None,
            evidence=(
                EvidenceItem(
                    fragment="TSS-A at -42.",
                    segment_id="txt:p:0001",
                    source_type="body_text",
                    location="line 1",
                ),
            ),
        )
        val_b = ExtractedValue(
            value_raw="-38",
            value_normalized="-38",
            qualifier=None,
            derivation_note=None,
            evidence=(
                EvidenceItem(
                    fragment="TSS-B at -38.",
                    segment_id="txt:p:0002",
                    source_type="body_text",
                    location="line 2",
                ),
            ),
        )
        result = PropertyResult(
            paper_id="PMC12345",
            promoter_name="lacZp1",
            property=Property.TSS,
            status=ScientificStatus.EXTRACTED,
            values=(val_a, val_b),
            candidate_values=(),
            evidence=(),
            abstention_reason=None,
        )
        validator = OutputValidator()
        validated = validator.validate(result, request, document)
        assert isinstance(validated, PropertyResult)
        assert len(validated.values) == 2

    def test_result_returned_unchanged_on_success(self) -> None:
        """Validated result is the same object (not a copy with altered fields)."""
        document = _make_document()
        request = _make_request(document=document)
        result = _make_extracted_result()
        validator = OutputValidator()
        validated = validator.validate(result, request, document)
        assert validated is result


# ─── Tests: rejected (AC-18) ─────────────────────────────────────────────────


class TestValidatorRejectsInvalidResults:
    """OutputValidator returns TechnicalFailure for malformed results."""

    def test_extracted_with_no_values_rejected(self) -> None:
        """AC-18: EXTRACTED with empty values tuple is a validation failure."""
        document = _make_document()
        request = _make_request(document=document)
        result = _make_extracted_result(values=())
        validator = OutputValidator()
        outcome = validator.validate(result, request, document)
        assert isinstance(outcome, TechnicalFailure)

    def test_extracted_value_with_empty_evidence_rejected(self) -> None:
        """AC-18: a value with an empty evidence tuple is a validation failure."""
        document = _make_document()
        request = _make_request(document=document)
        bad_value = ExtractedValue(
            value_raw="-42",
            value_normalized="-42",
            qualifier=None,
            derivation_note=None,
            evidence=(),  # empty — forbidden
        )
        result = _make_extracted_result(values=(bad_value,))
        validator = OutputValidator()
        outcome = validator.validate(result, request, document)
        assert isinstance(outcome, TechnicalFailure)

    def test_abstention_with_accepted_values_rejected(self) -> None:
        """AC-18: NOT_FOUND result that still contains accepted values is invalid."""
        document = _make_document()
        request = _make_request(document=document)
        result = PropertyResult(
            paper_id="PMC12345",
            promoter_name="lacZp1",
            property=Property.TSS,
            status=ScientificStatus.NOT_FOUND,
            values=(_make_value(),),  # must be empty for abstentions
            candidate_values=(),
            evidence=(),
            abstention_reason="Not found.",
        )
        validator = OutputValidator()
        outcome = validator.validate(result, request, document)
        assert isinstance(outcome, TechnicalFailure)

    def test_ambiguous_with_accepted_values_rejected(self) -> None:
        """AMBIGUOUS result with non-empty values is invalid."""
        document = _make_document()
        request = _make_request(document=document)
        result = PropertyResult(
            paper_id="PMC12345",
            promoter_name="lacZp1",
            property=Property.TSS,
            status=ScientificStatus.AMBIGUOUS,
            values=(_make_value(),),
            candidate_values=(),
            evidence=(_make_evidence(),),
            abstention_reason="Ambiguous.",
        )
        validator = OutputValidator()
        outcome = validator.validate(result, request, document)
        assert isinstance(outcome, TechnicalFailure)

    def test_identity_mismatch_paper_id_rejected(self) -> None:
        """Identity: result.paper_id differs from request.paper_id → failure."""
        document = _make_document()
        request = _make_request(document=document, paper_id="PMC12345")
        result = _make_extracted_result(paper_id="PMC99999")  # wrong
        validator = OutputValidator()
        outcome = validator.validate(result, request, document)
        assert isinstance(outcome, TechnicalFailure)

    def test_identity_mismatch_promoter_name_rejected(self) -> None:
        """Identity: result.promoter_name differs from request.promoter_name → failure."""
        document = _make_document()
        request = _make_request(document=document, promoter_name="lacZp1")
        result = _make_extracted_result(promoter_name="wrong_promoter")
        validator = OutputValidator()
        outcome = validator.validate(result, request, document)
        assert isinstance(outcome, TechnicalFailure)

    def test_identity_mismatch_property_rejected(self) -> None:
        """Identity: result.property differs from request.property → failure."""
        document = _make_document()
        request = _make_request(document=document, prop=Property.TSS)
        result = PropertyResult(
            paper_id="PMC12345",
            promoter_name="lacZp1",
            property=Property.CAJA_10,  # wrong property
            status=ScientificStatus.EXTRACTED,
            values=(_make_value(),),
            candidate_values=(),
            evidence=(),
            abstention_reason=None,
        )
        validator = OutputValidator()
        outcome = validator.validate(result, request, document)
        assert isinstance(outcome, TechnicalFailure)

    def test_evidence_segment_not_in_document_rejected(self) -> None:
        """AC-05: evidence referencing an absent segment_id → validation failure."""
        document = _make_document(seg_id="txt:p:0001")
        request = _make_request(document=document)
        bad_evidence = EvidenceItem(
            fragment="Some text.",
            segment_id="txt:p:DOES_NOT_EXIST",
            source_type="body_text",
            location=None,
        )
        bad_value = ExtractedValue(
            value_raw="-42",
            value_normalized="-42",
            qualifier=None,
            derivation_note=None,
            evidence=(bad_evidence,),
        )
        result = _make_extracted_result(values=(bad_value,))
        validator = OutputValidator()
        outcome = validator.validate(result, request, document)
        assert isinstance(outcome, TechnicalFailure)

    def test_evidence_fragment_not_in_referenced_segment_rejected(self) -> None:
        """A segment id alone cannot ground a fragment absent from that segment."""
        document = _make_document()
        request = _make_request(document=document)
        bad_value = _make_value()
        bad_value = ExtractedValue(
            value_raw=bad_value.value_raw,
            value_normalized=bad_value.value_normalized,
            qualifier=None,
            derivation_note=None,
            evidence=(_make_evidence(fragment="invented documentary claim"),),
        )
        outcome = OutputValidator().validate(
            _make_extracted_result(values=(bad_value,)), request, document
        )
        assert isinstance(outcome, TechnicalFailure)

    def test_evidence_location_mismatch_rejected(self) -> None:
        """Evidence location must be the location of its referenced segment."""
        document = _make_document()
        request = _make_request(document=document)
        evidence = EvidenceItem(
            fragment="TSS was mapped to -42",
            segment_id=_SEG_ID,
            source_type="body_text",
            location="line 999",
        )
        value = ExtractedValue("-42", "-42", None, None, (evidence,))
        outcome = OutputValidator().validate(
            _make_extracted_result(values=(value,)), request, document
        )
        assert isinstance(outcome, TechnicalFailure)

    @pytest.mark.parametrize(
        "status",
        [
            ScientificStatus.INSUFFICIENT_EVIDENCE,
            ScientificStatus.UNSUPPORTED_MODALITY,
            ScientificStatus.AMBIGUOUS,
        ],
    )
    def test_evidence_required_abstention_without_evidence_rejected(
        self, status: ScientificStatus
    ) -> None:
        """Evidence-bearing abstentions cannot rely on a reason alone."""
        document = _make_document()
        request = _make_request(document=document)
        result = _make_abstention_result(status=status)
        outcome = OutputValidator().validate(result, request, document)
        assert isinstance(outcome, TechnicalFailure)

    def test_abstention_without_reason_rejected(self) -> None:
        """Every scientific abstention must contain a non-empty reason."""
        document = _make_document()
        request = _make_request(document=document)
        result = PropertyResult(
            paper_id=request.paper_id,
            promoter_name=request.promoter_name,
            property=request.property,
            status=ScientificStatus.NOT_FOUND,
            values=(),
            candidate_values=(),
            evidence=(),
            abstention_reason=None,
        )
        outcome = OutputValidator().validate(result, request, document)
        assert isinstance(outcome, TechnicalFailure)

    def test_extracted_with_abstention_reason_rejected(self) -> None:
        """EXTRACTED cannot simultaneously claim scientific abstention."""
        document = _make_document()
        request = _make_request(document=document)
        valid = _make_extracted_result()
        result = PropertyResult(
            paper_id=valid.paper_id,
            promoter_name=valid.promoter_name,
            property=valid.property,
            status=valid.status,
            values=valid.values,
            candidate_values=(),
            evidence=(),
            abstention_reason="conflicting reason",
        )
        outcome = OutputValidator().validate(result, request, document)
        assert isinstance(outcome, TechnicalFailure)

    def test_validation_failure_code_not_a_scientific_status(self) -> None:
        """Constitution principle 6: TechnicalFailure.code ≠ any ScientificStatus."""
        document = _make_document()
        request = _make_request(document=document)
        result = _make_extracted_result(values=())  # empty EXTRACTED
        validator = OutputValidator()
        outcome = validator.validate(result, request, document)
        assert isinstance(outcome, TechnicalFailure)
        scientific_codes = {s.value for s in ScientificStatus}
        assert outcome.code not in scientific_codes

    def test_validation_failure_stage_is_validation(self) -> None:
        """TechnicalFailure from validation carries stage='validation'."""
        document = _make_document()
        request = _make_request(document=document)
        result = _make_extracted_result(values=())
        validator = OutputValidator()
        outcome = validator.validate(result, request, document)
        assert isinstance(outcome, TechnicalFailure)
        assert outcome.stage == "validation"


# ─── Tests: INVALID_CANDIDATE (AC-30) ────────────────────────────────────────


class TestInvalidCandidateSeparation:
    """INVALID_CANDIDATE stays in candidate_values and never leaks into values."""

    def test_result_with_invalid_candidate_and_abstention_accepted(self) -> None:
        """AC-30: NOT_FOUND with an INVALID_CANDIDATE diagnostic is valid."""
        document = _make_document()
        request = _make_request(document=document)
        candidate = RejectedCandidate(
            candidate_raw="-42",
            rejection_reason=CandidateRejectionReason.INVALID_CANDIDATE,
            evidence=_make_evidence(),
            rule_violated="promoter association could not be established",
        )
        result = PropertyResult(
            paper_id="PMC12345",
            promoter_name="lacZp1",
            property=Property.TSS,
            status=ScientificStatus.NOT_FOUND,
            values=(),
            candidate_values=(candidate,),
            evidence=(),
            abstention_reason="Candidate found but association unresolvable.",
        )
        validator = OutputValidator()
        outcome = validator.validate(result, request, document)
        # The result is valid: candidate stays in candidate_values, not in values
        assert isinstance(outcome, PropertyResult)
        assert len(outcome.values) == 0
        assert len(outcome.candidate_values) == 1

    def test_invalid_candidate_not_promoted_to_values(self) -> None:
        """AC-30: a candidate marked INVALID_CANDIDATE must not appear in values.

        The validator accepts a result that correctly keeps the candidate
        separate from accepted values.  There is no API surface that would
        let the extractor 'promote' a RejectedCandidate to ExtractedValue —
        this test confirms the types enforce the boundary and validation
        agrees with a correctly separated result.
        """
        document = _make_document()
        request = _make_request(document=document)
        # Correct: candidate in candidate_values, values empty → abstention
        candidate = RejectedCandidate(
            candidate_raw="TATAAT",
            rejection_reason=CandidateRejectionReason.INVALID_CANDIDATE,
            evidence=_make_evidence(),
            rule_violated="no promoter association",
        )
        result = PropertyResult(
            paper_id="PMC12345",
            promoter_name="lacZp1",
            property=Property.TSS,
            status=ScientificStatus.AMBIGUOUS,
            values=(),
            candidate_values=(candidate,),
            evidence=(_make_evidence(),),
            abstention_reason="Candidate present but unresolvable.",
        )
        validator = OutputValidator()
        outcome = validator.validate(result, request, document)
        assert isinstance(outcome, PropertyResult)
        assert all(isinstance(v, ExtractedValue) for v in outcome.values)

    def test_same_invalid_candidate_raw_cannot_be_accepted(self) -> None:
        """AC-30: a rejected candidate cannot also appear as an accepted value."""
        document = _make_document()
        request = _make_request(document=document)
        candidate = RejectedCandidate(
            candidate_raw="-42",
            rejection_reason=CandidateRejectionReason.INVALID_CANDIDATE,
            evidence=_make_evidence(),
            rule_violated="association is ambiguous",
        )
        valid = _make_extracted_result()
        result = PropertyResult(
            paper_id=valid.paper_id,
            promoter_name=valid.promoter_name,
            property=valid.property,
            status=valid.status,
            values=valid.values,
            candidate_values=(candidate,),
            evidence=(),
            abstention_reason=None,
        )
        outcome = OutputValidator().validate(result, request, document)
        assert isinstance(outcome, TechnicalFailure)
