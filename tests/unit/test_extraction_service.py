"""Tests for GuidedExtractionService orchestration (T017 / T018).

Initially all tests import from promoter_ai_extraction.extraction which
already exists (built in T016).  T017 is the RED phase for the service-level
behaviour (four-property independence, grouping, failures, multiple values).
T018 is the GREEN phase — GuidedExtractionService must already exist in
extraction.py after T016, so these tests are actually testing T018 behaviour.

Coverage (per task description):
- Independent extraction per property: four properties extracted independently.
- Grouped four results: ExtractionRun contains all four property attempts.
- Per-property failure remains separate: one backend failure leaves the other
  three attempts untouched.
- Multiple values per property flow through to ExtractionRun.
- Abstention (NOT_FOUND) for one property does not affect others.
- ExtractionRun identifies paper and promoter.
- ExtractionRun.run_id is populated (not empty).
- Backend receives four separate SafeExtractionInput objects (one per property).
"""
from __future__ import annotations

import pytest

from promoter_ai_extraction.boundary import ExtractionRequestFactory
from promoter_ai_extraction.documents import DocumentSegment, LoadedDocument
from promoter_ai_extraction.extraction import (
    BackendFailure,
    GuidedExtractionService,
    PropertyExtractor,
    RawPropertyPayload,
    RawValuePayload,
)
from promoter_ai_extraction.models import (
    ExtractionRun,
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
    "The promoter lacZp1 was characterized with TSS at -42, "
    "Caja -10 TATAAT, Caja -35 TTGACA, and sigma70."
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


def _extracted(value_raw: str, seg_id: str = _SEG_ID) -> RawPropertyPayload:
    return RawPropertyPayload(
        status="EXTRACTED",
        values=(
            RawValuePayload(
                value_raw=value_raw,
                qualifier=None,
                evidence_segment_ids=(seg_id,),
                evidence_fragments=(_SEG_TEXT,),
            ),
        ),
        candidates=(),
        abstention_reason=None,
        result_evidence=(),
    )


def _not_found() -> RawPropertyPayload:
    return RawPropertyPayload(
        status="NOT_FOUND",
        values=(),
        candidates=(),
        abstention_reason="No evidence found in the supplied document.",
        result_evidence=(),
    )


def _make_service(
    responses: dict[Property, RawPropertyPayload | BackendFailure],
) -> GuidedExtractionService:
    backend = ScriptedBackend(responses)
    extractor = PropertyExtractor(backend=backend, validator=OutputValidator())
    factory = ExtractionRequestFactory()
    return GuidedExtractionService(extractor=extractor, request_factory=factory)


# ─── Tests: grouping and identity ────────────────────────────────────────────


class TestExtractionRunGrouping:
    """GuidedExtractionService returns an ExtractionRun with correct identity."""

    def test_run_returns_extraction_run(self) -> None:
        """service.run() returns an ExtractionRun object."""
        service = _make_service(
            {
                Property.TSS: _extracted("-42"),
                Property.CAJA_10: _extracted("TATAAT"),
                Property.CAJA_35: _not_found(),
                Property.FACTOR_SIGMA: _extracted("sigma70"),
            }
        )
        doc = _make_document()
        run = service.run(doc, promoter_name="lacZp1")
        assert isinstance(run, ExtractionRun)

    def test_run_paper_id_matches_document(self) -> None:
        """ExtractionRun.paper_id equals document.paper_id."""
        service = _make_service(
            {
                Property.TSS: _extracted("-42"),
                Property.CAJA_10: _not_found(),
                Property.CAJA_35: _not_found(),
                Property.FACTOR_SIGMA: _not_found(),
            }
        )
        doc = _make_document(paper_id="PMC99999")
        run = service.run(doc, promoter_name="lacZp1")
        assert run.paper_id == "PMC99999"

    def test_run_promoter_name_preserved(self) -> None:
        """ExtractionRun.promoter_name equals the supplied promoter name."""
        service = _make_service(
            {
                Property.TSS: _not_found(),
                Property.CAJA_10: _not_found(),
                Property.CAJA_35: _not_found(),
                Property.FACTOR_SIGMA: _not_found(),
            }
        )
        doc = _make_document()
        run = service.run(doc, promoter_name="gadWp2")
        assert run.promoter_name == "gadWp2"

    def test_run_id_is_populated(self) -> None:
        """ExtractionRun.run_id is a non-empty string."""
        service = _make_service(
            {
                Property.TSS: _not_found(),
                Property.CAJA_10: _not_found(),
                Property.CAJA_35: _not_found(),
                Property.FACTOR_SIGMA: _not_found(),
            }
        )
        doc = _make_document()
        run = service.run(doc, promoter_name="lacZp1")
        assert isinstance(run.run_id, str)
        assert run.run_id.strip() != ""

    def test_custom_run_id_respected(self) -> None:
        """Caller-supplied run_id is used when provided."""
        service = _make_service(
            {
                Property.TSS: _not_found(),
                Property.CAJA_10: _not_found(),
                Property.CAJA_35: _not_found(),
                Property.FACTOR_SIGMA: _not_found(),
            }
        )
        doc = _make_document()
        run = service.run(doc, promoter_name="lacZp1", run_id="custom-run-001")
        assert run.run_id == "custom-run-001"


# ─── Tests: four-property independence ────────────────────────────────────────


class TestPropertyIndependence:
    """Each property is extracted independently — status/values do not cross."""

    def test_tss_extracted_caja35_not_found_are_independent(self) -> None:
        """TSS EXTRACTED and Caja -35 NOT_FOUND coexist in the same run (AC-04)."""
        service = _make_service(
            {
                Property.TSS: _extracted("-42"),
                Property.CAJA_10: _not_found(),
                Property.CAJA_35: _not_found(),
                Property.FACTOR_SIGMA: _not_found(),
            }
        )
        doc = _make_document()
        run = service.run(doc, promoter_name="lacZp1")
        assert isinstance(run.tss, PropertyResult)
        assert run.tss.status == ScientificStatus.EXTRACTED
        assert isinstance(run.caja_35, PropertyResult)
        assert run.caja_35.status == ScientificStatus.NOT_FOUND

    def test_all_four_properties_attempted(self) -> None:
        """All four property slots in ExtractionRun are always populated."""
        service = _make_service(
            {
                Property.TSS: _extracted("-42"),
                Property.CAJA_10: _extracted("TATAAT"),
                Property.CAJA_35: _extracted("TTGACA"),
                Property.FACTOR_SIGMA: _extracted("sigma70"),
            }
        )
        doc = _make_document()
        run = service.run(doc, promoter_name="lacZp1")
        # All four slots are PropertyResult
        assert isinstance(run.tss, PropertyResult)
        assert isinstance(run.caja_10, PropertyResult)
        assert isinstance(run.caja_35, PropertyResult)
        assert isinstance(run.sigma, PropertyResult)

    def test_tss_property_in_tss_slot(self) -> None:
        """ExtractionRun.tss.property is Property.TSS."""
        service = _make_service(
            {
                Property.TSS: _extracted("-42"),
                Property.CAJA_10: _not_found(),
                Property.CAJA_35: _not_found(),
                Property.FACTOR_SIGMA: _not_found(),
            }
        )
        doc = _make_document()
        run = service.run(doc, promoter_name="lacZp1")
        assert run.tss.property == Property.TSS  # type: ignore[union-attr]

    def test_sigma_property_in_sigma_slot(self) -> None:
        """ExtractionRun.sigma.property is Property.FACTOR_SIGMA."""
        service = _make_service(
            {
                Property.TSS: _not_found(),
                Property.CAJA_10: _not_found(),
                Property.CAJA_35: _not_found(),
                Property.FACTOR_SIGMA: _extracted("sigma70"),
            }
        )
        doc = _make_document()
        run = service.run(doc, promoter_name="lacZp1")
        assert run.sigma.property == Property.FACTOR_SIGMA  # type: ignore[union-attr]


# ─── Tests: per-property failure isolation ────────────────────────────────────


class TestPerPropertyFailureIsolation:
    """A backend failure for one property does not affect the other three."""

    def test_tss_backend_failure_leaves_others_intact(self) -> None:
        """TSS BackendFailure → TechnicalFailure in tss slot; others succeed."""
        service = _make_service(
            {
                Property.TSS: BackendFailure(code="TIMEOUT", message="timed out"),
                Property.CAJA_10: _extracted("TATAAT"),
                Property.CAJA_35: _not_found(),
                Property.FACTOR_SIGMA: _extracted("sigma70"),
            }
        )
        doc = _make_document()
        run = service.run(doc, promoter_name="lacZp1")
        assert isinstance(run.tss, TechnicalFailure)
        assert isinstance(run.caja_10, PropertyResult)
        assert run.caja_10.status == ScientificStatus.EXTRACTED
        assert isinstance(run.caja_35, PropertyResult)
        assert run.caja_35.status == ScientificStatus.NOT_FOUND
        assert isinstance(run.sigma, PropertyResult)
        assert run.sigma.status == ScientificStatus.EXTRACTED

    def test_failure_not_counted_as_abstention(self) -> None:
        """A TechnicalFailure in a slot is NOT a scientific abstention."""
        service = _make_service(
            {
                Property.TSS: BackendFailure(code="ERROR", message="error"),
                Property.CAJA_10: _not_found(),
                Property.CAJA_35: _not_found(),
                Property.FACTOR_SIGMA: _not_found(),
            }
        )
        doc = _make_document()
        run = service.run(doc, promoter_name="lacZp1")
        assert isinstance(run.tss, TechnicalFailure)
        # TechnicalFailure.code must not be a ScientificStatus value
        scientific_codes = {s.value for s in ScientificStatus}
        assert run.tss.code not in scientific_codes

    def test_all_four_fail_independently(self) -> None:
        """All four backend failures → four TechnicalFailures in the run."""
        service = _make_service(
            {
                Property.TSS: BackendFailure(code="ERR", message="err"),
                Property.CAJA_10: BackendFailure(code="ERR", message="err"),
                Property.CAJA_35: BackendFailure(code="ERR", message="err"),
                Property.FACTOR_SIGMA: BackendFailure(code="ERR", message="err"),
            }
        )
        doc = _make_document()
        run = service.run(doc, promoter_name="lacZp1")
        assert isinstance(run.tss, TechnicalFailure)
        assert isinstance(run.caja_10, TechnicalFailure)
        assert isinstance(run.caja_35, TechnicalFailure)
        assert isinstance(run.sigma, TechnicalFailure)


# ─── Tests: multiple values per property ──────────────────────────────────────


class TestMultipleValuesPerProperty:
    """Multiple values for a property flow through to ExtractionRun."""

    def test_two_tss_values_in_extraction_run(self) -> None:
        """Two TSS values from the backend appear as two ExtractedValues."""
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
        multi_payload = RawPropertyPayload(
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
        service = _make_service(
            {
                Property.TSS: multi_payload,
                Property.CAJA_10: _not_found(),
                Property.CAJA_35: _not_found(),
                Property.FACTOR_SIGMA: _not_found(),
            }
        )
        run = service.run(doc, promoter_name="lacZp1")
        assert isinstance(run.tss, PropertyResult)
        assert len(run.tss.values) == 2

    def test_multiple_values_remain_distinct(self) -> None:
        """Each value in a multi-value result is a distinct ExtractedValue."""
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
        multi_payload = RawPropertyPayload(
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
        service = _make_service(
            {
                Property.TSS: multi_payload,
                Property.CAJA_10: _not_found(),
                Property.CAJA_35: _not_found(),
                Property.FACTOR_SIGMA: _not_found(),
            }
        )
        run = service.run(doc, promoter_name="lacZp1")
        assert isinstance(run.tss, PropertyResult)
        values = run.tss.values
        assert values[0].value_raw == "-42"
        assert values[1].value_raw == "-38"


# ─── Tests: backend call count per property ────────────────────────────────────


class TestBackendCallCount:
    """Service calls the backend exactly once per property (four total)."""

    def test_backend_called_four_times(self) -> None:
        """CaptureBackend receives exactly 4 calls (one per property)."""
        any_payload = _not_found()
        capture = CaptureBackend(response=any_payload)
        extractor = PropertyExtractor(backend=capture, validator=OutputValidator())
        factory = ExtractionRequestFactory()
        service = GuidedExtractionService(extractor=extractor, request_factory=factory)
        doc = _make_document()
        service.run(doc, promoter_name="lacZp1")
        assert len(capture.received) == 4

    def test_backend_receives_four_different_properties(self) -> None:
        """The four backend calls carry four distinct property values."""
        any_payload = _not_found()
        capture = CaptureBackend(response=any_payload)
        extractor = PropertyExtractor(backend=capture, validator=OutputValidator())
        factory = ExtractionRequestFactory()
        service = GuidedExtractionService(extractor=extractor, request_factory=factory)
        doc = _make_document()
        service.run(doc, promoter_name="lacZp1")
        received_props = {inp.property for inp in capture.received}
        assert received_props == {
            Property.TSS,
            Property.CAJA_10,
            Property.CAJA_35,
            Property.FACTOR_SIGMA,
        }
