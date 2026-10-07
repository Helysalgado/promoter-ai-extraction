"""Immutable domain contracts for the guided extraction baseline (T004).

All public types are frozen (immutable after construction).  Enums use
StrEnum so values compare equal to their string representation without
explicit `.value` access, which keeps downstream code readable.

Hierarchy (bottom-up)
---------------------
EvidenceItem         – one fragment + location from the supplied document
ExtractedValue       – one accepted documentary value with evidence
RejectedCandidate    – a candidate that violated a rule; never an accepted value
PropertyResult       – one scientific conclusion for one paper×promoter×property
TechnicalFailure     – a non-scientific failure (never a scientific abstention)
PropertyAttempt      – union alias: PropertyResult | TechnicalFailure
ExtractionRun        – four property attempts grouped under one run (defined later)

Design decisions (T004):
  - StrEnum (Python ≥3.11) instead of plain Enum so enum members compare to
    str without `.value`.  Required by spec AC-06/AC-07 (raw string round-trip).
  - @dataclass(frozen=True, slots=True) (Python ≥3.10): hashable, no __dict__
    overhead, mutation raises FrozenInstanceError.
  - PropertyAttempt is a plain union alias (Python ≥3.10 | syntax); it is not
    a subclass so no ABC overhead is introduced.
  - Evidence is stored as tuple[EvidenceItem, ...] (immutable sequence) on both
    ExtractedValue and PropertyResult so neither can be mutated post-construction.
  - Constitution principle 6: TechnicalFailure.code must never equal a
    ScientificStatus value — enforced by separate type hierarchies, not by a
    shared base class.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


# ---------------------------------------------------------------------------
# Property — the four requested extraction targets
# ---------------------------------------------------------------------------


class Property(StrEnum):
    """The four bacterial-promoter properties requested per extraction run.

    String values match the Spanish-language column headers used in the gold
    workbook (``Propiedad`` column) so comparison requires no translation.
    """

    TSS = "TSS"
    CAJA_10 = "Caja -10"
    CAJA_35 = "Caja -35"
    FACTOR_SIGMA = "Factor sigma"


# ---------------------------------------------------------------------------
# ScientificStatus — terminal status for one PropertyResult
# ---------------------------------------------------------------------------


class ScientificStatus(StrEnum):
    """The five terminal scientific statuses for a property extraction attempt.

    ``INVALID_CANDIDATE`` is intentionally absent — it is a candidate-level
    diagnostic (see :class:`CandidateRejectionReason`), not a terminal status.

    Constitution principle 6: scientific abstention and technical failure stay
    distinct.  None of these values may appear as a TechnicalFailure code.
    """

    EXTRACTED = "EXTRACTED"
    NOT_FOUND = "NOT_FOUND"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    UNSUPPORTED_MODALITY = "UNSUPPORTED_MODALITY"
    AMBIGUOUS = "AMBIGUOUS"


# ---------------------------------------------------------------------------
# CandidateRejectionReason — diagnostic label for a rejected candidate
# ---------------------------------------------------------------------------


class CandidateRejectionReason(StrEnum):
    """Rejection reasons attached to a :class:`RejectedCandidate`.

    ``INVALID_CANDIDATE`` is a candidate-level diagnostic, not a terminal
    scientific status (spec §Candidate diagnostics; AC-30).  A rejected
    candidate never counts as a prediction and must not promote to accepted
    values.
    """

    INVALID_CANDIDATE = "INVALID_CANDIDATE"


# ---------------------------------------------------------------------------
# EvidenceItem — one documentary fragment + location
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class EvidenceItem:
    """A single evidence fragment from the supplied document.

    Attributes
    ----------
    fragment:
        The verbatim text excerpt or documentary pointer that supports the
        associated value or abstention.
    segment_id:
        Stable identifier of the document segment from which the fragment
        was drawn.
    source_type:
        Canonical segment type.  Accepted values: ``"body_text"``,
        ``"table"``, ``"figure_caption"``, ``"figure_reference"``,
        ``"figure_associated_text"``, ``"other"``.
    location:
        All available document location information (section, paragraph, page,
        XML id, …) as a single string, or ``None`` when the representation
        provides no stable reference.  The system does not invent unavailable
        precision.
    """

    fragment: str
    segment_id: str
    source_type: str
    location: str | None


# ---------------------------------------------------------------------------
# ExtractedValue — one accepted documentary value with evidence
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ExtractedValue:
    """One accepted value for a property, grounded in document evidence.

    Spec constraints:
    - ``value_raw`` preserves the documentary form exactly.
    - ``value_normalized`` uses only contract-approved transformations and is
      kept separate from ``value_raw`` (AC-06).
    - ``qualifier`` preserves paper-stated qualifiers such as ``"putative"``,
      ``"predicted"``, ``"possible"``, or ``"-like"`` (AC-08).
    - ``derivation_note`` makes any documentary transformation traceable
      without exposing private reasoning (AC-06).
    - ``evidence`` is an immutable tuple of documentary fragments.
      Evidence cardinality (non-empty requirement per AC-05, AC-10) is enforced
      by ``OutputValidator`` (T013/T014), not at construction time.
    """

    value_raw: str
    value_normalized: str
    qualifier: str | None
    derivation_note: str | None
    evidence: tuple[EvidenceItem, ...]


# ---------------------------------------------------------------------------
# RejectedCandidate — a candidate that violated a rule
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RejectedCandidate:
    """A candidate value that was rejected by a scientific or formal rule.

    A ``RejectedCandidate``:
    - is never promoted to ``ExtractedValue`` (AC-30);
    - does not determine the terminal scientific status of the property;
    - is auditable through ``rejection_reason``, ``rule_violated``, and
      optional ``evidence``.

    ``rejection_reason`` is typed as :class:`CandidateRejectionReason` rather
    than ``ScientificStatus`` to enforce the separation at the type level.
    """

    candidate_raw: str
    rejection_reason: CandidateRejectionReason
    evidence: EvidenceItem | None
    rule_violated: str


# ---------------------------------------------------------------------------
# PropertyResult — one scientific conclusion for paper × promoter × property
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PropertyResult:
    """The scientific conclusion for one paper × promoter × property triplet.

    Identity fields (``paper_id``, ``promoter_name``, ``property``) link every
    result to the extraction request and satisfy AC-03, AC-21.

    Status rules (enforced by :mod:`promoter_ai_extraction.validation`):
    - ``EXTRACTED``: ``values`` must be non-empty; ``abstention_reason`` is
      ``None``.
    - Abstention statuses (``NOT_FOUND``, ``INSUFFICIENT_EVIDENCE``,
      ``UNSUPPORTED_MODALITY``, ``AMBIGUOUS``): ``values`` must be empty;
      ``abstention_reason`` should be present.

    ``candidate_values`` may contain ``RejectedCandidate`` entries for any
    status; they are diagnostic and never count as predictions (AC-30).
    """

    paper_id: str
    promoter_name: str
    property: Property
    status: ScientificStatus
    values: tuple[ExtractedValue, ...]
    candidate_values: tuple[RejectedCandidate, ...]
    evidence: tuple[EvidenceItem, ...]
    abstention_reason: str | None


# ---------------------------------------------------------------------------
# TechnicalFailure — a non-scientific processing failure
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class TechnicalFailure:
    """A technical failure that prevents or invalidates an extraction attempt.

    Constitution principle 6: a TechnicalFailure is never stored as a
    ScientificStatus.  Its ``code`` must never equal a :class:`ScientificStatus`
    value.  This is enforced by keeping them in separate type hierarchies.

    Attributes
    ----------
    stage:
        The processing stage at which the failure occurred (e.g.
        ``"document_loading"``, ``"extraction"``, ``"validation"``,
        ``"persistence"``).
    code:
        A stable, machine-readable failure code (e.g. ``"UNREADABLE_INPUT"``,
        ``"MALFORMED_XML"``, ``"BACKEND_ERROR"``, ``"VALIDATION_FAILED"``).
        Must not equal any :class:`ScientificStatus` value.
    message:
        A human-readable, safe description of the failure.  Must not contain
        private data, gold values, or credentials.
    cause:
        The exception type or cause category (e.g. ``"FileNotFoundError"``,
        ``"ParseError"``, ``"TimeoutError"``).
    """

    stage: str
    code: str
    message: str
    cause: str

    def __post_init__(self) -> None:
        """Mechanically enforce constitution principle 6.

        A TechnicalFailure must never carry a code that equals any
        :class:`ScientificStatus` value.  Mixing these types would allow a
        technical failure to masquerade as a scientific conclusion.
        """
        scientific_codes = {s.value for s in ScientificStatus}
        if self.code in scientific_codes:
            raise ValueError(
                f"TechnicalFailure.code must not equal a ScientificStatus value "
                f"(constitution principle 6). Use a stable, non-scientific code."
            )


# ---------------------------------------------------------------------------
# PropertyAttempt — union alias consumed by ExtractionRun
# ---------------------------------------------------------------------------

#: Union of a successful scientific result and a technical failure.
#: Each property slot in an :class:`ExtractionRun` holds exactly one attempt.
#: A technical failure coexists with valid results in the same run but never
#: becomes an accepted value or a scientific abstention.
PropertyAttempt = PropertyResult | TechnicalFailure


# ---------------------------------------------------------------------------
# ExtractionRun — four property attempts grouped under one run (T018)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ExtractionRun:
    """Four independent property attempts grouped for one paper × promoter pair.

    Attributes
    ----------
    run_id:
        Unique identifier for this extraction run (e.g. a UUID or timestamp-
        based string).
    paper_id:
        The paper identifier shared by all four attempts.
    promoter_name:
        The promoter name shared by all four attempts.
    tss:
        The extraction attempt for :attr:`~Property.TSS`.
    caja_10:
        The extraction attempt for :attr:`~Property.CAJA_10`.
    caja_35:
        The extraction attempt for :attr:`~Property.CAJA_35`.
    sigma:
        The extraction attempt for :attr:`~Property.FACTOR_SIGMA`.

    Each slot holds either a :class:`PropertyResult` (scientific conclusion)
    or a :class:`TechnicalFailure` (non-scientific processing failure).
    A failure in one slot does not affect the other three slots.
    """

    run_id: str
    paper_id: str
    promoter_name: str
    tss: PropertyAttempt
    caja_10: PropertyAttempt
    caja_35: PropertyAttempt
    sigma: PropertyAttempt
