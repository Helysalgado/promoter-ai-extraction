"""Safe extractor boundary — T010.

Provides the closed allowlist / defensive denylist gate that every extraction
request and case-manifest entry must pass before reaching the backend.

Public surface
--------------
BoundaryViolation          – typed exception with stable ``code`` and safe
                             ``message`` (never echoes private caller values)
ExtractionRequest          – immutable allowlisted request (6 fields only)
ExtractionRequestFactory   – validates a raw mapping and returns ExtractionRequest
SafeCaseManifest           – immutable identification + document-reference carrier
CaseManifestFactory        – validates a raw manifest mapping and returns
                             SafeCaseManifest

Design decisions
----------------
* DEFAULT DENY: every mapping key not in the closed allowlist is rejected.
* Denylist checked BEFORE allowlist: an explicit forbidden-field message is
  more informative than a generic "unknown field" message.
* Key normalization (lowercase + diacritic-strip + separator-collapse) detects
  case/accent/hyphen/space variants of denylist entries.
* Recursive inspection: nested dict values are scanned for forbidden keys; the
  document value (LoadedDocument) is a typed object and is never dict-scanned.
* BoundaryViolation messages are safe: they never echo caller-supplied values
  (those values may contain private gold, curator, or credential data).
* All public value objects are frozen dataclasses with slots=True.
"""
from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

from promoter_ai_extraction.documents import LoadedDocument
from promoter_ai_extraction.models import Property

# ---------------------------------------------------------------------------
# BoundaryViolation — typed exception
# ---------------------------------------------------------------------------


class BoundaryViolation(Exception):
    """Raised when an input mapping violates the closed allowlist or denylist.

    Attributes
    ----------
    code:
        Stable, machine-readable identifier for the violation kind.
        Never changes between releases for the same violation class.
    message:
        Human-readable description.  Must not contain values supplied by the
        caller; only field *names* (from the allowlist) may be mentioned.
    """

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


# ---------------------------------------------------------------------------
# Key normalization (denylist variant detection)
# ---------------------------------------------------------------------------


def _normalize_key(key: str) -> str:
    """Canonical form for denylist comparison.

    Steps:
    1. NFKD decomposition (separates base letter from combining marks).
    2. Strip combining characters (removes accents: Ñ→N, É→E, Á→A …).
    3. Lowercase.
    4. Replace hyphens and spaces with underscores.
    5. Collapse any run of repeated underscores to a single underscore.

    This lets ``Año_confirmado``, ``Ano_confirmado``, ``ano-confirmado``,
    ``ANO CONFIRMADO``, and ``GT__para__referencia`` (double underscore) all
    map to the same canonical form.
    """
    nfkd = unicodedata.normalize("NFKD", key)
    stripped = "".join(c for c in nfkd if not unicodedata.combining(c))
    collapsed = stripped.lower().replace("-", "_").replace(" ", "_")
    return re.sub(r"_+", "_", collapsed)


# ---------------------------------------------------------------------------
# Normalized denylist
# ---------------------------------------------------------------------------
# Keys are the *normalized* forms (via _normalize_key).  Incoming keys are
# also normalized before lookup so variants are transparently caught.
#
# Sources: plan §0 Defensive denylist, spec AC-28/AC-29.
#
# Rule: only inspect mapping *keys*, never document text — legitimate papers
# can legitimately mention these words; only the field names are the boundary.

_NORMALIZED_DENYLIST: frozenset[str] = frozenset(
    _normalize_key(k)
    for k in (
        # Named gold / RegulonDB / curator fields (plan §0)
        "Fila_origen",
        "Valor_RegulonDB",
        "Sin_dato_en_RegulonDB",
        "Modalidad_origen",
        "Valor_verificado_manualmente",
        "GT_para_referencia",
        "Año_confirmado",
        "Técnica_confirmada_manualmente",
        "Evidencia",
        "PMID_fuente_alternativa",
        # Split / adjudication fields
        "split",
        "split_assignment",
        "adjudication",
        "is_test",
        "is_dev",
        "benchmark_inclusion",
        # Evaluation labels / outcomes / scores / metrics
        "TP",
        "FP",
        "FN",
        "true_positive",
        "false_positive",
        "false_negative",
        "precision",
        "recall",
        "F1",
        "f1_score",
        "score",
        "metrics",
        "accuracy",
        "exact_match",
        # Previous outputs used as targets / derived expected answers
        "ground_truth",
        "target",
        "target_value",
        "gold",
        "gold_value",
        "gold_label",
        "expected",
        "expected_value",
        "curated_reference",
        "curated_value",
    )
)

# ---------------------------------------------------------------------------
# ExtractionRequest — immutable allowlisted request (6 fields)
# ---------------------------------------------------------------------------

#: Exact set of keys accepted by ExtractionRequestFactory.
_REQUEST_ALLOWLIST: frozenset[str] = frozenset(
    {
        "document",
        "paper_id",
        "promoter_id",
        "promoter_name",
        "paper_gene_synonym",
        "property",
    }
)


@dataclass(frozen=True, slots=True)
class ExtractionRequest:
    """Immutable, allowlisted extraction request for one paper × promoter × property.

    Contains exactly six fields — no metadata bag, no gold path, no evaluator
    data.  Created only through :class:`ExtractionRequestFactory`.

    Fields
    ------
    document:
        Fully loaded, segment-indexed document (format carried inside it).
    paper_id:
        Non-empty paper identifier.  Must match ``document.paper_id``.
    promoter_id:
        Optional promoter-database identifier.
    promoter_name:
        Required, non-empty promoter name as it appears in the document context.
    paper_gene_synonym:
        Optional paper-specific gene synonym to assist extraction.
    property:
        The one :class:`~promoter_ai_extraction.models.Property` requested for
        this extraction attempt.
    """

    document: LoadedDocument
    paper_id: str
    promoter_id: str | None
    promoter_name: str
    paper_gene_synonym: str | None
    property: Property


# ---------------------------------------------------------------------------
# SafeCaseManifest — immutable manifest entry (no target/evaluator columns)
# ---------------------------------------------------------------------------

#: Exact set of keys accepted by CaseManifestFactory.
_MANIFEST_ALLOWLIST: frozenset[str] = frozenset(
    {
        "document_path",
        "document_format",
        "paper_id",
        "promoter_id",
        "promoter_name",
        "paper_gene_synonym",
        "property",
    }
)

#: Accepted document format strings.
_VALID_FORMATS: frozenset[str] = frozenset({"TXT", "TEI/XML"})


@dataclass(frozen=True, slots=True)
class SafeCaseManifest:
    """Immutable manifest entry: document reference + extraction identity only.

    Contains only what is needed to locate the document and identify the
    extraction task.  No target column, no modality label, no curator field,
    no evaluation data.  Created only through :class:`CaseManifestFactory`.
    """

    document_path: Path
    document_format: Literal["TXT", "TEI/XML"]
    paper_id: str
    promoter_id: str | None
    promoter_name: str
    paper_gene_synonym: str | None
    property: Property


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _scan_value(value: Any) -> None:
    """Recursively scan a value for Mapping objects with forbidden keys.

    Rule: inspect only mapping *keys*, never scalar text — legitimate papers
    can contain forbidden words in their body; only field names are the boundary.

    Containers traversed: :class:`~collections.abc.Mapping`, list, tuple, set,
    frozenset.  Any other type (str, int, typed objects such as
    :class:`~promoter_ai_extraction.documents.LoadedDocument`) is skipped.

    Raises
    ------
    BoundaryViolation
        With code ``FORBIDDEN_FIELD`` on the first forbidden key found.
    """
    if isinstance(value, Mapping):
        _check_forbidden_keys(value, skip_values_of=frozenset())
    elif isinstance(value, (list, tuple, set, frozenset)):
        for item in value:
            _scan_value(item)
    # All other types (str, int, typed domain objects) → ignore


def _check_forbidden_keys(
    mapping: Mapping[str, Any],
    *,
    skip_values_of: frozenset[str] = frozenset(),
) -> None:
    """Recursively check mapping keys against the normalized denylist.

    Parameters
    ----------
    mapping:
        The mapping to inspect.
    skip_values_of:
        Keys whose *values* should not be recursively inspected (e.g. the
        ``"document"`` key holds a typed object, not a plain dict).

    Raises
    ------
    BoundaryViolation
        On the first forbidden key found, at any nesting level.
        Message does NOT echo the value.
    """
    for key, value in mapping.items():
        norm = _normalize_key(str(key))
        if norm in _NORMALIZED_DENYLIST:
            raise BoundaryViolation(
                code="FORBIDDEN_FIELD",
                message=(
                    "Input contains a field forbidden by the boundary contract. "
                    "Forbidden fields must not be supplied to the extractor."
                ),
            )
        # Recurse into nested structures — Mapping and sequence containers.
        # Skip the value when the key is in skip_values_of (e.g. "document").
        if key not in skip_values_of:
            _scan_value(value)


def _check_allowlist(
    mapping: Mapping[str, Any],
    allowlist: frozenset[str],
    context: str,
) -> None:
    """Ensure every top-level key is in *allowlist*.

    Parameters
    ----------
    mapping:
        The mapping to inspect (top-level keys only).
    allowlist:
        The closed set of permitted keys.
    context:
        Short label used in the error message (``"request"`` or ``"manifest"``).

    Raises
    ------
    BoundaryViolation
        If any key is not in the allowlist.
        The count of unknown keys is mentioned but the key names are NOT echoed
        (a key name could itself encode private data via an evasion attempt).
    """
    unknown = frozenset(mapping.keys()) - allowlist
    if unknown:
        raise BoundaryViolation(
            code="UNKNOWN_FIELD",
            message=(
                f"{context.capitalize()} contains {len(unknown)} field(s) not "
                f"present in the closed allowlist. Only allowlisted fields are accepted."
            ),
        )


# ---------------------------------------------------------------------------
# ExtractionRequestFactory
# ---------------------------------------------------------------------------


class ExtractionRequestFactory:
    """Validates a raw mapping and returns an immutable :class:`ExtractionRequest`.

    Validation order
    ----------------
    1. Recursive denylist check (forbidden fields, including variants).
    2. Top-level allowlist check (rejects unknown / renamed keys).
    3. Type and value validation for each allowlisted field.
    4. Identity consistency check (paper_id must match document.paper_id).
    """

    def create(self, mapping: Mapping[str, Any]) -> ExtractionRequest:
        """Return a validated, immutable ExtractionRequest.

        Parameters
        ----------
        mapping:
            Raw input dict.  The ``"document"`` value is not recursively
            dict-scanned (it is a typed LoadedDocument, not a plain dict).

        Raises
        ------
        BoundaryViolation
            On any constraint violation.  Messages never echo caller values.
        """
        # Step 1 — denylist (recursive; skip the document value)
        _check_forbidden_keys(mapping, skip_values_of=frozenset({"document"}))

        # Step 2 — closed allowlist (top-level only)
        _check_allowlist(mapping, _REQUEST_ALLOWLIST, context="request")

        # Step 3 — field type / value validation
        document = mapping.get("document")
        if not isinstance(document, LoadedDocument):
            raise BoundaryViolation(
                code="INVALID_FIELD_TYPE",
                message="'document' must be a LoadedDocument instance.",
            )

        paper_id = mapping.get("paper_id")
        if not isinstance(paper_id, str) or not paper_id.strip():
            raise BoundaryViolation(
                code="INVALID_FIELD_VALUE",
                message="'paper_id' must be a non-empty string.",
            )

        promoter_name = mapping.get("promoter_name")
        if not isinstance(promoter_name, str) or not promoter_name.strip():
            raise BoundaryViolation(
                code="INVALID_FIELD_VALUE",
                message="'promoter_name' must be a non-empty string.",
            )

        prop = mapping.get("property")
        if not isinstance(prop, Property):
            raise BoundaryViolation(
                code="INVALID_FIELD_TYPE",
                message="'property' must be a Property enum member.",
            )

        promoter_id = mapping.get("promoter_id")
        if promoter_id is not None:
            if not isinstance(promoter_id, str):
                raise BoundaryViolation(
                    code="INVALID_FIELD_TYPE",
                    message="'promoter_id' must be a string or None.",
                )
            if not promoter_id.strip():
                raise BoundaryViolation(
                    code="INVALID_FIELD_VALUE",
                    message="'promoter_id', when supplied, must be a non-empty string.",
                )

        paper_gene_synonym = mapping.get("paper_gene_synonym")
        if paper_gene_synonym is not None:
            if not isinstance(paper_gene_synonym, str):
                raise BoundaryViolation(
                    code="INVALID_FIELD_TYPE",
                    message="'paper_gene_synonym' must be a string or None.",
                )
            if not paper_gene_synonym.strip():
                raise BoundaryViolation(
                    code="INVALID_FIELD_VALUE",
                    message="'paper_gene_synonym', when supplied, must be a non-empty string.",
                )

        # Step 4 — identity consistency
        if paper_id != document.paper_id:
            raise BoundaryViolation(
                code="IDENTITY_MISMATCH",
                message=(
                    "The supplied paper_id does not match the loaded document's "
                    "paper_id. Both must identify the same paper."
                ),
            )

        return ExtractionRequest(
            document=document,
            paper_id=paper_id,
            promoter_id=promoter_id,
            promoter_name=promoter_name,
            paper_gene_synonym=paper_gene_synonym,
            property=prop,
        )


# ---------------------------------------------------------------------------
# CaseManifestFactory
# ---------------------------------------------------------------------------


class CaseManifestFactory:
    """Validates a raw manifest row mapping and returns a :class:`SafeCaseManifest`.

    Validation order mirrors ExtractionRequestFactory:
    1. Recursive denylist check.
    2. Top-level manifest allowlist check.
    3. Type and value validation.
    """

    def from_mapping(self, mapping: Mapping[str, Any]) -> SafeCaseManifest:
        """Return a validated, immutable SafeCaseManifest.

        Raises
        ------
        BoundaryViolation
            On any constraint violation.
        """
        # Step 1 — denylist (recursive; no special skip needed for manifests)
        _check_forbidden_keys(mapping)

        # Step 2 — closed allowlist
        _check_allowlist(mapping, _MANIFEST_ALLOWLIST, context="manifest")

        # Step 3 — field validation
        raw_path = mapping.get("document_path")
        if raw_path is None:
            raise BoundaryViolation(
                code="INVALID_FIELD_VALUE",
                message="'document_path' is required and must be a non-empty string or Path.",
            )
        # Reject empty or whitespace-only strings before Path() silently converts
        # '' → Path('.') or '   ' → a nonsensical whitespace path.
        if isinstance(raw_path, str) and not raw_path.strip():
            raise BoundaryViolation(
                code="INVALID_FIELD_VALUE",
                message="'document_path' must be a non-empty, non-whitespace path.",
            )
        try:
            doc_path = Path(raw_path)  # type: ignore[arg-type]
        except TypeError:
            raise BoundaryViolation(
                code="INVALID_FIELD_TYPE",
                message="'document_path' must be a string or Path-like object.",
            )

        doc_format = mapping.get("document_format")
        if not isinstance(doc_format, str):
            raise BoundaryViolation(
                code="INVALID_FIELD_TYPE",
                message="'document_format' must be a string.",
            )
        if doc_format not in _VALID_FORMATS:
            raise BoundaryViolation(
                code="INVALID_FIELD_VALUE",
                message=f"'document_format' must be one of {sorted(_VALID_FORMATS)}.",
            )

        paper_id = mapping.get("paper_id")
        if not isinstance(paper_id, str) or not paper_id.strip():
            raise BoundaryViolation(
                code="INVALID_FIELD_VALUE",
                message="'paper_id' must be a non-empty string.",
            )

        promoter_name = mapping.get("promoter_name")
        if not isinstance(promoter_name, str) or not promoter_name.strip():
            raise BoundaryViolation(
                code="INVALID_FIELD_VALUE",
                message="'promoter_name' must be a non-empty string.",
            )

        prop = mapping.get("property")
        if not isinstance(prop, Property):
            raise BoundaryViolation(
                code="INVALID_FIELD_TYPE",
                message="'property' must be a Property enum member.",
            )

        promoter_id = mapping.get("promoter_id")
        if promoter_id is not None:
            if not isinstance(promoter_id, str):
                raise BoundaryViolation(
                    code="INVALID_FIELD_TYPE",
                    message="'promoter_id' must be a string or None.",
                )
            if not promoter_id.strip():
                raise BoundaryViolation(
                    code="INVALID_FIELD_VALUE",
                    message="'promoter_id', when supplied, must be a non-empty string.",
                )

        paper_gene_synonym = mapping.get("paper_gene_synonym")
        if paper_gene_synonym is not None:
            if not isinstance(paper_gene_synonym, str):
                raise BoundaryViolation(
                    code="INVALID_FIELD_TYPE",
                    message="'paper_gene_synonym' must be a string or None.",
                )
            if not paper_gene_synonym.strip():
                raise BoundaryViolation(
                    code="INVALID_FIELD_VALUE",
                    message="'paper_gene_synonym', when supplied, must be a non-empty string.",
                )

        return SafeCaseManifest(
            document_path=doc_path,
            document_format=cast(Literal["TXT", "TEI/XML"], doc_format),
            paper_id=paper_id,
            promoter_id=promoter_id,
            promoter_name=promoter_name,
            paper_gene_synonym=paper_gene_synonym,
            property=prop,
        )


# ---------------------------------------------------------------------------
# DevelopmentCase — paper × promoter file row (T039; no property, no gold)
# ---------------------------------------------------------------------------

#: Exact set of keys accepted by a development-case row. The runner requests
#: the fixed four-property set (spec §Inputs); property is not a file column.
DEVELOPMENT_CASE_ALLOWLIST: frozenset[str] = frozenset(
    {
        "document_path",
        "document_format",
        "paper_id",
        "promoter_id",
        "promoter_name",
        "paper_gene_synonym",
    }
)


@dataclass(frozen=True, slots=True)
class DevelopmentCase:
    """One leakage-safe development case: paper × promoter + document reference."""

    document_path: Path
    document_format: Literal["TXT", "TEI/XML"]
    paper_id: str
    promoter_id: str | None
    promoter_name: str
    paper_gene_synonym: str | None


class DevelopmentCaseFactory:
    """Validates one development-manifest row (identities and document reference)."""

    def from_mapping(self, mapping: Mapping[str, Any]) -> DevelopmentCase:
        _check_forbidden_keys(mapping)
        _check_allowlist(mapping, DEVELOPMENT_CASE_ALLOWLIST, context="manifest")

        raw_path = mapping.get("document_path")
        if raw_path is None:
            raise BoundaryViolation(
                code="INVALID_FIELD_VALUE",
                message="'document_path' is required and must be a non-empty string or Path.",
            )
        if isinstance(raw_path, str) and not raw_path.strip():
            raise BoundaryViolation(
                code="INVALID_FIELD_VALUE",
                message="'document_path' must be a non-empty, non-whitespace path.",
            )
        try:
            doc_path = Path(raw_path)  # type: ignore[arg-type]
        except TypeError:
            raise BoundaryViolation(
                code="INVALID_FIELD_TYPE",
                message="'document_path' must be a string or Path-like object.",
            )

        doc_format = mapping.get("document_format")
        if not isinstance(doc_format, str):
            raise BoundaryViolation(
                code="INVALID_FIELD_TYPE",
                message="'document_format' must be a string.",
            )
        if doc_format not in _VALID_FORMATS:
            raise BoundaryViolation(
                code="INVALID_FIELD_VALUE",
                message=f"'document_format' must be one of {sorted(_VALID_FORMATS)}.",
            )

        paper_id = mapping.get("paper_id")
        if not isinstance(paper_id, str) or not paper_id.strip():
            raise BoundaryViolation(
                code="INVALID_FIELD_VALUE",
                message="'paper_id' must be a non-empty string.",
            )

        promoter_name = mapping.get("promoter_name")
        if not isinstance(promoter_name, str) or not promoter_name.strip():
            raise BoundaryViolation(
                code="INVALID_FIELD_VALUE",
                message="'promoter_name' must be a non-empty string.",
            )

        promoter_id = mapping.get("promoter_id")
        if promoter_id is not None:
            if not isinstance(promoter_id, str):
                raise BoundaryViolation(
                    code="INVALID_FIELD_TYPE",
                    message="'promoter_id' must be a string or None.",
                )
            if not promoter_id.strip():
                raise BoundaryViolation(
                    code="INVALID_FIELD_VALUE",
                    message="'promoter_id', when supplied, must be a non-empty string.",
                )

        paper_gene_synonym = mapping.get("paper_gene_synonym")
        if paper_gene_synonym is not None:
            if not isinstance(paper_gene_synonym, str):
                raise BoundaryViolation(
                    code="INVALID_FIELD_TYPE",
                    message="'paper_gene_synonym' must be a string or None.",
                )
            if not paper_gene_synonym.strip():
                raise BoundaryViolation(
                    code="INVALID_FIELD_VALUE",
                    message="'paper_gene_synonym', when supplied, must be a non-empty string.",
                )

        return DevelopmentCase(
            document_path=doc_path,
            document_format=cast(Literal["TXT", "TEI/XML"], doc_format),
            paper_id=paper_id,
            promoter_id=promoter_id,
            promoter_name=promoter_name,
            paper_gene_synonym=paper_gene_synonym,
        )
