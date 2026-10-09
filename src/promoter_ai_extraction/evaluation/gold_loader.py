"""Evaluator-only XLSX gold loader (T024).

Opens a workbook only after receiving a verified persisted prediction.
Never constructs an extraction request and never belongs on the extractor path.
"""
from __future__ import annotations

import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException

from promoter_ai_extraction.models import Property, ScientificStatus
from promoter_ai_extraction.persistence import VerifiedPersistedPrediction

__all__ = ["GoldDataset", "GoldLoadError", "GoldLoader", "GoldRecord"]

_REQUIRED_HEADERS = (
    "ID_paper",
    "Nombre_promotor",
    "Propiedad",
    "GT_para_referencia",
)
_HEADER_ROW = 4
_SHEET_NAME = "Hoja1"
_PROPERTY_BY_LABEL = {member.value: member for member in Property}
_SCIENTIFIC_CODES = frozenset(status.value for status in ScientificStatus)
# Floats beyond this magnitude are not exact integers (IEEE-754).
_MAX_EXACT_FLOAT_INT = 2**53


@dataclass(frozen=True, slots=True)
class GoldRecord:
    """Evaluator-only gold row. Not an extraction request."""

    paper_id: str
    promoter_name: str
    property: Property
    gold_value_raw: object
    storage_type: str
    modalidad_origen: str | None


@dataclass(frozen=True, slots=True)
class GoldDataset:
    records: tuple[GoldRecord, ...]


@dataclass(frozen=True, slots=True)
class GoldLoadError:
    stage: str
    code: str
    message: str
    cause: str

    def __post_init__(self) -> None:
        if self.code in _SCIENTIFIC_CODES:
            raise ValueError(
                "GoldLoadError.code must not equal a ScientificStatus value."
            )


def _fail(code: str, message: str, cause: str) -> GoldLoadError:
    return GoldLoadError(
        stage="gold_load",
        code=code,
        message=message,
        cause=cause,
    )


def _paper_id_text(value: object) -> str | None:
    """Return an unambiguous paper-id string, or None when conversion is unsafe.

    Excel numeric cells arrive as ``int`` or as an integer-valued ``float``.
    ``bool`` is rejected because it is an ``int`` subclass. Fractional floats
    and floats outside the exact integer range are rejected. Curator target
    cells are not passed through this function.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not value.is_integer():
            return None
        if abs(value) > _MAX_EXACT_FLOAT_INT:
            return None
        return str(int(value))
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return None


def _storage_type(value: object) -> str:
    if isinstance(value, bool):
        return "text"
    if isinstance(value, (int, float)):
        return "numeric"
    return "text"


class GoldLoader:
    """Read-only gold access gated by verified persistence."""

    def load(self, source: object, gold_path: Path) -> GoldDataset | GoldLoadError:
        if not isinstance(source, VerifiedPersistedPrediction):
            return _fail(
                "MISSING_VERIFIED_PERSISTENCE",
                "Gold access requires a verified persisted prediction. "
                "In-memory extraction runs are not accepted.",
                "TypeError",
            )
        path = Path(gold_path)
        if not path.exists() or not path.is_file():
            return _fail(
                "FILE_NOT_FOUND",
                "The configured gold workbook was not found.",
                "FileNotFoundError",
            )
        try:
            workbook = load_workbook(path, read_only=True, data_only=True)
        except (
            InvalidFileException,
            zipfile.BadZipFile,
            OSError,
            KeyError,
            ValueError,
        ) as exc:
            return _fail(
                "CORRUPT_WORKBOOK",
                "The gold workbook could not be read as XLSX.",
                type(exc).__name__,
            )
        try:
            if _SHEET_NAME not in workbook.sheetnames:
                return _fail(
                    "MISSING_SHEET",
                    "The gold workbook does not contain the required sheet.",
                    "KeyError",
                )
            sheet = workbook[_SHEET_NAME]
            return self._read_sheet(sheet)
        finally:
            workbook.close()

    def _read_sheet(self, sheet: Any) -> GoldDataset | GoldLoadError:
        header_map: dict[str, int] | None = None
        records: list[GoldRecord] = []
        for index, row in enumerate(sheet.iter_rows(values_only=True), start=1):
            if index < _HEADER_ROW:
                continue
            if index == _HEADER_ROW:
                headers = [str(cell).strip() if cell is not None else "" for cell in row]
                if any(required not in headers for required in _REQUIRED_HEADERS):
                    return _fail(
                        "MISSING_HEADERS",
                        "The gold header row is missing required evaluator columns.",
                        "KeyError",
                    )
                header_map = {name: position for position, name in enumerate(headers) if name}
                continue
            assert header_map is not None
            record = self._parse_row(row, header_map)
            if isinstance(record, GoldLoadError):
                return record
            if record is not None:
                records.append(record)
        if header_map is None:
            return _fail(
                "MISSING_HEADERS",
                "The gold workbook has no header row in the expected position.",
                "KeyError",
            )
        return GoldDataset(records=tuple(records))

    def _parse_row(
        self,
        row: tuple[object, ...],
        header_map: dict[str, int],
    ) -> GoldRecord | GoldLoadError | None:
        def cell(name: str) -> object:
            position = header_map.get(name)
            if position is None or position >= len(row):
                return None
            return row[position]

        paper_id = cell("ID_paper")
        promoter_name = cell("Nombre_promotor")
        property_label = cell("Propiedad")
        gold_value = cell("GT_para_referencia")
        if paper_id is None and promoter_name is None and property_label is None:
            return None
        paper_id_text = _paper_id_text(paper_id)
        if paper_id_text is None:
            return _fail(
                "CORRUPT_WORKBOOK",
                "A gold row has a missing or ambiguous ID_paper.",
                "ValueError",
            )
        if not isinstance(promoter_name, str) or not promoter_name.strip():
            return _fail(
                "CORRUPT_WORKBOOK",
                "A gold row is missing Nombre_promotor.",
                "ValueError",
            )
        if not isinstance(property_label, str):
            return _fail("UNKNOWN_PROPERTY", "A gold row has a non-text property label.", "TypeError")
        prop = _PROPERTY_BY_LABEL.get(property_label.strip())
        if prop is None:
            return _fail(
                "UNKNOWN_PROPERTY",
                "A gold row has a property label outside the baseline set.",
                "ValueError",
            )
        modalidad = cell("Modalidad_origen")
        modalidad_text = (
            modalidad.strip()
            if isinstance(modalidad, str) and modalidad.strip()
            else None
        )
        return GoldRecord(
            paper_id=paper_id_text,
            promoter_name=promoter_name.strip(),
            property=prop,
            gold_value_raw=gold_value,
            storage_type=_storage_type(gold_value),
            modalidad_origen=modalidad_text,
        )
