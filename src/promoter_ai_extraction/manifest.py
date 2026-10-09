"""Development-case manifest file loader (T039).

Loads a JSON file of paper × promoter cases. Does not open gold, papers, or
evaluator files. The real local manifest and papers stay under git-ignored
``02-DOCS/data/`` / ``data/``; tests use a synthetic fixture.
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from promoter_ai_extraction.boundary import (
    DEVELOPMENT_CASE_ALLOWLIST,
    DevelopmentCase,
    DevelopmentCaseFactory,
    _check_allowlist,
    _check_forbidden_keys,
)

__all__ = [
    "DEVELOPMENT_CASE_ALLOWLIST",
    "DevelopmentCase",
    "DevelopmentManifest",
    "DevelopmentManifestLoader",
    "ManifestLoadError",
]

_FILE_ALLOWLIST: frozenset[str] = frozenset({"cases"})


@dataclass(frozen=True, slots=True)
class ManifestLoadError:
    """Technical failure while reading a development manifest file."""

    code: str
    message: str


@dataclass(frozen=True, slots=True)
class DevelopmentManifest:
    """Immutable list of leakage-safe development cases (paper × promoter)."""

    cases: tuple[DevelopmentCase, ...]


class DevelopmentManifestLoader:
    """Validate and load a JSON development-case manifest."""

    def __init__(self) -> None:
        self._rows = DevelopmentCaseFactory()

    @staticmethod
    def audit_fields(raw: Mapping[str, Any]) -> frozenset[str]:
        names: set[str] = set(raw.keys())
        cases = raw.get("cases")
        if isinstance(cases, list):
            for item in cases:
                if isinstance(item, Mapping):
                    names.update(str(key) for key in item.keys())
        return frozenset(names)

    def load(self, path: Path) -> DevelopmentManifest | ManifestLoadError:
        if not path.is_file():
            return ManifestLoadError(
                code="FILE_NOT_FOUND",
                message="The development manifest file was not found.",
            )
        try:
            raw_text = path.read_text(encoding="utf-8")
            parsed: object = json.loads(raw_text)
        except json.JSONDecodeError:
            return ManifestLoadError(
                code="INVALID_JSON",
                message="The development manifest is not valid JSON.",
            )
        except OSError:
            return ManifestLoadError(
                code="READ_ERROR",
                message="The development manifest could not be read.",
            )
        if not isinstance(parsed, dict):
            return ManifestLoadError(
                code="INVALID_MANIFEST",
                message="The development manifest must be a JSON object with a cases list.",
            )
        return self._from_mapping(parsed)

    def _from_mapping(self, mapping: Mapping[str, Any]) -> DevelopmentManifest | ManifestLoadError:
        _check_forbidden_keys(mapping)
        _check_allowlist(mapping, _FILE_ALLOWLIST, context="manifest")
        cases = mapping.get("cases")
        if not isinstance(cases, list):
            return ManifestLoadError(
                code="INVALID_MANIFEST",
                message="The development manifest 'cases' field must be a list.",
            )
        if not cases:
            return ManifestLoadError(
                code="EMPTY_MANIFEST",
                message="The development manifest contains no cases.",
            )
        loaded: list[DevelopmentCase] = []
        seen: set[tuple[str, str]] = set()
        for item in cases:
            if not isinstance(item, Mapping):
                return ManifestLoadError(
                    code="INVALID_MANIFEST",
                    message="Each development manifest case must be a JSON object.",
                )
            case = self._rows.from_mapping(item)
            identity = (case.paper_id, case.promoter_name)
            if identity in seen:
                return ManifestLoadError(
                    code="DUPLICATE_CASE",
                    message=(
                        "The development manifest contains duplicate "
                        "paper × promoter cases."
                    ),
                )
            seen.add(identity)
            loaded.append(case)
        return DevelopmentManifest(cases=tuple(loaded))
