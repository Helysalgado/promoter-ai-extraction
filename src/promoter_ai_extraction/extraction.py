"""Extractor port, safe payload contracts, and orchestration (T016 / T018).

Public surface
--------------
SafeDocumentSegment   – safe view of one document segment for the backend
SafeExtractionInput   – only the fields the backend is permitted to see
RawValuePayload       – one raw accepted-value description from the backend
RawCandidatePayload   – one raw rejected-candidate description from the backend
RawPropertyPayload    – structured backend output for one property attempt
BackendFailure        – non-scientific failure from the backend call
ModelBackend          – Protocol that any backend adapter must implement
PropertyExtractor     – converts ExtractionRequest → PropertyResult | TechnicalFailure
GuidedExtractionService – sequential four-property orchestrator → ExtractionRun

Design decisions (plan §2 / §3 / §4, T016 / T018)
---------------------------------------------------
* The backend receives only ``SafeExtractionInput`` — never the full
  ``ExtractionRequest``, never the ``LoadedDocument``.  This enforces the
  leakage boundary at the type level.
* ``SafeExtractionInput`` contains no ``document_hash``, no gold path, and no
  evaluator-only fields.
* ``PropertyExtractor`` applies property-specific normalization between the
  backend call and the ``OutputValidator``.
* ``GuidedExtractionService`` calls the extractor exactly once per property
  in a fixed sequence; results are independent (one failure does not block
  the others).
* ``ExtractionRun`` is defined in ``models.py`` as a pure data carrier.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from promoter_ai_extraction.boundary import ExtractionRequest, ExtractionRequestFactory, BoundaryViolation
from promoter_ai_extraction.documents import DocumentSegment, LoadedDocument
from promoter_ai_extraction.models import (
    CandidateRejectionReason,
    EvidenceItem,
    ExtractedValue,
    ExtractionRun,
    Property,
    PropertyAttempt,
    PropertyResult,
    RejectedCandidate,
    ScientificStatus,
    TechnicalFailure,
)
from promoter_ai_extraction.normalization import normalize_for_property
from promoter_ai_extraction.validation import OutputValidator

__all__ = [
    "BackendFailure",
    "GuidedExtractionService",
    "ModelBackend",
    "PropertyExtractor",
    "RawCandidatePayload",
    "RawPropertyPayload",
    "RawValuePayload",
    "SafeDocumentSegment",
    "SafeExtractionInput",
]


# ─── Safe payload types ───────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class SafeDocumentSegment:
    """A safe view of one document segment for the model backend.

    Contains only content and structural location — no gold data, no document
    hash, no evaluator fields.
    """

    segment_id: str
    text: str
    source_type: str
    location: str | None


@dataclass(frozen=True, slots=True)
class SafeExtractionInput:
    """The only input the model backend is permitted to receive.

    Built by :class:`PropertyExtractor` from an allowlisted
    :class:`~promoter_ai_extraction.boundary.ExtractionRequest`.  Never
    carries a full ``LoadedDocument``, a document hash, a gold path, or any
    evaluator-only field.

    Fields
    ------
    paper_id:
        Paper identifier (passed for traceability, not for retrieval).
    promoter_name:
        Required promoter name.
    promoter_id:
        Optional promoter identifier.
    paper_gene_synonym:
        Optional paper-specific gene synonym.
    property:
        The one :class:`~promoter_ai_extraction.models.Property` being
        extracted in this call.
    document_segments:
        Immutable tuple of :class:`SafeDocumentSegment` objects from the
        loaded document.
    """

    paper_id: str
    promoter_name: str
    promoter_id: str | None
    paper_gene_synonym: str | None
    property: Property
    document_segments: tuple[SafeDocumentSegment, ...]


@dataclass(frozen=True, slots=True)
class RawValuePayload:
    """One raw accepted-value payload item from the model backend.

    Attributes
    ----------
    value_raw:
        The documentary form of the value as extracted from the text.
    qualifier:
        Optional qualifier string (e.g. ``"putative"``, ``"predicted"``).
    evidence_segment_ids:
        Segment identifiers (from the loaded document) that support this value.
    evidence_fragments:
        Text fragments (excerpts) corresponding to each segment id.
        Must have exactly the same cardinality as ``evidence_segment_ids``.
        A mismatch is a malformed backend payload and becomes a technical
        failure; it is never silently truncated.
    """

    value_raw: str
    qualifier: str | None
    evidence_segment_ids: tuple[str, ...]
    evidence_fragments: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RawCandidatePayload:
    """One raw rejected-candidate payload item from the model backend.

    All candidates are treated as :attr:`~CandidateRejectionReason.INVALID_CANDIDATE`
    diagnostics (spec §Candidate diagnostics, AC-30).
    """

    candidate_raw: str
    rule_violated: str
    evidence_segment_id: str | None
    evidence_fragment: str | None


@dataclass(frozen=True, slots=True)
class RawPropertyPayload:
    """Structured output from one model backend call for one property.

    The :class:`PropertyExtractor` converts this raw payload into a validated
    :class:`~promoter_ai_extraction.models.PropertyResult`.
    """

    status: str  # must be a ScientificStatus value string
    values: tuple[RawValuePayload, ...]
    candidates: tuple[RawCandidatePayload, ...]
    abstention_reason: str | None
    result_evidence: tuple[tuple[str, str], ...]  # (segment_id, fragment)


@dataclass(frozen=True, slots=True)
class BackendFailure:
    """A non-scientific failure returned by a :class:`ModelBackend`.

    Converted to a :class:`~promoter_ai_extraction.models.TechnicalFailure`
    by :class:`PropertyExtractor`.
    """

    code: str
    message: str


# ─── ModelBackend protocol ────────────────────────────────────────────────────


@runtime_checkable
class ModelBackend(Protocol):
    """Protocol any model backend adapter must implement.

    The backend must not call external services, perform retrieval, access
    gold data, or use any field outside the supplied :class:`SafeExtractionInput`.
    A malformed or unstructured response should be returned as
    :class:`BackendFailure`.
    """

    def generate(
        self, safe_input: SafeExtractionInput
    ) -> RawPropertyPayload | BackendFailure:
        """Generate a raw property payload for one extraction request.

        Parameters
        ----------
        safe_input:
            Allowlisted, immutable extraction context.

        Returns
        -------
        RawPropertyPayload
            Structured extraction result (status + values/candidates + evidence).
        BackendFailure
            When the backend cannot complete the extraction (timeout, parse
            failure, context-limit exceeded, …).
        """
        ...  # pragma: no cover


# ─── PropertyExtractor ────────────────────────────────────────────────────────


class PropertyExtractor:
    """Converts a :class:`~promoter_ai_extraction.boundary.ExtractionRequest`
    into a :class:`~promoter_ai_extraction.models.PropertyResult` or
    :class:`~promoter_ai_extraction.models.TechnicalFailure`.

    Pipeline (per call to :meth:`extract`)
    ----------------------------------------
    1. Project ``ExtractionRequest`` → ``SafeExtractionInput`` (allowed
       fields only; document hash and full object excluded).
    2. Call ``backend.generate(safe_input)``.
    3. On ``BackendFailure`` → return ``TechnicalFailure``.
    4. On ``RawPropertyPayload``:
       a. Validate status string.
       b. Look up segment objects in the document.
       c. Build ``EvidenceItem`` tuples for each value.
       d. Apply property-specific normalization to each ``value_raw``.
       e. Build ``ExtractedValue`` and ``RejectedCandidate`` objects.
       f. Build ``PropertyResult`` with correct identity.
       g. Call ``OutputValidator.validate(result, request, document)``.
       h. Return the validated result or ``TechnicalFailure``.
    """

    def __init__(self, backend: ModelBackend, validator: OutputValidator) -> None:
        self._backend = backend
        self._validator = validator

    def extract(
        self, request: ExtractionRequest
    ) -> PropertyResult | TechnicalFailure:
        """Run one extraction attempt for one property.

        Parameters
        ----------
        request:
            Allowlisted, immutable extraction request.

        Returns
        -------
        PropertyResult
            A validated scientific conclusion.
        TechnicalFailure
            When the backend fails or validation is rejected.
        """
        safe_input = self._project(request)
        try:
            raw = self._backend.generate(safe_input)
        except Exception as exc:
            return TechnicalFailure(
                stage="extraction",
                code="BACKEND_ERROR",
                message="The backend raised an exception during extraction.",
                cause=type(exc).__name__,
            )

        if isinstance(raw, BackendFailure):
            return TechnicalFailure(
                stage="extraction",
                code="BACKEND_ERROR",
                message=f"Backend reported a failure: {raw.message}",
                cause=raw.code,
            )
        if not isinstance(raw, RawPropertyPayload):
            return TechnicalFailure(
                stage="extraction",
                code="INVALID_BACKEND_PAYLOAD",
                message="Backend returned an object outside the structured payload contract.",
                cause=type(raw).__name__,
            )

        return self._build_and_validate(raw, request)

    # ── private helpers ──────────────────────────────────────────────────

    def _project(self, request: ExtractionRequest) -> SafeExtractionInput:
        """Project only the safe fields into a ``SafeExtractionInput``."""
        safe_segments = tuple(
            SafeDocumentSegment(
                segment_id=seg.segment_id,
                text=seg.text,
                source_type=seg.source_type,
                location=seg.location,
            )
            for seg in request.document.segments
        )
        return SafeExtractionInput(
            paper_id=request.paper_id,
            promoter_name=request.promoter_name,
            promoter_id=request.promoter_id,
            paper_gene_synonym=request.paper_gene_synonym,
            property=request.property,
            document_segments=safe_segments,
        )

    def _build_and_validate(
        self,
        payload: RawPropertyPayload,
        request: ExtractionRequest,
    ) -> PropertyResult | TechnicalFailure:
        """Convert a ``RawPropertyPayload`` into a validated ``PropertyResult``."""
        # Step 1: validate status string.
        try:
            status = ScientificStatus(payload.status)
        except (TypeError, ValueError):
            return TechnicalFailure(
                stage="extraction",
                code="INVALID_BACKEND_STATUS",
                message=(
                    f"Backend returned an unrecognised status string. "
                    f"Expected one of: {[s.value for s in ScientificStatus]}."
                ),
                cause="ValueError",
            )

        # Step 2: build a segment lookup for evidence grounding.
        segments_by_id = {seg.segment_id: seg for seg in request.document.segments}

        # Step 3: build ExtractedValues.
        built_values: list[ExtractedValue] = []
        for raw_val in payload.values:
            if len(raw_val.evidence_segment_ids) != len(raw_val.evidence_fragments):
                return TechnicalFailure(
                    stage="extraction",
                    code="INVALID_BACKEND_PAYLOAD",
                    message=(
                        "Backend returned mismatched evidence identifiers and "
                        "fragments for an accepted value."
                    ),
                    cause="evidence_cardinality_mismatch",
                )
            norm = normalize_for_property(
                request.property,
                raw_val.value_raw,
                documentary_context=" ".join(raw_val.evidence_fragments),
            )
            evidence = self._build_value_evidence(raw_val, segments_by_id)
            built_values.append(
                ExtractedValue(
                    value_raw=raw_val.value_raw,
                    value_normalized=norm.value_normalized,
                    qualifier=raw_val.qualifier,
                    derivation_note=norm.derivation_note,
                    evidence=evidence,
                )
            )

        # Step 4: build RejectedCandidates.
        built_candidates: list[RejectedCandidate] = []
        for raw_cand in payload.candidates:
            if (raw_cand.evidence_segment_id is None) != (
                raw_cand.evidence_fragment is None
            ):
                return TechnicalFailure(
                    stage="extraction",
                    code="INVALID_BACKEND_PAYLOAD",
                    message=(
                        "Backend returned incomplete evidence for a rejected candidate."
                    ),
                    cause="candidate_evidence_cardinality_mismatch",
                )
            ev_item = self._build_candidate_evidence(raw_cand, segments_by_id)
            built_candidates.append(
                RejectedCandidate(
                    candidate_raw=raw_cand.candidate_raw,
                    rejection_reason=CandidateRejectionReason.INVALID_CANDIDATE,
                    evidence=ev_item,
                    rule_violated=raw_cand.rule_violated,
                )
            )

        # Step 5: build result-level evidence (for abstentions).
        result_evidence = self._build_result_evidence(payload, segments_by_id)

        # Step 6: build PropertyResult.
        result = PropertyResult(
            paper_id=request.paper_id,
            promoter_name=request.promoter_name,
            property=request.property,
            status=status,
            values=tuple(built_values),
            candidate_values=tuple(built_candidates),
            evidence=result_evidence,
            abstention_reason=payload.abstention_reason,
        )

        # Step 7: validate.
        return self._validator.validate(result, request, request.document)

    def _build_value_evidence(
        self,
        raw_val: RawValuePayload,
        segments_by_id: dict[str, DocumentSegment],
    ) -> tuple[EvidenceItem, ...]:
        items: list[EvidenceItem] = []
        for seg_id, fragment in zip(
            raw_val.evidence_segment_ids, raw_val.evidence_fragments
        ):
            seg = segments_by_id.get(seg_id)
            if seg is None:
                # Include with unknown type so validator can catch missing segment.
                items.append(
                    EvidenceItem(
                        fragment=fragment,
                        segment_id=seg_id,
                        source_type="unknown",
                        location=None,
                    )
                )
            else:
                items.append(
                    EvidenceItem(
                        fragment=fragment,
                        segment_id=seg_id,
                        source_type=seg.source_type,
                        location=seg.location,
                    )
                )
        return tuple(items)

    def _build_candidate_evidence(
        self,
        raw_cand: RawCandidatePayload,
        segments_by_id: dict[str, DocumentSegment],
    ) -> EvidenceItem | None:
        if raw_cand.evidence_segment_id is None:
            return None
        seg = segments_by_id.get(raw_cand.evidence_segment_id)
        fragment = raw_cand.evidence_fragment or ""
        if seg is None:
            return EvidenceItem(
                fragment=fragment,
                segment_id=raw_cand.evidence_segment_id,
                source_type="unknown",
                location=None,
            )
        return EvidenceItem(
            fragment=fragment,
            segment_id=raw_cand.evidence_segment_id,
            source_type=seg.source_type,
            location=seg.location,
        )

    def _build_result_evidence(
        self,
        payload: RawPropertyPayload,
        segments_by_id: dict[str, DocumentSegment],
    ) -> tuple[EvidenceItem, ...]:
        items: list[EvidenceItem] = []
        for seg_id, fragment in payload.result_evidence:
            seg = segments_by_id.get(seg_id)
            if seg is None:
                items.append(
                    EvidenceItem(
                        fragment=fragment,
                        segment_id=seg_id,
                        source_type="unknown",
                        location=None,
                    )
                )
            else:
                items.append(
                    EvidenceItem(
                        fragment=fragment,
                        segment_id=seg_id,
                        source_type=seg.source_type,
                        location=seg.location,
                    )
                )
        return tuple(items)


# ─── GuidedExtractionService ──────────────────────────────────────────────────

# Fixed property extraction order (matches Property enum declaration order).
_PROPERTY_ORDER: tuple[Property, ...] = (
    Property.TSS,
    Property.CAJA_10,
    Property.CAJA_35,
    Property.FACTOR_SIGMA,
)


class GuidedExtractionService:
    """Sequential four-property orchestrator for one paper × promoter pair.

    Creates four independent :class:`~promoter_ai_extraction.boundary.ExtractionRequest`
    objects (one per property), delegates each to :class:`PropertyExtractor`,
    and groups the four attempts into an :class:`~promoter_ai_extraction.models.ExtractionRun`.

    Property independence guarantee
    --------------------------------
    A technical failure in any one property attempt does **not** prevent the
    remaining three from being attempted.  All four slots in the returned
    ``ExtractionRun`` are always populated.
    """

    def __init__(
        self,
        extractor: PropertyExtractor,
        request_factory: ExtractionRequestFactory,
    ) -> None:
        self._extractor = extractor
        self._factory = request_factory

    def run(
        self,
        document: LoadedDocument,
        promoter_name: str,
        *,
        promoter_id: str | None = None,
        paper_gene_synonym: str | None = None,
        run_id: str | None = None,
    ) -> ExtractionRun:
        """Extract all four properties for *document* and return grouped results.

        Parameters
        ----------
        document:
            Already-loaded document.  ``document.paper_id`` is used as the
            paper identifier for all four attempts.
        promoter_name:
            Required promoter name.
        promoter_id:
            Optional promoter identifier.
        paper_gene_synonym:
            Optional paper-specific gene synonym.
        run_id:
            Optional caller-supplied run identifier.  A UUID is generated
            when omitted.

        Returns
        -------
        ExtractionRun
            Four property attempts grouped under one run identifier.
        """
        effective_run_id = run_id or str(uuid.uuid4())
        attempts: dict[Property, PropertyAttempt] = {}

        for prop in _PROPERTY_ORDER:
            attempt = self._attempt_one(
                document=document,
                paper_id=document.paper_id,
                promoter_name=promoter_name,
                promoter_id=promoter_id,
                paper_gene_synonym=paper_gene_synonym,
                prop=prop,
            )
            attempts[prop] = attempt

        return ExtractionRun(
            run_id=effective_run_id,
            paper_id=document.paper_id,
            promoter_name=promoter_name,
            tss=attempts[Property.TSS],
            caja_10=attempts[Property.CAJA_10],
            caja_35=attempts[Property.CAJA_35],
            sigma=attempts[Property.FACTOR_SIGMA],
        )

    def _attempt_one(
        self,
        document: LoadedDocument,
        paper_id: str,
        promoter_name: str,
        promoter_id: str | None,
        paper_gene_synonym: str | None,
        prop: Property,
    ) -> PropertyAttempt:
        """Run a single property extraction attempt, catching factory errors."""
        try:
            request = self._factory.create(
                {
                    "document": document,
                    "paper_id": paper_id,
                    "promoter_name": promoter_name,
                    "promoter_id": promoter_id,
                    "paper_gene_synonym": paper_gene_synonym,
                    "property": prop,
                }
            )
        except BoundaryViolation as exc:
            return TechnicalFailure(
                stage="extraction",
                code="REQUEST_BUILD_ERROR",
                message=f"Failed to build extraction request: {exc.message}",
                cause="BoundaryViolation",
            )
        return self._extractor.extract(request)
