"""Failing tests for the current-workset GoldParser (T025)."""
from __future__ import annotations

from promoter_ai_extraction.evaluation.gold_loader import GoldRecord
from promoter_ai_extraction.evaluation.gold_parser import (
    PARSE_ERROR_CODE,
    GoldParseError,
    GoldParser,
    ParsedGoldValue,
)
from promoter_ai_extraction.models import Property, ScientificStatus


def _record(
    prop: Property,
    raw: object,
    storage_type: str = "text",
) -> GoldRecord:
    return GoldRecord(
        paper_id="PMC12345",
        promoter_name="lacZp1",
        property=prop,
        gold_value_raw=raw,
        storage_type=storage_type,
        modalidad_origen="texto_explicito",
    )


def test_single_caja10_value() -> None:
    parsed = GoldParser().parse(_record(Property.CAJA_10, "TATAAT"))
    assert isinstance(parsed, ParsedGoldValue)
    assert parsed.gold_value_raw == "TATAAT"
    assert parsed.gold_value_set == frozenset({"TATAAT"})
    assert parsed.raw_tokens == ("TATAAT",)


def test_caja10_literal_plus_delimiter() -> None:
    parsed = GoldParser().parse(_record(Property.CAJA_10, "TATAAT + TTGACA"))
    assert isinstance(parsed, ParsedGoldValue)
    assert parsed.gold_value_raw == "TATAAT + TTGACA"
    assert parsed.gold_value_set == frozenset({"TATAAT", "TTGACA"})
    assert parsed.raw_tokens == ("TATAAT", "TTGACA")


def test_caja10_plus_without_spaces_is_parse_error() -> None:
    parsed = GoldParser().parse(_record(Property.CAJA_10, "TATAAT+TTGACA"))
    assert isinstance(parsed, GoldParseError)
    assert parsed.code == PARSE_ERROR_CODE
    assert parsed.gold_value_raw == "TATAAT+TTGACA"


def test_caja10_three_plus_tokens_is_parse_error() -> None:
    parsed = GoldParser().parse(_record(Property.CAJA_10, "AAA + CCC + GGG"))
    assert isinstance(parsed, GoldParseError)
    assert parsed.code == PARSE_ERROR_CODE


def test_caja35_internal_newline_is_one_sequence() -> None:
    raw = "TT\nGTTA"
    parsed = GoldParser().parse(_record(Property.CAJA_35, raw))
    assert isinstance(parsed, ParsedGoldValue)
    assert parsed.gold_value_raw == raw
    assert parsed.raw_tokens == (raw,)
    assert parsed.gold_value_set == frozenset({"TTGTTA"})


def test_tss_negative_integer_text() -> None:
    parsed = GoldParser().parse(_record(Property.TSS, "-42"))
    assert isinstance(parsed, ParsedGoldValue)
    assert parsed.gold_value_raw == "-42"
    assert parsed.gold_value_set == frozenset({"-42"})


def test_tss_does_not_split_on_minus() -> None:
    parsed = GoldParser().parse(_record(Property.TSS, "-145"))
    assert isinstance(parsed, ParsedGoldValue)
    assert parsed.gold_value_set == frozenset({"-145"})


def test_tss_numeric_cell() -> None:
    parsed = GoldParser().parse(_record(Property.TSS, -42, storage_type="numeric"))
    assert isinstance(parsed, ParsedGoldValue)
    assert parsed.gold_value_raw == -42
    assert parsed.storage_type == "numeric"
    assert parsed.gold_value_set == frozenset({"-42"})


def test_tss_phrase_is_parse_error() -> None:
    parsed = GoldParser().parse(_record(Property.TSS, "42 bp upstream of the ATG"))
    assert isinstance(parsed, GoldParseError)
    assert parsed.code == PARSE_ERROR_CODE


def test_sigma_typographic_normalization() -> None:
    parsed = GoldParser().parse(_record(Property.FACTOR_SIGMA, "Sigma70"))
    assert isinstance(parsed, ParsedGoldValue)
    assert parsed.gold_value_raw == "Sigma70"
    assert parsed.gold_value_set == frozenset({"sigma70"})


def test_sigma_does_not_apply_rpo_equivalence() -> None:
    parsed = GoldParser().parse(_record(Property.FACTOR_SIGMA, "RpoS"))
    assert isinstance(parsed, ParsedGoldValue)
    assert "sigma38" not in parsed.gold_value_set
    assert "sigmaS" not in parsed.gold_value_set
    assert parsed.gold_value_set == frozenset({"RpoS"})


def test_deduplicates_after_normalization_and_keeps_raw_provenance() -> None:
    parsed = GoldParser().parse(_record(Property.CAJA_10, "tat aat + TATAAT"))
    assert isinstance(parsed, ParsedGoldValue)
    assert parsed.gold_value_set == frozenset({"TATAAT"})
    assert parsed.raw_tokens == ("tat aat", "TATAAT")
    assert parsed.provenance == (("tat aat", "TATAAT"), ("TATAAT", "TATAAT"))


def test_unknown_comma_syntax_is_parse_error() -> None:
    parsed = GoldParser().parse(_record(Property.CAJA_10, "TATAAT, TTGACA"))
    assert isinstance(parsed, GoldParseError)
    assert parsed.code == PARSE_ERROR_CODE
    assert parsed.gold_value_raw == "TATAAT, TTGACA"


def test_empty_cell_is_non_positive_not_scientific() -> None:
    parsed = GoldParser().parse(_record(Property.TSS, None))
    assert isinstance(parsed, GoldParseError)
    assert parsed.code == "NON_POSITIVE"
    assert parsed.code not in {status.value for status in ScientificStatus}


def test_parse_error_code_is_not_scientific() -> None:
    assert PARSE_ERROR_CODE not in {status.value for status in ScientificStatus}
