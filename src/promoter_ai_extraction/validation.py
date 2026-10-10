"""OutputValidator for the guided extraction baseline (T014).

The validator checks a :class:`~promoter_ai_extraction.models.PropertyResult`
against the originating :class:`~promoter_ai_extraction.boundary.ExtractionRequest`
and the :class:`~promoter_ai_extraction.documents.LoadedDocument` that was
supplied to the extractor.

Validation rules (from spec §Validation / §Accepted values / §Candidate
diagnostics, and constitution principle 6)
---------------------------------------------------------------------------
1. **Identity**: result.paper_id, result.promoter_name, and result.property
   must all match the corresponding request fields.

2. **Status / value consistency**:
   - ``EXTRACTED`` requires at least one accepted value.
   - All abstention statuses (NOT_FOUND, INSUFFICIENT_EVIDENCE,
     UNSUPPORTED_MODALITY, AMBIGUOUS) require zero accepted values.

3. **Per-value evidence**: every :class:`~promoter_ai_extraction.models.ExtractedValue`
   in an EXTRACTED result must carry at least one
   :class:`~promoter_ai_extraction.models.EvidenceItem`.

4. **Evidence grounding**: every ``EvidenceItem.segment_id`` referenced by an
   accepted value must exist in ``document.segments``.

5. **INVALID_CANDIDATE boundary** (AC-30): the validator does not need to
   re-enforce type separation (``values`` holds ``ExtractedValue`` instances
   and ``candidate_values`` holds ``RejectedCandidate`` instances — types
   enforce this), but it verifies the result structure is self-consistent.

Design
------
- ``validate`` never raises; it always returns either the original
  :class:`~promoter_ai_extraction.models.PropertyResult` or a
  :class:`~promoter_ai_extraction.models.TechnicalFailure`.
- Constitution principle 6: the ``TechnicalFailure.code`` is
  ``"VALIDATION_FAILED"``, which is not a :class:`~promoter_ai_extraction.models.ScientificStatus`
  value.
- The validator does not read gold data, call the backend, or perform any I/O.
"""
from __future__ import annotations

from promoter_ai_extraction.boundary import ExtractionRequest
from promoter_ai_extraction.documents import DocumentSegment, LoadedDocument
from promoter_ai_extraction.models import (
    EvidenceItem,
    PropertyResult,
    ScientificStatus,
    TechnicalFailure,
)

__all__ = ["OutputValidator"]

# Status values that require zero accepted values.
_ABSTENTION_STATUSES = frozenset(
    {
        ScientificStatus.NOT_FOUND,
        ScientificStatus.INSUFFICIENT_EVIDENCE,
        ScientificStatus.UNSUPPORTED_MODALITY,
        ScientificStatus.AMBIGUOUS,
    }
)
_EVIDENCE_REQUIRED_ABSTENTIONS = frozenset(
    {
        ScientificStatus.INSUFFICIENT_EVIDENCE,
        ScientificStatus.UNSUPPORTED_MODALITY,
        ScientificStatus.AMBIGUOUS,
    }
)


def _fail(message: str) -> TechnicalFailure:
    """Return a TechnicalFailure from the validation stage."""
    return TechnicalFailure(
        stage="validation",
        code="VALIDATION_FAILED",
        message=message,
        cause="contract_violation",
    )


class OutputValidator:
    """Validates a :class:`~promoter_ai_extraction.models.PropertyResult`.

    Usage::

        validator = OutputValidator()
        outcome = validator.validate(result, request, document)
        if isinstance(outcome, TechnicalFailure):
            # handle validation failure ...
    """

    def validate(
        self,
        result: PropertyResult,
        request: ExtractionRequest,
        document: LoadedDocument,
    ) -> PropertyResult | TechnicalFailure:
        """Validate *result* against *request* and *document*.

        Parameters
        ----------
        result:
            The :class:`~promoter_ai_extraction.models.PropertyResult` to
            check.
        request:
            The originating :class:`~promoter_ai_extraction.boundary.ExtractionRequest`
            that produced the result.  Identity fields are matched against it.
        document:
            The :class:`~promoter_ai_extraction.documents.LoadedDocument`
            whose segment identifiers are used to verify evidence grounding.

        Returns
        -------
        PropertyResult
            The original *result* object, unchanged, when all checks pass.
        TechnicalFailure
            When any validation rule is violated.  Code is always
            ``"VALIDATION_FAILED"``; stage is always ``"validation"``.
        """
        # ── 1. Identity ────────────────────────────────────────────────────
        if result.paper_id != request.paper_id:
            return _fail(
                "result.paper_id does not match the extraction request paper_id."
            )
        if result.promoter_name != request.promoter_name:
            return _fail(
                "result.promoter_name does not match the extraction request promoter_name."
            )
        if result.property != request.property:
            return _fail(
                "result.property does not match the extraction request property."
            )

        # ── 2. Status / value consistency ──────────────────────────────────
        if result.status == ScientificStatus.EXTRACTED:
            if not result.values:
                return _fail(
                    "EXTRACTED result must contain at least one accepted value, "
                    "but values is empty."
                )
            if result.abstention_reason is not None:
                return _fail(
                    "EXTRACTED result must not contain an abstention reason."
                )
        elif result.status in _ABSTENTION_STATUSES:
            if result.values:
                return _fail(
                    f"{result.status} result must have zero accepted values, "
                    f"but {len(result.values)} value(s) were found."
                )
            if (
                result.abstention_reason is None
                or not result.abstention_reason.strip()
            ):
                return _fail(
                    f"{result.status} result must contain a non-empty "
                    "abstention reason."
                )
            has_candidate_evidence = any(
                candidate.evidence is not None
                for candidate in result.candidate_values
            )
            if (
                result.status in _EVIDENCE_REQUIRED_ABSTENTIONS
                and not result.evidence
                and not has_candidate_evidence
            ):
                return _fail(
                    f"{result.status} result must contain documentary evidence "
                    "or an evidenced candidate."
                )

        # ── 3 + 4. Evidence existence and document grounding ────────────────
        segments_by_id = {segment.segment_id: segment for segment in document.segments}

        if result.status == ScientificStatus.EXTRACTED:
            for i, val in enumerate(result.values):
                if not val.value_raw or not val.value_raw.strip():
                    return _fail(
                        f"Accepted value at index {i} has an empty value_raw."
                    )
                if not val.value_normalized or not val.value_normalized.strip():
                    return _fail(
                        f"Accepted value at index {i} has an empty value_normalized."
                    )
                if not val.evidence:
                    return _fail(
                        f"Accepted value at index {i} has an empty evidence tuple. "
                        "Every accepted value must reference at least one "
                        "document segment."
                    )
                for ev in val.evidence:
                    failure = _validate_evidence(
                        ev, segments_by_id, context=f"accepted value {i}"
                    )
                    if failure is not None:
                        return failure

        for i, ev in enumerate(result.evidence):
            failure = _validate_evidence(
                ev, segments_by_id, context=f"result evidence {i}"
            )
            if failure is not None:
                return failure

        accepted_by_raw_and_segment = {
            (value.value_raw, evidence.segment_id)
            for value in result.values
            for evidence in value.evidence
        }
        for i, candidate in enumerate(result.candidate_values):
            if candidate.evidence is not None:
                failure = _validate_evidence(
                    candidate.evidence,
                    segments_by_id,
                    context=f"candidate evidence {i}",
                )
                if failure is not None:
                    return failure
                if (
                    candidate.candidate_raw,
                    candidate.evidence.segment_id,
                ) in accepted_by_raw_and_segment:
                    return _fail(
                        "A candidate marked INVALID_CANDIDATE cannot also be "
                        "accepted from the same documentary segment."
                    )

        return result


def _validate_evidence(
    evidence: EvidenceItem,
    segments_by_id: dict[str, DocumentSegment],
    *,
    context: str,
) -> TechnicalFailure | None:
    """Validate one evidence item against its referenced document segment."""
    segment = segments_by_id.get(evidence.segment_id)
    if segment is None:
        return _fail(
            f"{context} references a segment_id absent from the supplied document."
        )
    if not evidence.fragment or not evidence.fragment.strip():
        return _fail(f"{context} contains an empty evidence fragment.")
    if evidence.fragment not in segment.text:
        return _fail(
            f"{context} contains a fragment absent from its referenced segment."
        )
    if evidence.source_type != segment.source_type:
        return _fail(
            f"{context} source_type does not match its referenced segment."
        )
    if evidence.location != segment.location:
        return _fail(
            f"{context} location does not match its referenced segment."
        )
    return None
