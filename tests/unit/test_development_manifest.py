"""T039 — safe development-case manifest schema and field audit.

Inference unit is paper × promoter. The file has no gold, curator, evaluator,
or property-target columns. The runner (T041) applies the fixed four-property set.
"""
from __future__ import annotations

import dataclasses
import json
import subprocess
from pathlib import Path

import pytest

from promoter_ai_extraction.boundary import BoundaryViolation
from promoter_ai_extraction.manifest import (
    DEVELOPMENT_CASE_ALLOWLIST,
    DevelopmentCase,
    DevelopmentManifest,
    DevelopmentManifestLoader,
    ManifestLoadError,
)

_REPO = Path(__file__).resolve().parents[2]
_FIXTURE = _REPO / "tests" / "fixtures" / "synthetic_safe_manifest.json"


def _valid_case() -> dict[str, object]:
    return {
        "document_path": "papers/PMC12345.txt",
        "document_format": "TXT",
        "paper_id": "PMC12345",
        "promoter_id": None,
        "promoter_name": "lacZp1",
        "paper_gene_synonym": None,
    }


def _write_manifest(path: Path, cases: list[dict[str, object]]) -> Path:
    path.write_text(json.dumps({"cases": cases}), encoding="utf-8")
    return path


def test_valid_synthetic_fixture_loads() -> None:
    result = DevelopmentManifestLoader().load(_FIXTURE)
    assert isinstance(result, DevelopmentManifest)
    assert len(result.cases) == 1
    case = result.cases[0]
    assert isinstance(case, DevelopmentCase)
    assert case.paper_id == "PMC12345"
    assert case.promoter_name == "lacZp1"
    assert not hasattr(case, "property")
    assert not hasattr(result, "gold_path")


def test_loaded_manifest_is_frozen() -> None:
    result = DevelopmentManifestLoader().load(_FIXTURE)
    with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
        result.cases = ()  # type: ignore[misc]


def test_field_audit_contains_only_allowlisted_identities() -> None:
    raw = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    names = DevelopmentManifestLoader.audit_fields(raw)
    assert "cases" in names
    case_fields = names - {"cases"}
    assert case_fields <= DEVELOPMENT_CASE_ALLOWLIST
    for forbidden in (
        "GT_para_referencia",
        "Modalidad_origen",
        "property",
        "gold_path",
        "split",
    ):
        assert forbidden not in names


def test_gold_column_is_rejected(tmp_path: Path) -> None:
    case = _valid_case()
    case["GT_para_referencia"] = "-42"
    path = _write_manifest(tmp_path / "leaky.json", [case])
    with pytest.raises(BoundaryViolation) as exc_info:
        DevelopmentManifestLoader().load(path)
    assert exc_info.value.code == "FORBIDDEN_FIELD"


def test_property_column_is_rejected_on_development_manifest(tmp_path: Path) -> None:
    case = _valid_case()
    case["property"] = "TSS"
    path = _write_manifest(tmp_path / "per-property.json", [case])
    with pytest.raises(BoundaryViolation) as exc_info:
        DevelopmentManifestLoader().load(path)
    assert exc_info.value.code == "UNKNOWN_FIELD"


def test_unknown_column_is_rejected(tmp_path: Path) -> None:
    case = _valid_case()
    case["curator_notes"] = "x"
    path = _write_manifest(tmp_path / "unknown.json", [case])
    with pytest.raises(BoundaryViolation) as exc_info:
        DevelopmentManifestLoader().load(path)
    assert exc_info.value.code == "UNKNOWN_FIELD"


def test_missing_file_is_load_error(tmp_path: Path) -> None:
    missing = tmp_path / "absent.json"
    outcome = DevelopmentManifestLoader().load(missing)
    assert isinstance(outcome, ManifestLoadError)
    assert outcome.code == "FILE_NOT_FOUND"


def test_empty_cases_is_load_error(tmp_path: Path) -> None:
    path = _write_manifest(tmp_path / "empty.json", [])
    outcome = DevelopmentManifestLoader().load(path)
    assert isinstance(outcome, ManifestLoadError)
    assert outcome.code == "EMPTY_MANIFEST"


def test_duplicate_paper_promoter_is_rejected(tmp_path: Path) -> None:
    first = _valid_case()
    second = _valid_case()
    second["document_path"] = "papers/PMC12345-copy.txt"
    second["promoter_id"] = "promoter-2"
    path = _write_manifest(tmp_path / "dup.json", [first, second])
    outcome = DevelopmentManifestLoader().load(path)
    assert isinstance(outcome, ManifestLoadError)
    assert outcome.code == "DUPLICATE_CASE"
    assert "GT_para_referencia" not in outcome.message


def test_same_paper_different_promoters_are_accepted(tmp_path: Path) -> None:
    first = _valid_case()
    second = _valid_case()
    second["promoter_name"] = "lacZp2"
    second["document_path"] = "papers/PMC12345-b.txt"
    path = _write_manifest(tmp_path / "two-promoters.json", [first, second])
    outcome = DevelopmentManifestLoader().load(path)
    assert isinstance(outcome, DevelopmentManifest)
    assert len(outcome.cases) == 2
    assert outcome.cases[0].promoter_name == "lacZp1"
    assert outcome.cases[1].promoter_name == "lacZp2"


def test_real_development_manifest_path_is_gitignored() -> None:
    probe = subprocess.run(
        ["git", "check-ignore", "-q", "02-DOCS/data/safe-development-manifest.json"],
        cwd=_REPO,
        check=False,
    )
    assert probe.returncode == 0


def test_synthetic_manifest_fixture_is_versionable() -> None:
    probe = subprocess.run(
        ["git", "check-ignore", "-q", "tests/fixtures/synthetic_safe_manifest.json"],
        cwd=_REPO,
        check=False,
    )
    assert probe.returncode == 1
    assert _FIXTURE.is_file()
