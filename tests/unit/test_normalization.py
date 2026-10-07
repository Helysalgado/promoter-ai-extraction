"""Failing tests for property-specific pure normalizers (T011).

RED: collection fails because promoter_ai_extraction.normalization does not
exist yet.  After T012 implementation all tests pass (GREEN).

Coverage:
- TSS sign/anchor cases, +1 designation, genomic-coordinate preservation,
  missing-anchor non-conversion (TSS-01…TSS-06).
- Caja uppercase, typographic whitespace/hyphen/line-break removal without
  base correction (BOX-06/BOX-07).
- Sigma typographic normalization without Rpo equivalences (SIG-02/SIG-03).
- Raw input not mutated by any normalizer.
- NormalizationResult is the return type for all normalizers.
- derivation_note is None when no transformation occurred.
- derivation_note is not None when a transformation was applied.
"""
from __future__ import annotations

import pytest

from promoter_ai_extraction.normalization import (
    NormalizationResult,
    normalize_box_sequence,
    normalize_sigma,
    normalize_tss,
)


# ─── TSS normalization ────────────────────────────────────────────────────────


class TestTssNormalization:
    """TSS-specific normalization (extraction-contract §26, TSS-01…TSS-06)."""

    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("-42", "-42"),
            ("-12", "-12"),
            ("+42", "+42"),
            ("0", "0"),
            ("-145", "-145"),
            ("-1", "-1"),
        ],
    )
    def test_signed_integer_returned_unchanged(self, raw: str, expected: str) -> None:
        """Signed integer strings are the normalized form and require no change."""
        result = normalize_tss(raw)
        assert result.value_normalized == expected

    def test_plus_one_designation_preserved(self) -> None:
        """+1 as TSS designation (TSS-05) is preserved — not converted to a
        position relative to the translation start."""
        result = normalize_tss("+1")
        assert result.value_normalized == "+1"

    def test_genomic_coordinate_preserved(self) -> None:
        """Absolute genomic coordinate (TSS-06) is preserved without transformation."""
        result = normalize_tss("1234567")
        assert result.value_normalized == "1234567"

    def test_no_automatic_sign_assignment_without_anchor(self) -> None:
        """TSS-04: a distance without an unambiguous anchor must NOT produce -42.

        The normalizer may not sign-assign a plain distance string.
        """
        result = normalize_tss("42 upstream")
        assert result.value_normalized != "-42"

    @pytest.mark.parametrize(
        "raw",
        [
            "42 bp upstream of the ATG",
            "42 bp upstream of the start codon",
            "42 bp upstream of the translation start",
        ],
    )
    def test_upstream_distance_with_explicit_translation_anchor_is_negative(
        self, raw: str
    ) -> None:
        """TSS-02/TSS-03: an explicit translation-start anchor permits -42."""
        result = normalize_tss(raw)
        assert result.value_normalized == "-42"
        assert result.derivation_note is not None

    def test_downstream_distance_with_explicit_translation_anchor_is_positive(
        self,
    ) -> None:
        """TSS-02/TSS-03: an explicit translation-start anchor permits +42."""
        result = normalize_tss("42 bp downstream of the initiation codon")
        assert result.value_normalized == "+42"
        assert result.derivation_note is not None

    def test_external_anchor_context_can_authorize_sign_derivation(self) -> None:
        """Distributed documentary context may provide the explicit anchor."""
        result = normalize_tss(
            "42 bp upstream",
            anchor_context="measured from the translational start",
        )
        assert result.value_normalized == "-42"

    def test_unrecognized_anchor_does_not_authorize_sign_derivation(self) -> None:
        """An unrelated anchor must not be treated as translation_start."""
        result = normalize_tss("42 bp upstream of the promoter")
        assert result.value_normalized == "42 bp upstream of the promoter"

    def test_raw_string_not_mutated(self) -> None:
        """The input string is unchanged after the call."""
        raw = "-42"
        normalize_tss(raw)
        assert raw == "-42"

    def test_derivation_note_none_for_already_normalized_integer(self) -> None:
        """No transformation → derivation_note is None."""
        result = normalize_tss("-42")
        assert result.derivation_note is None

    def test_result_is_normalization_result(self) -> None:
        """Return type is always NormalizationResult."""
        result = normalize_tss("-42")
        assert isinstance(result, NormalizationResult)

    def test_strip_leading_trailing_whitespace(self) -> None:
        """Leading/trailing whitespace on a signed integer is stripped."""
        result = normalize_tss("  -42  ")
        assert result.value_normalized == "-42"


# ─── Box sequence normalization ───────────────────────────────────────────────


class TestBoxNormalization:
    """Caja -10 and Caja -35 normalization (BOX-06/BOX-07)."""

    def test_lowercase_to_uppercase(self) -> None:
        """BOX-06: lowercase nucleotides are converted to uppercase."""
        result = normalize_box_sequence("tataat")
        assert result.value_normalized == "TATAAT"

    def test_typographic_space_removed(self) -> None:
        """BOX-06: typographic spaces between nucleotides are removed."""
        result = normalize_box_sequence("TAT AAT")
        assert result.value_normalized == "TATAAT"

    def test_typographic_hyphen_removed(self) -> None:
        """BOX-06: typographic hyphens between nucleotides are removed."""
        result = normalize_box_sequence("TAT-AAT")
        assert result.value_normalized == "TATAAT"

    def test_internal_line_break_removed(self) -> None:
        """Typographic line break within a nucleotide sequence is removed (AC-33)."""
        result = normalize_box_sequence("TT\nGTTA")
        assert result.value_normalized == "TTGTTA"

    def test_no_nucleotide_base_correction(self) -> None:
        """BOX-07: nucleotide bases must not be altered (no consensus substitution)."""
        result = normalize_box_sequence("TATAAC")
        assert result.value_normalized == "TATAAC"

    def test_mixed_case_and_spaces(self) -> None:
        """Lowercase and internal spaces combined in one call."""
        result = normalize_box_sequence("tat aat")
        assert result.value_normalized == "TATAAT"

    def test_no_correction_short_sequence(self) -> None:
        """Short sequences are preserved without base correction."""
        result = normalize_box_sequence("gc")
        assert result.value_normalized == "GC"

    def test_raw_string_not_mutated(self) -> None:
        """Input string is unchanged after normalization."""
        raw = "tataat"
        normalize_box_sequence(raw)
        assert raw == "tataat"

    def test_derivation_note_set_when_transformation_applied(self) -> None:
        """derivation_note is not None when any transformation was needed."""
        result = normalize_box_sequence("TAT AAT")
        assert result.derivation_note is not None

    def test_derivation_note_none_when_already_normalized(self) -> None:
        """No transformation → derivation_note is None."""
        result = normalize_box_sequence("TATAAT")
        assert result.derivation_note is None

    def test_result_is_normalization_result(self) -> None:
        """Return type is always NormalizationResult."""
        result = normalize_box_sequence("TATAAT")
        assert isinstance(result, NormalizationResult)

    def test_lowercase_only_has_derivation_note(self) -> None:
        """Lowercase-only input: uppercase transformation sets a derivation note."""
        result = normalize_box_sequence("tataat")
        assert result.derivation_note is not None


# ─── Sigma normalization ──────────────────────────────────────────────────────


class TestSigmaNormalization:
    """Factor sigma normalization (SIG-02/SIG-03)."""

    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("sigma70", "sigma70"),
            ("Sigma70", "sigma70"),
            ("SIGMA70", "sigma70"),
            ("sigma 70", "sigma70"),
            ("Sigma 70", "sigma70"),
            ("sigma32", "sigma32"),
            ("Sigma32", "sigma32"),
            ("sigma 32", "sigma32"),
            ("Sigma 32", "sigma32"),
            ("sigmaF", "sigmaF"),
            ("sigma F", "sigmaF"),
            ("SigmaF", "sigmaF"),
            ("sigma54", "sigma54"),
            ("sigma24", "sigma24"),
            ("sigma28", "sigma28"),
        ],
    )
    def test_typographic_sigma_normalization(self, raw: str, expected: str) -> None:
        """SIG-02: typographic case/space variants normalize to 'sigma<designator>'."""
        result = normalize_sigma(raw)
        assert result.value_normalized == expected

    def test_greek_sigma_symbol_numeric(self) -> None:
        """Greek σ followed by a number → 'sigma<number>'."""
        result = normalize_sigma("σ70")
        assert result.value_normalized == "sigma70"

    def test_greek_sigma_symbol_with_space(self) -> None:
        """Greek σ with space before number → 'sigma<number>' (space removed)."""
        result = normalize_sigma("σ 70")
        assert result.value_normalized == "sigma70"

    def test_no_rpos_to_sigmas_equivalence(self) -> None:
        """SIG-03: RpoS is NOT converted to sigmaS or sigma38."""
        result = normalize_sigma("RpoS")
        assert result.value_normalized not in {"sigmaS", "sigma38", "sigma_s"}

    def test_no_rpoh_to_sigma32_equivalence(self) -> None:
        """SIG-03: RpoH is NOT converted to sigma32."""
        result = normalize_sigma("RpoH")
        assert result.value_normalized != "sigma32"

    def test_no_rpon_to_sigma54_equivalence(self) -> None:
        """SIG-03: RpoN is NOT converted to sigma54."""
        result = normalize_sigma("RpoN")
        assert result.value_normalized != "sigma54"

    def test_raw_string_not_mutated(self) -> None:
        """Input string is unchanged after normalization."""
        raw = "Sigma70"
        normalize_sigma(raw)
        assert raw == "Sigma70"

    def test_result_is_normalization_result(self) -> None:
        """Return type is always NormalizationResult."""
        result = normalize_sigma("sigma70")
        assert isinstance(result, NormalizationResult)

    def test_derivation_note_set_for_case_transformation(self) -> None:
        """derivation_note is not None when case normalization was applied."""
        result = normalize_sigma("Sigma70")
        assert result.derivation_note is not None

    def test_derivation_note_set_for_space_removal(self) -> None:
        """derivation_note is not None when a space was removed."""
        result = normalize_sigma("sigma 70")
        assert result.derivation_note is not None

    def test_derivation_note_set_for_greek_symbol(self) -> None:
        """derivation_note is not None when Greek σ was replaced."""
        result = normalize_sigma("σ70")
        assert result.derivation_note is not None

    def test_derivation_note_none_when_already_normalized(self) -> None:
        """Already-normalized label: derivation_note is None."""
        result = normalize_sigma("sigma70")
        assert result.derivation_note is None

    def test_derivation_note_none_for_sigmaF_already_normalized(self) -> None:
        """sigmaF (already normalized): derivation_note is None."""
        result = normalize_sigma("sigmaF")
        assert result.derivation_note is None
