"""Pure property-specific normalizers for the guided extraction baseline (T012).

All functions are **pure** — no side effects, no global state, deterministic.
Gold, curator, and evaluator data never enter this module.

Allowed transformations per the authoritative contracts
-------------------------------------------------------
TSS (extraction-contract §26, TSS-01…TSS-06):
  - A signed integer string (``-42``, ``+42``, ``0``, ``+1``) is returned
    as-is after stripping outer whitespace.
  - A bare non-negative integer (genomic coordinate) is returned as-is.
  - Without a clear, unambiguous documentary anchor, the raw form is preserved
    and sign is *not* auto-assigned (TSS-04).

Caja -10 / Caja -35 (BOX-06/BOX-07):
  - Convert the entire sequence string to uppercase.
  - Remove typographic spaces, hyphens, and internal line-breaks.
  - Nucleotide bases are **never** corrected, completed, or substituted.

Factor sigma (SIG-02/SIG-03):
  - Replace Greek σ/Σ with the ASCII prefix ``sigma``.
  - Lowercase the ``sigma`` prefix.
  - Remove any whitespace between ``sigma`` and its designator.
  - Biological Rpo/sigma equivalences (RpoS↔sigma38, RpoH↔sigma32 …) are
    explicitly **not** applied (SIG-03).

Design
------
Each function returns a :class:`NormalizationResult`.  The raw input string is
the caller's responsibility to preserve in ``ExtractedValue.value_raw``.
``derivation_note`` is ``None`` when the input required no transformation, and
a human-readable description when at least one transformation was applied.

This module has no runtime dependency on the production domain models to avoid
import cycles; the caller dispatches via :func:`normalize_for_property`.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

__all__ = [
    "NormalizationResult",
    "normalize_box_sequence",
    "normalize_for_property",
    "normalize_sigma",
    "normalize_tss",
]

# ─── Return type ──────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class NormalizationResult:
    """Immutable result of a pure property-specific normalization call.

    Attributes
    ----------
    value_normalized:
        The form produced by permitted transformations only.  Equal to the
        input when no transformation was needed.
    derivation_note:
        Human-readable description of the transformation applied, or ``None``
        when the input was already in normalized form.  Must not contain
        private data, gold values, or credentials.
    """

    value_normalized: str
    derivation_note: str | None = None


# ─── TSS normalizer ───────────────────────────────────────────────────────────

# Matches a complete signed-integer string (including bare unsigned ints and
# conventional TSS designations such as +1). Sign characters are ASCII only.
_SIGNED_INTEGER_RE = re.compile(r"^[+-]?\d+$")
# Leading glyphs that GROBID and typography use as a minus, never as a digit.
# U+03EA (Coptic gangia / GROBID minus) and U+2212 (MINUS SIGN).
_TYPOGRAPHIC_MINUS = frozenset({"\u03ea", "\u2212"})
_TSS_DISTANCE_RE = re.compile(
    r"^(?P<distance>\d+)\s*(?:bp)?\s+"
    r"(?P<direction>upstream|downstream)(?P<context>.*)$",
    re.IGNORECASE,
)
_TSS_ANCHOR = (
    r"(?:translation(?:al)?\s+start|start\s+codon|initiation\s+codon|"
    r"gene\s+start|ATG)"
)
# Distance, relation, and anchor must sit in one clause. The gap allows a
# short modifier such as "proposed radC" and does not cross punctuation.
_TSS_CLAUSE_RE = re.compile(
    r"(?P<sign>[+\-\u03ea\u2212])?\s*"
    r"(?P<distance>\d+)\s*bp\s+"
    r"(?P<relation>upstream\s+of|downstream\s+of|from)\s+"
    r"(?:the\s+)?"
    r"(?:[\w]+\s+){0,6}?"
    rf"(?P<anchor>{_TSS_ANCHOR})\b",
    re.IGNORECASE,
)
_CLAUSE_CONFLICT = object()
_TRANSLATION_ANCHOR_RE = re.compile(
    r"\b(?:translation(?:al)?\s+start|start\s+codon|initiation\s+codon|"
    r"gene\s+start|ATG)\b",
    re.IGNORECASE,
)


def normalize_tss(raw: str, *, anchor_context: str | None = None) -> NormalizationResult:
    """Normalize a TSS raw value string.

    Permitted transformations
    -------------------------
    - Strip leading/trailing whitespace.
    - A signed (or unsigned) integer string is returned as-is (covers
      ``-42``, ``+42``, ``0``, ``+1``, genomic coordinates).
    - A whole token whose only sign is U+03EA or U+2212 followed by digits
      folds that sign to ASCII ``-``. Prose that merely contains the glyph
      is left unchanged. An unsigned digit string never gains a sign.
    - A documentary upstream/downstream distance is signed only when the raw
      form or the explicitly supplied context names an approved
      translation-start anchor.
    - One ``bp`` distance in the same clause as an approved anchor becomes a
      signed integer. An explicit sign is kept. ``upstream`` and
      ``downstream`` supply a sign only when the clause has none. ``from``
      without a sign does not. Product lengths in ``nt`` are not distances.
      Two disagreeing distances are left unchanged.

    Not permitted
    -------------
    - Assigning a sign to a plain distance that lacks an unambiguous
      documentary anchor (TSS-04).
    - Converting ``+1`` from a TSS designation to a relative position
      (TSS-05).
    - Using RegulonDB, a genome, consensus, or any external source.

    Parameters
    ----------
    raw:
        The documentary value string extracted by the backend.
    anchor_context:
        Optional documentary context from the supplied paper. It may authorize
        sign derivation only when it explicitly names an approved
        translation-start anchor.
    """
    stripped = raw.strip()
    folded, folded_sign = _fold_typographic_integer_sign(stripped)
    # Plain or signed integers (covers -42, +42, 0, +1, and genomic coords).
    if _SIGNED_INTEGER_RE.match(folded):
        note = (
            "typographic minus folded to ASCII hyphen-minus"
            if folded_sign
            else None
        )
        return NormalizationResult(value_normalized=folded, derivation_note=note)

    anchored, blocked = _anchored_bp_distance(stripped)
    if blocked:
        return NormalizationResult(value_normalized=stripped, derivation_note=None)
    if anchored is not None:
        return NormalizationResult(
            value_normalized=anchored,
            derivation_note=(
                "documentary bp distance normalized to a signed integer at the "
                "explicit translation-start anchor"
            ),
        )

    distance_match = _TSS_DISTANCE_RE.match(stripped)
    if distance_match:
        documentary_context = " ".join(
            part
            for part in (
                distance_match.group("context"),
                anchor_context,
            )
            if part
        )
        if _TRANSLATION_ANCHOR_RE.search(documentary_context):
            sign = "-" if distance_match.group("direction").lower() == "upstream" else "+"
            return NormalizationResult(
                value_normalized=f"{sign}{distance_match.group('distance')}",
                derivation_note=(
                    "documentary distance normalized relative to the explicit "
                    "translation-start anchor; upstream is negative and downstream "
                    "is positive"
                ),
            )

    # All other forms: preserve the stripped raw form unchanged (TSS-04).
    return NormalizationResult(value_normalized=stripped, derivation_note=None)


def _anchored_bp_distance(stripped: str) -> tuple[str | None, bool]:
    """Return one agreed signed distance, and whether the clause set is blocked.

    A block means two usable distances disagree, or a sign contradicts
    ``upstream`` or ``downstream``. The caller must keep the raw phrase.
    """
    found: list[str] = []
    blocked = False
    for match in _TSS_CLAUSE_RE.finditer(stripped):
        interpreted = _interpret_distance_clause(match)
        if interpreted is _CLAUSE_CONFLICT:
            blocked = True
        elif isinstance(interpreted, str):
            found.append(interpreted)
    unique = set(found)
    if blocked or len(unique) > 1:
        return None, True
    if len(unique) == 1:
        return next(iter(unique)), False
    return None, False


def _interpret_distance_clause(match: re.Match[str]) -> str | object | None:
    """Map one distance clause to a signed integer, or skip it.

    ``from`` without an explicit sign is not a usable distance. An explicit
    sign that disagrees with ``upstream`` or ``downstream`` is a conflict.
    """
    relation = re.sub(r"\s+", " ", match.group("relation").lower())
    inferred = {"upstream of": "-", "downstream of": "+"}.get(relation)
    sign = match.group("sign")
    distance = match.group("distance")
    if sign is None:
        if inferred is None:
            return None
        return f"{inferred}{distance}"
    explicit = "-" if sign == "-" or sign in _TYPOGRAPHIC_MINUS else "+"
    if inferred is not None and inferred != explicit:
        return _CLAUSE_CONFLICT
    return f"{explicit}{distance}"


def _fold_typographic_integer_sign(stripped: str) -> tuple[str, bool]:
    """Fold a leading typographic minus only on a complete integer token."""
    if len(stripped) < 2 or stripped[0] not in _TYPOGRAPHIC_MINUS:
        return stripped, False
    digits = stripped[1:]
    if not digits.isdigit():
        return stripped, False
    return f"-{digits}", True


# ─── Box sequence normalizer ──────────────────────────────────────────────────

# Typographic separators that are unambiguously presentational:
# whitespace characters (space, tab, newline, \r) and hyphens.
_BOX_SEPARATORS_RE = re.compile(r"[\s\-]")


def normalize_box_sequence(raw: str) -> NormalizationResult:
    """Normalize a Caja -10 or -35 nucleotide sequence string.

    Permitted transformations (BOX-06)
    -----------------------------------
    - Convert to uppercase.
    - Remove typographic spaces, hyphens, and line-breaks within the sequence.

    Not permitted (BOX-07)
    -----------------------
    - Nucleotide base correction.
    - Completion from a genome or consensus.
    - Substitution by a more plausible alternative.
    """
    upper = raw.upper()
    normalized = _BOX_SEPARATORS_RE.sub("", upper)

    if normalized == raw:
        # Already in normalized form — no derivation note.
        return NormalizationResult(value_normalized=normalized, derivation_note=None)

    # Build a descriptive note for the curator / audit trail.
    notes: list[str] = []
    if raw != raw.upper():
        notes.append("converted to uppercase")
    if _BOX_SEPARATORS_RE.search(raw):
        notes.append("removed typographic separators (spaces, hyphens, line-breaks)")

    derivation_note = "; ".join(notes) if notes else "typographic normalization applied"
    return NormalizationResult(value_normalized=normalized, derivation_note=derivation_note)


# ─── Sigma normalizer ─────────────────────────────────────────────────────────

# Matches the Greek lowercase and uppercase sigma characters.
_GREEK_SIGMA_RE = re.compile(r"[σΣ]")

# Case-insensitive match of the 'sigma' prefix, consuming any trailing whitespace.
# Used to detect and normalize the prefix to lowercase + remove internal space.
_SIGMA_PREFIX_RE = re.compile(r"^sigma\s*", re.IGNORECASE)


def normalize_sigma(raw: str) -> NormalizationResult:
    """Normalize a factor sigma label string.

    Permitted transformations (SIG-02)
    ------------------------------------
    - Replace Greek σ or Σ with the ASCII string ``sigma``.
    - Lowercase the ``sigma`` prefix.
    - Remove any whitespace between ``sigma`` and its designator.

    Not permitted (SIG-03)
    -----------------------
    - Biological Rpo ↔ sigma equivalences (RpoS ↔ sigma38, RpoH ↔ sigma32,
      RpoN ↔ sigma54, …).  Those require an explicit, globally versioned table
      that has not been approved for this baseline.
    """
    changed = False
    current = raw

    # Step 1: Greek symbol → ASCII 'sigma'.
    if _GREEK_SIGMA_RE.search(current):
        current = _GREEK_SIGMA_RE.sub("sigma", current)
        changed = True

    # Step 2: Normalize sigma prefix (lowercase + remove internal whitespace).
    m = _SIGMA_PREFIX_RE.match(current)
    if m:
        designator = current[m.end():]
        normalized = "sigma" + designator
        if normalized != current:
            changed = True
        current = normalized

    if not changed:
        return NormalizationResult(value_normalized=current, derivation_note=None)

    return NormalizationResult(
        value_normalized=current,
        derivation_note=(
            "sigma label normalized: Greek symbol or case/space variants replaced "
            "with lowercase ASCII 'sigma' prefix"
        ),
    )


# ─── Property dispatch ────────────────────────────────────────────────────────


def normalize_for_property(
    prop: object,
    raw: str,
    *,
    documentary_context: str | None = None,
) -> NormalizationResult:
    """Dispatch normalization to the correct property-specific function.

    Parameters
    ----------
    prop:
        A :class:`~promoter_ai_extraction.models.Property` enum member.
        Imported lazily to avoid circular imports during module initialization.
    raw:
        The raw documentary value string.
    documentary_context:
        Evidence text linked to this value. Used only for conservative TSS
        anchor detection; ignored by the other property normalizers.
    """
    # Lazy import avoids a circular dependency at module level.
    from promoter_ai_extraction.models import Property  # noqa: PLC0415

    if prop == Property.TSS:
        return normalize_tss(raw, anchor_context=documentary_context)
    if prop in (Property.CAJA_10, Property.CAJA_35):
        return normalize_box_sequence(raw)
    if prop == Property.FACTOR_SIGMA:
        return normalize_sigma(raw)
    # Fallback for any future property not yet covered: preserve raw.
    return NormalizationResult(value_normalized=raw, derivation_note=None)
