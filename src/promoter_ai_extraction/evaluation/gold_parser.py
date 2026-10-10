"""Current-workset gold parser (T026).

Tokenizes only observed encodings from SUBSET_GOLD.xlsx clarification.
Does not match or score. Unknown syntax fails closed.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from promoter_ai_extraction.evaluation.gold_loader import GoldRecord
from promoter_ai_extraction.models import Property, ScientificStatus
from promoter_ai_extraction.normalization import normalize_for_property

__all__ = [
    "PARSE_ERROR_CODE",
    "PARSER_VERSION",
    "GoldParseError",
    "GoldParser",
    "ParsedGoldValue",
]

PARSE_ERROR_CODE = "PARSE_ERROR / NEEDS_REVIEW"
PARSER_VERSION = "current-workset-v1"
_CAJA10_DELIMITER = " + "
_INTEGER_RE = re.compile(r"^[+-]?\d+$")
_NUCLEOTIDE_BODY_RE = re.compile(r"^[ACGTU]+$", re.IGNORECASE)
_NON_POSITIVE_MARKERS = frozenset(
    {
        "",
        "na",
        "n/a",
        "ausente_en_este_paper",
        "inferido_no_dato",
    }
)
_SCIENTIFIC_CODES = frozenset(status.value for status in ScientificStatus)


@dataclass(frozen=True, slots=True)
class ParsedGoldValue:
    gold_value_raw: object
    storage_type: str
    raw_tokens: tuple[str, ...]
    gold_value_set: frozenset[str]
    provenance: tuple[tuple[str, str], ...]
    parser_version: str = PARSER_VERSION


@dataclass(frozen=True, slots=True)
class GoldParseError:
    gold_value_raw: object
    code: str
    message: str

    def __post_init__(self) -> None:
        if self.code in _SCIENTIFIC_CODES:
            raise ValueError(
                "GoldParseError.code must not equal a ScientificStatus value."
            )


class GoldParser:
    """Deterministic current-workset tokenizer + permitted normalization."""

    def parse(self, record: GoldRecord) -> ParsedGoldValue | GoldParseError:
        if _is_non_positive(record.gold_value_raw):
            return GoldParseError(
                gold_value_raw=record.gold_value_raw,
                code="NON_POSITIVE",
                message="The gold cell is empty or a non-positive marker.",
            )
        tokens = _tokenize(record)
        if tokens is None:
            return GoldParseError(
                gold_value_raw=record.gold_value_raw,
                code=PARSE_ERROR_CODE,
                message="Gold cell syntax is outside the current-workset grammar.",
            )
        provenance: list[tuple[str, str]] = []
        normalized_values: list[str] = []
        for token in tokens:
            normalized = normalize_for_property(record.property, token).value_normalized
            provenance.append((token, normalized))
            if normalized not in normalized_values:
                normalized_values.append(normalized)
        return ParsedGoldValue(
            gold_value_raw=record.gold_value_raw,
            storage_type=record.storage_type,
            raw_tokens=tokens,
            gold_value_set=frozenset(normalized_values),
            provenance=tuple(provenance),
        )


def _is_non_positive(raw: object) -> bool:
    if raw is None:
        return True
    if isinstance(raw, str) and raw.strip().lower() in _NON_POSITIVE_MARKERS:
        return True
    return False


def _tokenize(record: GoldRecord) -> tuple[str, ...] | None:
    if record.property is Property.CAJA_10:
        return _tokenize_caja10(record.gold_value_raw)
    if record.property is Property.CAJA_35:
        return _tokenize_caja35(record.gold_value_raw)
    if record.property is Property.TSS:
        return _tokenize_tss(record.gold_value_raw)
    if record.property is Property.FACTOR_SIGMA:
        return _tokenize_sigma(record.gold_value_raw)
    return None


def _tokenize_caja10(raw: object) -> tuple[str, ...] | None:
    if not isinstance(raw, str):
        return None
    if _CAJA10_DELIMITER in raw:
        parts = raw.split(_CAJA10_DELIMITER)
        if len(parts) != 2:
            return None
        left, right = (part.strip() for part in parts)
        if _is_nucleotide_token(left) and _is_nucleotide_token(right):
            return (left, right)
        return None
    if _is_nucleotide_token(raw):
        return (raw,)
    return None


def _tokenize_caja35(raw: object) -> tuple[str, ...] | None:
    if not isinstance(raw, str):
        return None
    if _CAJA10_DELIMITER in raw or "," in raw or ";" in raw or "/" in raw or "|" in raw:
        return None
    if _is_nucleotide_token(raw):
        return (raw,)
    return None


def _tokenize_tss(raw: object) -> tuple[str, ...] | None:
    if isinstance(raw, bool):
        return None
    if isinstance(raw, int):
        return (str(raw),)
    if isinstance(raw, float):
        if raw.is_integer():
            return (str(int(raw)),)
        return None
    if isinstance(raw, str) and _INTEGER_RE.fullmatch(raw.strip()):
        return (raw.strip(),)
    return None


def _tokenize_sigma(raw: object) -> tuple[str, ...] | None:
    if not isinstance(raw, str):
        return None
    if any(mark in raw for mark in (_CAJA10_DELIMITER, ",", ";", "/", "|")):
        return None
    stripped = raw.strip()
    if not stripped or stripped.lower() in _NON_POSITIVE_MARKERS:
        return None
    return (stripped,)


def _is_nucleotide_token(text: str) -> bool:
    compact = re.sub(r"[\s\-]", "", text)
    return bool(compact) and _NUCLEOTIDE_BODY_RE.fullmatch(compact) is not None
