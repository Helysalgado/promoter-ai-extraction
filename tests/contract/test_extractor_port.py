"""Contract tests for PropertyExtractor, ModelBackend, and ScriptedBackend (T015).

RED: collection fails because promoter_ai_extraction.extraction does not
exist yet.  After T016 implementation all tests pass (GREEN).

Coverage:
- AC-04/AC-05/AC-14–AC-16 (property independence, value grounding, failure
  separation, no external completion).
- Deterministic ScriptedBackend: same SafeExtractionInput → same response.
- Backend receives only SafeExtractionInput (safe projection); never receives
  the full ExtractionRequest or LoadedDocument directly.
- SafeExtractionInput fields verified: only the expected safe fields.
- Backend failure (BackendFailure) → TechnicalFailure from PropertyExtractor.
- EXTRACTED response flows through normalization to PropertyResult.
- Qualifiers from backend payload are preserved in PropertyResult.
- INVALID_CANDIDATE candidate from backend is preserved in candidate_values.
- CaptureBackend verifies the exact type the backend is invoked with.
"""
from __future__ import annotations

import pytest

from promoter_ai_extraction.boundary import ExtractionRequest, ExtractionRequestFactory
from promoter_ai_extraction.documents import DocumentSegment, DocumentLoader, DocumentSource, LoadedDocument
from promoter_ai_extraction.extraction import (
    BackendFailure,
    PropertyExtractor,
    RawCandidatePayload,
    RawPropertyPayload,
    RawValuePayload,
    SafeDocumentSegment,
    SafeExtractionInput,
)
from promoter_ai_extraction.models import (
    CandidateRejectionReason,
    Property,
    PropertyResult,
    ScientificStatus,
    TechnicalFailure,
)
from promoter_ai_extraction.validation import OutputValidator
from fakes import CaptureBackend, ScriptedBackend


# ─── Fixtures ─────────────────────────────────────────────────────────────────

_SEG_ID = "txt:p:0001"
_SEG_TEXT = (
    "The TSS was mapped to -42 upstream of the ATG. "
    "The -10 box tataat was identified. "
    "A putative -10 box TATAAT was found. "
    "Transcription is initiated by Sigma70. "
    "TSS at -42 but promoter association ambiguous."
)


def _make_document(paper_id: str = "PMC12345") -> LoadedDocument:
    return LoadedDocument(
        paper_id=paper_id,
        format="TXT",
        segments=(
            DocumentSegment(
                segment_id=_SEG_ID,
                text=_SEG_TEXT,
                source_type="body_text",
                location="line 1",
            ),
        ),
        document_hash="deadbeef" * 8,
    )


def _make_request(
    document: LoadedDocument | None = None,
    prop: Property = Property.TSS,
    paper_id: str = "PMC12345",
    promoter_name: str = "lacZp1",
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


def _extracted_payload(
    seg_id: str = _SEG_ID,
    value_raw: str = "-42",
    qualifier: str | None = None,
) -> RawPropertyPayload:
    return RawPropertyPayload(
        status="EXTRACTED",
        values=(
            RawValuePayload(
                value_raw=value_raw,
                qualifier=qualifier,
                evidence_segment_ids=(seg_id,),
                evidence_fragments=(
                    "The TSS was mapped to -42 upstream of the ATG.",
                ),
            ),
        ),
        candidates=(),
        abstention_reason=None,
        result_evidence=(),
    )


def _not_found_payload() -> RawPropertyPayload:
    return RawPropertyPayload(
        status="NOT_FOUND",
        values=(),
        candidates=(),
        abstention_reason="No evidence found.",
        result_evidence=(),
    )


def _make_extractor(
    backend: object,
) -> PropertyExtractor:
    return PropertyExtractor(backend=backend, validator=OutputValidator())


# ─── ScriptedBackend determinism ──────────────────────────────────────────────


class TestScriptedBackendDeterminism:
    """ScriptedBackend returns identical responses for identical inputs."""

    def test_same_property_same_response(self) -> None:
        """Same property key → identical RawPropertyPayload object returned."""
        payload = _extracted_payload()
        backend = ScriptedBackend({Property.TSS: payload})
        doc = _make_document()
        safe1 = SafeExtractionInput(
            paper_id="PMC12345",
            promoter_name="lacZp1",
            promoter_id=None,
            paper_gene_synonym=None,
            property=Property.TSS,
            document_segments=tuple(
                SafeDocumentSegment(
                    segment_id=s.segment_id,
                    text=s.text,
                    source_type=s.source_type,
                    location=s.location,
                )
                for s in doc.segments
            ),
        )
        safe2 = SafeExtractionInput(
            paper_id="PMC12345",
            promoter_name="lacZp1",
            promoter_id=None,
            paper_gene_synonym=None,
            property=Property.TSS,
            document_segments=safe1.document_segments,
        )
        response1 = backend.generate(safe1)
        response2 = backend.generate(safe2)
        assert response1 is response2  # same object → deterministic

    def test_different_properties_different_responses(self) -> None:
        """Different property keys return the configured response for each."""
        tss_payload = _extracted_payload(value_raw="-42")
        nf_payload = _not_found_payload()
        backend = ScriptedBackend(
            {Property.TSS: tss_payload, Property.CAJA_10: nf_payload}
        )
        doc = _make_document()
        base_segments = tuple(
            SafeDocumentSegment(
                segment_id=s.segment_id,
                text=s.text,
                source_type=s.source_type,
                location=s.location,
            )
            for s in doc.segments
        )
        safe_tss = SafeExtractionInput(
            paper_id="PMC12345",
            promoter_name="lacZp1",
            promoter_id=None,
            paper_gene_synonym=None,
            property=Property.TSS,
            document_segments=base_segments,
        )
        safe_c10 = SafeExtractionInput(
            paper_id="PMC12345",
            promoter_name="lacZp1",
            promoter_id=None,
            paper_gene_synonym=None,
            property=Property.CAJA_10,
            document_segments=base_segments,
        )
        assert backend.generate(safe_tss) is tss_payload
        assert backend.generate(safe_c10) is nf_payload


# ─── SafeExtractionInput projection ───────────────────────────────────────────


class TestSafeExtractionInputProjection:
    """PropertyExtractor projects ExtractionRequest to SafeExtractionInput only."""

    def test_backend_receives_safe_extraction_input_type(self) -> None:
        """Backend is called with SafeExtractionInput, not ExtractionRequest."""
        payload = _extracted_payload()
        capture = CaptureBackend(response=payload)
        extractor = _make_extractor(capture)
        request = _make_request()
        extractor.extract(request)
        assert len(capture.received) == 1
        assert isinstance(capture.received[0], SafeExtractionInput)

    def test_backend_does_not_receive_loaded_document(self) -> None:
        """Backend receives SafeExtractionInput which does not embed a LoadedDocument."""
        payload = _extracted_payload()
        capture = CaptureBackend(response=payload)
        extractor = _make_extractor(capture)
        request = _make_request()
        extractor.extract(request)
        received = capture.received[0]
        from promoter_ai_extraction.documents import LoadedDocument
        # SafeExtractionInput must not carry the full LoadedDocument
        assert not isinstance(received, LoadedDocument)
        for attr_name in vars(received.__class__):
            val = getattr(received, attr_name, None)
            assert not isinstance(val, LoadedDocument), (
                f"SafeExtractionInput field '{attr_name}' contains a LoadedDocument"
            )

    def test_safe_input_has_no_document_hash(self) -> None:
        """SafeExtractionInput has no document_hash field."""
        payload = _extracted_payload()
        capture = CaptureBackend(response=payload)
        extractor = _make_extractor(capture)
        request = _make_request()
        extractor.extract(request)
        received = capture.received[0]
        assert not hasattr(received, "document_hash")

    def test_safe_input_document_segments_are_safe_type(self) -> None:
        """Document segments in SafeExtractionInput are SafeDocumentSegment objects."""
        payload = _extracted_payload()
        capture = CaptureBackend(response=payload)
        extractor = _make_extractor(capture)
        request = _make_request()
        extractor.extract(request)
        received = capture.received[0]
        for seg in received.document_segments:
            assert isinstance(seg, SafeDocumentSegment)

    def test_safe_input_paper_id_matches_request(self) -> None:
        """SafeExtractionInput.paper_id equals the request paper_id."""
        payload = _extracted_payload()
        capture = CaptureBackend(response=payload)
        extractor = _make_extractor(capture)
        request = _make_request(paper_id="PMC99999")
        extractor.extract(request)
        received = capture.received[0]
        assert received.paper_id == "PMC99999"

    def test_safe_input_property_matches_request(self) -> None:
        """SafeExtractionInput.property equals the request property."""
        payload = _extracted_payload()
        capture = CaptureBackend(response=payload)
        extractor = _make_extractor(capture)
        request = _make_request(prop=Property.CAJA_10)
        extractor.extract(request)
        received = capture.received[0]
        assert received.property == Property.CAJA_10


# ─── Backend failure → TechnicalFailure ───────────────────────────────────────


class TestBackendFailureHandling:
    """BackendFailure from the backend becomes a TechnicalFailure."""

    def test_backend_failure_yields_technical_failure(self) -> None:
        """A BackendFailure from the backend → TechnicalFailure from PropertyExtractor."""
        failure = BackendFailure(code="TIMEOUT", message="Backend timed out.")
        backend = ScriptedBackend({Property.TSS: failure})
        extractor = _make_extractor(backend)
        request = _make_request(prop=Property.TSS)
        outcome = extractor.extract(request)
        assert isinstance(outcome, TechnicalFailure)

    def test_technical_failure_code_not_scientific_status(self) -> None:
        """TechnicalFailure produced from BackendFailure has a non-scientific code."""
        failure = BackendFailure(code="BACKEND_ERROR", message="Unexpected error.")
        backend = ScriptedBackend({Property.TSS: failure})
        extractor = _make_extractor(backend)
        request = _make_request(prop=Property.TSS)
        outcome = extractor.extract(request)
        assert isinstance(outcome, TechnicalFailure)
        scientific_codes = {s.value for s in ScientificStatus}
        assert outcome.code not in scientific_codes

    def test_technical_failure_stage_is_extraction(self) -> None:
        """TechnicalFailure from a backend call carries stage='extraction'."""
        failure = BackendFailure(code="BACKEND_ERROR", message="Error.")
        backend = ScriptedBackend({Property.TSS: failure})
        extractor = _make_extractor(backend)
        request = _make_request(prop=Property.TSS)
        outcome = extractor.extract(request)
        assert isinstance(outcome, TechnicalFailure)
        assert outcome.stage == "extraction"

    def test_backend_exception_yields_technical_failure(self) -> None:
        """An adapter exception remains a technical failure for this property."""

        class RaisingBackend:
            def generate(self, safe_input: SafeExtractionInput) -> RawPropertyPayload:
                raise RuntimeError("synthetic adapter failure")

        outcome = _make_extractor(RaisingBackend()).extract(_make_request())
        assert isinstance(outcome, TechnicalFailure)
        assert outcome.code == "BACKEND_ERROR"
        assert outcome.cause == "RuntimeError"


# ─── EXTRACTED response flow through normalization ────────────────────────────


class TestExtractedResponseNormalization:
    """EXTRACTED payload flows through property normalizer into PropertyResult."""

    def test_box_value_normalized_uppercase(self) -> None:
        """Caja -10 lowercase value is normalized to uppercase in PropertyResult."""
        payload = RawPropertyPayload(
            status="EXTRACTED",
            values=(
                RawValuePayload(
                    value_raw="tataat",
                    qualifier=None,
                    evidence_segment_ids=(_SEG_ID,),
                    evidence_fragments=("The -10 box tataat was identified.",),
                ),
            ),
            candidates=(),
            abstention_reason=None,
            result_evidence=(),
        )
        backend = ScriptedBackend({Property.CAJA_10: payload})
        extractor = _make_extractor(backend)
        request = _make_request(prop=Property.CAJA_10)
        outcome = extractor.extract(request)
        assert isinstance(outcome, PropertyResult)
        assert outcome.values[0].value_normalized == "TATAAT"
        assert outcome.values[0].value_raw == "tataat"  # raw preserved

    def test_sigma_value_normalized_lowercase(self) -> None:
        """Factor sigma 'Sigma70' is normalized to 'sigma70' in PropertyResult."""
        payload = RawPropertyPayload(
            status="EXTRACTED",
            values=(
                RawValuePayload(
                    value_raw="Sigma70",
                    qualifier=None,
                    evidence_segment_ids=(_SEG_ID,),
                    evidence_fragments=("Transcription is initiated by Sigma70.",),
                ),
            ),
            candidates=(),
            abstention_reason=None,
            result_evidence=(),
        )
        backend = ScriptedBackend({Property.FACTOR_SIGMA: payload})
        extractor = _make_extractor(backend)
        request = _make_request(prop=Property.FACTOR_SIGMA)
        outcome = extractor.extract(request)
        assert isinstance(outcome, PropertyResult)
        assert outcome.values[0].value_normalized == "sigma70"
        assert outcome.values[0].value_raw == "Sigma70"

    def test_qualifier_preserved_from_backend(self) -> None:
        """Qualifier from RawValuePayload is preserved in the PropertyResult value."""
        payload = RawPropertyPayload(
            status="EXTRACTED",
            values=(
                RawValuePayload(
                    value_raw="TATAAT",
                    qualifier="putative",
                    evidence_segment_ids=(_SEG_ID,),
                    evidence_fragments=("A putative -10 box TATAAT was found.",),
                ),
            ),
            candidates=(),
            abstention_reason=None,
            result_evidence=(),
        )
        backend = ScriptedBackend({Property.CAJA_10: payload})
        extractor = _make_extractor(backend)
        request = _make_request(prop=Property.CAJA_10)
        outcome = extractor.extract(request)
        assert isinstance(outcome, PropertyResult)
        assert outcome.values[0].qualifier == "putative"

    def test_tss_extracted_result_has_correct_identity(self) -> None:
        """PropertyResult identity fields match the request."""
        payload = _extracted_payload()
        backend = ScriptedBackend({Property.TSS: payload})
        extractor = _make_extractor(backend)
        request = _make_request(
            prop=Property.TSS, paper_id="PMC12345", promoter_name="lacZp1"
        )
        outcome = extractor.extract(request)
        assert isinstance(outcome, PropertyResult)
        assert outcome.paper_id == "PMC12345"
        assert outcome.promoter_name == "lacZp1"
        assert outcome.property == Property.TSS

    def test_tss_anchor_can_come_from_grounded_evidence(self) -> None:
        """Distributed evidence can supply the explicit translation-start anchor."""
        document = LoadedDocument(
            paper_id="PMC12345",
            format="TXT",
            segments=(
                DocumentSegment(
                    segment_id=_SEG_ID,
                    text="The TSS lies 42 bp upstream of the translation start.",
                    source_type="body_text",
                    location="line 1",
                ),
            ),
            document_hash="deadbeef" * 8,
        )
        payload = RawPropertyPayload(
            status="EXTRACTED",
            values=(
                RawValuePayload(
                    value_raw="42 bp upstream",
                    qualifier=None,
                    evidence_segment_ids=(_SEG_ID,),
                    evidence_fragments=(
                        "The TSS lies 42 bp upstream of the translation start.",
                    ),
                ),
            ),
            candidates=(),
            abstention_reason=None,
            result_evidence=(),
        )
        outcome = _make_extractor(
            ScriptedBackend({Property.TSS: payload})
        ).extract(_make_request(document=document))
        assert isinstance(outcome, PropertyResult)
        assert outcome.values[0].value_raw == "42 bp upstream"
        assert outcome.values[0].value_normalized == "-42"

    def test_multiple_values_from_backend(self) -> None:
        """Two values in backend payload → two ExtractedValues in PropertyResult."""
        doc = LoadedDocument(
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
        payload = RawPropertyPayload(
            status="EXTRACTED",
            values=(
                RawValuePayload(
                    value_raw="-42",
                    qualifier=None,
                    evidence_segment_ids=("txt:p:0001",),
                    evidence_fragments=("TSS-A at -42.",),
                ),
                RawValuePayload(
                    value_raw="-38",
                    qualifier=None,
                    evidence_segment_ids=("txt:p:0002",),
                    evidence_fragments=("TSS-B at -38.",),
                ),
            ),
            candidates=(),
            abstention_reason=None,
            result_evidence=(),
        )
        backend = ScriptedBackend({Property.TSS: payload})
        extractor = _make_extractor(backend)
        request = ExtractionRequest(
            document=doc,
            paper_id="PMC12345",
            promoter_id=None,
            promoter_name="lacZp1",
            paper_gene_synonym=None,
            property=Property.TSS,
        )
        outcome = extractor.extract(request)
        assert isinstance(outcome, PropertyResult)
        assert len(outcome.values) == 2

    @pytest.mark.parametrize(
        "segment_ids,fragments",
        [
            ((_SEG_ID, "txt:p:0002"), ("one fragment",)),
            ((_SEG_ID,), ("first", "second")),
        ],
    )
    def test_mismatched_evidence_cardinality_is_technical_failure(
        self,
        segment_ids: tuple[str, ...],
        fragments: tuple[str, ...],
    ) -> None:
        """Malformed backend evidence arrays must not be silently truncated."""
        payload = RawPropertyPayload(
            status="EXTRACTED",
            values=(
                RawValuePayload(
                    value_raw="-42",
                    qualifier=None,
                    evidence_segment_ids=segment_ids,
                    evidence_fragments=fragments,
                ),
            ),
            candidates=(),
            abstention_reason=None,
            result_evidence=(),
        )
        outcome = _make_extractor(
            ScriptedBackend({Property.TSS: payload})
        ).extract(_make_request())
        assert isinstance(outcome, TechnicalFailure)
        assert outcome.code == "INVALID_BACKEND_PAYLOAD"


# ─── INVALID_CANDIDATE flow ───────────────────────────────────────────────────


class TestInvalidCandidateFlow:
    """INVALID_CANDIDATE from backend ends up in candidate_values (AC-30)."""

    def test_backend_candidate_in_candidate_values_not_in_values(self) -> None:
        """A RawCandidatePayload from the backend maps to RejectedCandidate."""
        payload = RawPropertyPayload(
            status="NOT_FOUND",
            values=(),
            candidates=(
                RawCandidatePayload(
                    candidate_raw="-42",
                    rule_violated="ambiguous promoter association",
                    evidence_segment_id=_SEG_ID,
                    evidence_fragment="TSS at -42 but promoter association ambiguous.",
                ),
            ),
            abstention_reason="Candidate rejected; promoter association ambiguous.",
            result_evidence=(),
        )
        backend = ScriptedBackend({Property.TSS: payload})
        extractor = _make_extractor(backend)
        request = _make_request(prop=Property.TSS)
        outcome = extractor.extract(request)
        assert isinstance(outcome, PropertyResult)
        assert len(outcome.values) == 0
        assert len(outcome.candidate_values) == 1
        candidate = outcome.candidate_values[0]
        assert candidate.rejection_reason == CandidateRejectionReason.INVALID_CANDIDATE
        assert candidate.candidate_raw == "-42"
