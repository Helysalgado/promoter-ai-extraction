"""Boundary tests — T009 (RED) / T010 (GREEN).

Scope
-----
* ``ExtractionRequestFactory.create`` with a valid closed-allowlist mapping
  → returns an immutable ``ExtractionRequest``
* Every canonical denylist field (parametrized) → ``BoundaryViolation``
* Unknown keys, nested forbidden keys, renamed evasions → ``BoundaryViolation``
* Case / diacritic / hyphen variants of denylist entries → ``BoundaryViolation``
* Optional fields (promoter_id, paper_gene_synonym) may be None
* Required-field failures: empty paper_id, empty promoter_name, wrong types
* Paper-id / document-id mismatch → ``BoundaryViolation``
* Capture assertion: ExtractionRequest has exactly the six allowlisted fields;
  no gold_path, no metadata bag
* ``SafeCaseManifest`` from a valid manifest mapping → immutable carrier
* Manifest with forbidden/unknown columns → ``BoundaryViolation``
* ``BoundaryViolation`` carries a stable ``code`` attribute; message is safe
  (no private values echoed back)

Design rules enforced here
--------------------------
- Inspect only mapping *keys* — never document text (legitimate papers can
  mention forbidden words; only the field names are the safety boundary).
- Allowlist is CLOSED: any key not in the allowlist is rejected even when it
  is not on the denylist.
- Denylist catches canonical and variant (case/diacritic/hyphen) forms of
  known-bad gold/evaluator/curator fields.
- BoundaryViolation messages must not echo private values passed by the caller.
"""
from __future__ import annotations

import dataclasses
from typing import Any

import pytest

from promoter_ai_extraction.boundary import (
    BoundaryViolation,
    CaseManifestFactory,
    ExtractionRequest,
    ExtractionRequestFactory,
    SafeCaseManifest,
)
from promoter_ai_extraction.documents import DocumentSegment, LoadedDocument
from promoter_ai_extraction.models import Property

# ---------------------------------------------------------------------------
# Shared helpers / fixtures
# ---------------------------------------------------------------------------

_DUMMY_HASH = "a" * 64  # 64-char hex string; real SHA-256 has exactly 64 chars


def _make_loaded_doc(paper_id: str = "PMID001") -> LoadedDocument:
    """Minimal synthetic LoadedDocument — no real papers, no gold data."""
    seg = DocumentSegment(
        segment_id="txt:p:0000",
        text="Sigma-70 promoter study.",
        source_type="body_text",
        location="lines:1-1",
    )
    return LoadedDocument(
        paper_id=paper_id,
        format="TXT",
        segments=(seg,),
        document_hash=_DUMMY_HASH,
    )


def _valid_mapping(doc: LoadedDocument | None = None) -> dict[str, Any]:
    """Mapping that satisfies every allowlist/type constraint."""
    if doc is None:
        doc = _make_loaded_doc()
    return {
        "document": doc,
        "paper_id": doc.paper_id,
        "promoter_id": "pA-01",
        "promoter_name": "pA",
        "paper_gene_synonym": "sigA",
        "property": Property.TSS,
    }


_FACTORY = ExtractionRequestFactory()
_MANIFEST_FACTORY = CaseManifestFactory()


def _valid_manifest_mapping() -> dict[str, Any]:
    """Minimal mapping for SafeCaseManifest creation."""
    return {
        "document_path": "/data/papers/PMID001.xml",
        "document_format": "TEI/XML",
        "paper_id": "PMID001",
        "promoter_id": None,
        "promoter_name": "pA",
        "paper_gene_synonym": None,
        "property": Property.TSS,
    }


# ---------------------------------------------------------------------------
# T009 § Valid path — request creation
# ---------------------------------------------------------------------------


def test_valid_request_succeeds() -> None:
    """A fully compliant mapping creates an ExtractionRequest without error."""
    result = _FACTORY.create(_valid_mapping())
    assert isinstance(result, ExtractionRequest)


def test_valid_request_paper_id_carried() -> None:
    """paper_id from the mapping appears on the returned request."""
    result = _FACTORY.create(_valid_mapping())
    assert result.paper_id == "PMID001"


def test_valid_request_property_carried() -> None:
    """property from the mapping appears on the returned request."""
    result = _FACTORY.create(_valid_mapping())
    assert result.property is Property.TSS


def test_valid_request_optional_fields_carried() -> None:
    """Optional promoter_id and synonym are carried through when supplied."""
    result = _FACTORY.create(_valid_mapping())
    assert result.promoter_id == "pA-01"
    assert result.paper_gene_synonym == "sigA"


# ---------------------------------------------------------------------------
# T009 § Immutability and safe payload (capture assertion, T010 done-check)
# ---------------------------------------------------------------------------


def test_request_is_frozen() -> None:
    """ExtractionRequest must be immutable (frozen dataclass)."""
    result = _FACTORY.create(_valid_mapping())
    with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
        result.paper_id = "MUTATED"  # type: ignore[misc]


def test_request_has_exactly_six_fields() -> None:
    """ExtractionRequest exposes exactly the six allowlisted fields — no extras."""
    expected_names = frozenset(
        {"document", "paper_id", "promoter_id", "promoter_name", "paper_gene_synonym", "property"}
    )
    actual_names = frozenset(f.name for f in dataclasses.fields(ExtractionRequest))
    assert actual_names == expected_names


def test_request_has_no_gold_path_attribute() -> None:
    """ExtractionRequest must not carry a gold_path attribute."""
    result = _FACTORY.create(_valid_mapping())
    assert not hasattr(result, "gold_path")


def test_request_has_no_metadata_bag() -> None:
    """ExtractionRequest must not carry a metadata or extra_fields bag."""
    result = _FACTORY.create(_valid_mapping())
    assert not hasattr(result, "metadata")
    assert not hasattr(result, "extra_fields")
    assert not hasattr(result, "extra")


# ---------------------------------------------------------------------------
# T009 § Closed allowlist — unknown / renamed keys
# ---------------------------------------------------------------------------


def test_unknown_key_raises_boundary_violation() -> None:
    """Any key not in the allowlist must raise BoundaryViolation."""
    mapping = _valid_mapping()
    mapping["unknown_field"] = "something"
    with pytest.raises(BoundaryViolation):
        _FACTORY.create(mapping)


@pytest.mark.parametrize(
    "evasion_key",
    [
        "gold_value",       # alias for a gold reference column
        "expected_value",   # alias for a target column
        "target",           # generic target / ground-truth label
        "curated_reference",  # curator-derived reference
    ],
)
def test_renamed_evasion_rejected(evasion_key: str) -> None:
    """Renamed / aliased forbidden-concept keys are rejected by the closed allowlist."""
    mapping = _valid_mapping()
    mapping[evasion_key] = "synthetic_value"
    with pytest.raises(BoundaryViolation):
        _FACTORY.create(mapping)


# ---------------------------------------------------------------------------
# T009 § Denylist — canonical forbidden fields (one parametrized test)
# ---------------------------------------------------------------------------

#: Canonical gold/curator/evaluator field names that must be rejected.
#: Sources: plan §0 Defensive denylist + spec AC-28/AC-29.
CANONICAL_FORBIDDEN_FIELDS: list[str] = [
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
    # Evaluation labels / outcomes / scores / metrics / TP / FP / FN
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
    "target_value",
    "gold",
    "gold_label",
    "expected",
]


@pytest.mark.parametrize("forbidden_key", CANONICAL_FORBIDDEN_FIELDS)
def test_canonical_forbidden_field_rejected(forbidden_key: str) -> None:
    """Every canonical denylist field raises BoundaryViolation when present."""
    mapping = _valid_mapping()
    mapping[forbidden_key] = "synthetic_value"
    with pytest.raises(BoundaryViolation):
        _FACTORY.create(mapping)


# ---------------------------------------------------------------------------
# T009 § Denylist — key normalization (variants must still be rejected)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "variant_key",
    [
        "valor_regulondb",          # lowercase of Valor_RegulonDB
        "VALOR_REGULONDB",          # uppercase of Valor_RegulonDB
        "valor_RegulonDB",          # mixed case
        "Ano_confirmado",           # diacritic-stripped variant of Año_confirmado
        "ano_confirmado",           # fully lowercased diacritic-stripped variant
        "Tecnica_confirmada_manualmente",   # accent-stripped Técnica...
        "GT-para-referencia",       # hyphen instead of underscores
        "gt-para-referencia",       # lowercase + hyphen variant
        "sin dato en regulondb",    # spaces instead of underscores
    ],
)
def test_key_variant_rejected(variant_key: str) -> None:
    """Case / diacritic / separator variants of canonical denylist keys are rejected."""
    mapping = _valid_mapping()
    mapping[variant_key] = "synthetic_value"
    with pytest.raises(BoundaryViolation):
        _FACTORY.create(mapping)


# ---------------------------------------------------------------------------
# T009 § Recursive inspection — nested forbidden keys in nested dicts
# ---------------------------------------------------------------------------


def test_nested_forbidden_key_rejected() -> None:
    """A forbidden key inside a nested dict value is caught by recursive inspection."""
    doc = _make_loaded_doc()
    mapping: dict[str, Any] = {
        "document": doc,
        "paper_id": doc.paper_id,
        "promoter_name": "pA",
        "property": Property.TSS,
        # nested dict — contains a forbidden evaluator field
        "extra_context": {"GT_para_referencia": "TATAAT"},
    }
    with pytest.raises(BoundaryViolation):
        _FACTORY.create(mapping)


def test_deeply_nested_forbidden_key_rejected() -> None:
    """Forbidden key two levels deep is also rejected."""
    doc = _make_loaded_doc()
    mapping: dict[str, Any] = {
        "document": doc,
        "paper_id": doc.paper_id,
        "promoter_name": "pA",
        "property": Property.TSS,
        "wrapper": {"inner": {"Valor_RegulonDB": "GCACTTT"}},
    }
    with pytest.raises(BoundaryViolation):
        _FACTORY.create(mapping)


# ---------------------------------------------------------------------------
# T009 § Optional fields
# ---------------------------------------------------------------------------


def test_promoter_id_may_be_none() -> None:
    """promoter_id=None is a valid request (optional field)."""
    mapping = _valid_mapping()
    mapping["promoter_id"] = None
    result = _FACTORY.create(mapping)
    assert result.promoter_id is None


def test_paper_gene_synonym_may_be_none() -> None:
    """paper_gene_synonym=None is a valid request (optional field)."""
    mapping = _valid_mapping()
    mapping["paper_gene_synonym"] = None
    result = _FACTORY.create(mapping)
    assert result.paper_gene_synonym is None


def test_request_without_optional_fields() -> None:
    """Mapping with only the four required fields is valid."""
    doc = _make_loaded_doc()
    mapping: dict[str, Any] = {
        "document": doc,
        "paper_id": doc.paper_id,
        "promoter_name": "pA",
        "property": Property.CAJA_10,
    }
    result = _FACTORY.create(mapping)
    assert result.promoter_id is None
    assert result.paper_gene_synonym is None


# ---------------------------------------------------------------------------
# T009 § Required-field validation
# ---------------------------------------------------------------------------


def test_empty_paper_id_rejected() -> None:
    """paper_id='' must raise BoundaryViolation."""
    mapping = _valid_mapping()
    mapping["paper_id"] = ""
    with pytest.raises(BoundaryViolation):
        _FACTORY.create(mapping)


def test_whitespace_only_paper_id_rejected() -> None:
    """paper_id with only whitespace must raise BoundaryViolation."""
    mapping = _valid_mapping()
    mapping["paper_id"] = "   "
    with pytest.raises(BoundaryViolation):
        _FACTORY.create(mapping)


def test_empty_promoter_name_rejected() -> None:
    """promoter_name='' must raise BoundaryViolation."""
    mapping = _valid_mapping()
    mapping["promoter_name"] = ""
    with pytest.raises(BoundaryViolation):
        _FACTORY.create(mapping)


def test_wrong_type_for_document_rejected() -> None:
    """Passing a plain string as 'document' must raise BoundaryViolation."""
    mapping = _valid_mapping()
    mapping["document"] = "not_a_loaded_document"
    with pytest.raises(BoundaryViolation):
        _FACTORY.create(mapping)


def test_wrong_type_for_property_rejected() -> None:
    """Passing a raw string as 'property' (not a Property enum) must raise BoundaryViolation."""
    mapping = _valid_mapping()
    mapping["property"] = "TSS"   # str, not Property enum
    with pytest.raises(BoundaryViolation):
        _FACTORY.create(mapping)


def test_paper_id_mismatch_with_document_rejected() -> None:
    """paper_id that differs from document.paper_id must raise BoundaryViolation."""
    doc = _make_loaded_doc("PMID001")
    mapping = _valid_mapping(doc)
    mapping["paper_id"] = "PMID999"   # mismatches doc.paper_id == "PMID001"
    with pytest.raises(BoundaryViolation):
        _FACTORY.create(mapping)


# ---------------------------------------------------------------------------
# T009 § BoundaryViolation contract
# ---------------------------------------------------------------------------


def test_boundary_violation_has_code_attribute() -> None:
    """BoundaryViolation must expose a stable string 'code' attribute."""
    exc = BoundaryViolation(code="TEST_CODE", message="test message")
    assert exc.code == "TEST_CODE"


def test_boundary_violation_is_exception() -> None:
    """BoundaryViolation must be raiseable as a Python exception."""
    with pytest.raises(BoundaryViolation):
        raise BoundaryViolation(code="X", message="test")


def test_boundary_violation_message_does_not_echo_private_value() -> None:
    """When a forbidden field is rejected, the message must NOT include the
    field's value — values may be private (gold, curator data)."""
    private_value = "SUPER_SECRET_GOLD_DATA_12345"
    mapping = _valid_mapping()
    mapping["GT_para_referencia"] = private_value
    with pytest.raises(BoundaryViolation) as exc_info:
        _FACTORY.create(mapping)
    assert private_value not in str(exc_info.value)


def test_boundary_violation_message_does_not_echo_forbidden_key_value() -> None:
    """When an unknown key is rejected, the message must NOT include the
    supplied value."""
    secret_value = "TOP_SECRET_42"
    mapping = _valid_mapping()
    mapping["unknown_key"] = secret_value
    with pytest.raises(BoundaryViolation) as exc_info:
        _FACTORY.create(mapping)
    assert secret_value not in str(exc_info.value)


# ---------------------------------------------------------------------------
# T009 § SafeCaseManifest — valid path
# ---------------------------------------------------------------------------


def test_valid_manifest_succeeds() -> None:
    """A fully compliant manifest mapping creates a SafeCaseManifest."""
    result = _MANIFEST_FACTORY.from_mapping(_valid_manifest_mapping())
    assert isinstance(result, SafeCaseManifest)


def test_manifest_paper_id_carried() -> None:
    """paper_id is preserved on the SafeCaseManifest."""
    result = _MANIFEST_FACTORY.from_mapping(_valid_manifest_mapping())
    assert result.paper_id == "PMID001"


def test_manifest_is_frozen() -> None:
    """SafeCaseManifest must be immutable (frozen dataclass)."""
    result = _MANIFEST_FACTORY.from_mapping(_valid_manifest_mapping())
    with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
        result.paper_id = "MUTATED"  # type: ignore[misc]


def test_manifest_optional_fields_may_be_none() -> None:
    """promoter_id and paper_gene_synonym may be None in a manifest."""
    mapping = _valid_manifest_mapping()
    assert mapping["promoter_id"] is None
    assert mapping["paper_gene_synonym"] is None
    result = _MANIFEST_FACTORY.from_mapping(mapping)
    assert result.promoter_id is None
    assert result.paper_gene_synonym is None


def test_manifest_has_no_gold_path_attribute() -> None:
    """SafeCaseManifest must not expose gold_path or evaluation metadata."""
    result = _MANIFEST_FACTORY.from_mapping(_valid_manifest_mapping())
    assert not hasattr(result, "gold_path")
    assert not hasattr(result, "metadata")


# ---------------------------------------------------------------------------
# T009 § SafeCaseManifest — forbidden / unknown column rejection
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "forbidden_col",
    [
        "GT_para_referencia",
        "Valor_RegulonDB",
        "Modalidad_origen",
        "Fila_origen",
        "split",
        "TP",
        "ground_truth",
        "expected_value",
    ],
)
def test_manifest_forbidden_column_rejected(forbidden_col: str) -> None:
    """Forbidden evaluator/gold/curator columns must raise BoundaryViolation."""
    mapping = _valid_manifest_mapping()
    mapping[forbidden_col] = "synthetic"
    with pytest.raises(BoundaryViolation):
        _MANIFEST_FACTORY.from_mapping(mapping)


def test_manifest_unknown_column_rejected() -> None:
    """Any column not in the manifest allowlist must raise BoundaryViolation."""
    mapping = _valid_manifest_mapping()
    mapping["arbitrary_extra"] = "leaks_gold"
    with pytest.raises(BoundaryViolation):
        _MANIFEST_FACTORY.from_mapping(mapping)


def test_manifest_empty_paper_id_rejected() -> None:
    """Manifest with empty paper_id must raise BoundaryViolation."""
    mapping = _valid_manifest_mapping()
    mapping["paper_id"] = ""
    with pytest.raises(BoundaryViolation):
        _MANIFEST_FACTORY.from_mapping(mapping)


def test_manifest_wrong_document_format_rejected() -> None:
    """Manifest with unsupported document_format must raise BoundaryViolation."""
    mapping = _valid_manifest_mapping()
    mapping["document_format"] = "PDF"  # only TXT and TEI/XML are accepted
    with pytest.raises(BoundaryViolation):
        _MANIFEST_FACTORY.from_mapping(mapping)


# ---------------------------------------------------------------------------
# Gap-1 corrections: document_format with wrong type must raise
# BoundaryViolation(INVALID_FIELD_TYPE), not a raw TypeError
# ---------------------------------------------------------------------------


def test_manifest_document_format_list_raises_invalid_field_type() -> None:
    """document_format supplied as a list (unhashable) must raise
    BoundaryViolation with code INVALID_FIELD_TYPE — never a raw TypeError."""
    mapping = _valid_manifest_mapping()
    mapping["document_format"] = ["TXT"]
    with pytest.raises(BoundaryViolation) as exc_info:
        _MANIFEST_FACTORY.from_mapping(mapping)
    assert exc_info.value.code == "INVALID_FIELD_TYPE"


def test_manifest_document_format_int_raises_invalid_field_type() -> None:
    """document_format supplied as an int must raise BoundaryViolation
    INVALID_FIELD_TYPE, not INVALID_FIELD_VALUE (int is wrong type, not just
    wrong value)."""
    mapping = _valid_manifest_mapping()
    mapping["document_format"] = 42
    with pytest.raises(BoundaryViolation) as exc_info:
        _MANIFEST_FACTORY.from_mapping(mapping)
    assert exc_info.value.code == "INVALID_FIELD_TYPE"


def test_manifest_document_format_wrong_type_message_safe() -> None:
    """BoundaryViolation for wrong document_format type must not echo the
    caller-supplied value (it may encode private intent)."""
    secret_payload = ["TXT", "SECRET_42"]
    mapping = _valid_manifest_mapping()
    mapping["document_format"] = secret_payload
    with pytest.raises(BoundaryViolation) as exc_info:
        _MANIFEST_FACTORY.from_mapping(mapping)
    assert "SECRET_42" not in str(exc_info.value)


# ---------------------------------------------------------------------------
# Gap-2 corrections: document_path empty / whitespace must raise
# BoundaryViolation(INVALID_FIELD_VALUE), not silently become Path('.')
# ---------------------------------------------------------------------------


def test_manifest_empty_document_path_raises_invalid_field_value() -> None:
    """document_path='' must raise BoundaryViolation INVALID_FIELD_VALUE.
    Path('') silently becomes Path('.') — that must not happen."""
    mapping = _valid_manifest_mapping()
    mapping["document_path"] = ""
    with pytest.raises(BoundaryViolation) as exc_info:
        _MANIFEST_FACTORY.from_mapping(mapping)
    assert exc_info.value.code == "INVALID_FIELD_VALUE"


def test_manifest_whitespace_document_path_raises_invalid_field_value() -> None:
    """document_path='   ' (whitespace only) must raise BoundaryViolation
    INVALID_FIELD_VALUE."""
    mapping = _valid_manifest_mapping()
    mapping["document_path"] = "   "
    with pytest.raises(BoundaryViolation) as exc_info:
        _MANIFEST_FACTORY.from_mapping(mapping)
    assert exc_info.value.code == "INVALID_FIELD_VALUE"


def test_manifest_empty_path_message_safe() -> None:
    """BoundaryViolation for empty document_path must not echo the empty string."""
    mapping = _valid_manifest_mapping()
    mapping["document_path"] = ""
    with pytest.raises(BoundaryViolation) as exc_info:
        _MANIFEST_FACTORY.from_mapping(mapping)
    # The message should describe the constraint, not repeat the supplied value.
    assert exc_info.value.message  # non-empty message


# ---------------------------------------------------------------------------
# Gap-3 corrections: optional promoter_id / paper_gene_synonym, when supplied
# as strings, must be non-empty after strip — cover both request and manifest
# ---------------------------------------------------------------------------


def test_request_whitespace_promoter_id_rejected() -> None:
    """promoter_id='   ' (whitespace only) must raise BoundaryViolation.
    None is allowed; a non-empty string is allowed; whitespace-only is not."""
    mapping = _valid_mapping()
    mapping["promoter_id"] = "   "
    with pytest.raises(BoundaryViolation):
        _FACTORY.create(mapping)


def test_request_empty_promoter_id_rejected() -> None:
    """promoter_id='' must raise BoundaryViolation."""
    mapping = _valid_mapping()
    mapping["promoter_id"] = ""
    with pytest.raises(BoundaryViolation):
        _FACTORY.create(mapping)


def test_request_whitespace_synonym_rejected() -> None:
    """paper_gene_synonym='   ' (whitespace only) must raise BoundaryViolation."""
    mapping = _valid_mapping()
    mapping["paper_gene_synonym"] = "   "
    with pytest.raises(BoundaryViolation):
        _FACTORY.create(mapping)


def test_request_empty_synonym_rejected() -> None:
    """paper_gene_synonym='' must raise BoundaryViolation."""
    mapping = _valid_mapping()
    mapping["paper_gene_synonym"] = ""
    with pytest.raises(BoundaryViolation):
        _FACTORY.create(mapping)


def test_manifest_whitespace_promoter_id_rejected() -> None:
    """promoter_id='   ' in a manifest must raise BoundaryViolation."""
    mapping = _valid_manifest_mapping()
    mapping["promoter_id"] = "   "
    with pytest.raises(BoundaryViolation):
        _MANIFEST_FACTORY.from_mapping(mapping)


def test_manifest_empty_promoter_id_rejected() -> None:
    """promoter_id='' in a manifest must raise BoundaryViolation."""
    mapping = _valid_manifest_mapping()
    mapping["promoter_id"] = ""
    with pytest.raises(BoundaryViolation):
        _MANIFEST_FACTORY.from_mapping(mapping)


def test_manifest_whitespace_synonym_rejected() -> None:
    """paper_gene_synonym='   ' in a manifest must raise BoundaryViolation."""
    mapping = _valid_manifest_mapping()
    mapping["paper_gene_synonym"] = "   "
    with pytest.raises(BoundaryViolation):
        _MANIFEST_FACTORY.from_mapping(mapping)


def test_manifest_empty_synonym_rejected() -> None:
    """paper_gene_synonym='' in a manifest must raise BoundaryViolation."""
    mapping = _valid_manifest_mapping()
    mapping["paper_gene_synonym"] = ""
    with pytest.raises(BoundaryViolation):
        _MANIFEST_FACTORY.from_mapping(mapping)


# ---------------------------------------------------------------------------
# Gap-4 corrections: BoundaryViolation messages must not echo caller values
# (these cover the newly validated optional fields and document_path)
# ---------------------------------------------------------------------------


def test_whitespace_promoter_id_message_safe() -> None:
    """BoundaryViolation for whitespace promoter_id must not echo the value."""
    private_ws = "\t  \t"
    mapping = _valid_mapping()
    mapping["promoter_id"] = private_ws
    with pytest.raises(BoundaryViolation) as exc_info:
        _FACTORY.create(mapping)
    assert private_ws not in str(exc_info.value)


def test_whitespace_synonym_message_safe() -> None:
    """BoundaryViolation for whitespace synonym must not echo the value."""
    private_ws = "   "
    mapping = _valid_mapping()
    mapping["paper_gene_synonym"] = private_ws
    with pytest.raises(BoundaryViolation) as exc_info:
        _FACTORY.create(mapping)
    assert private_ws not in str(exc_info.value)


# ---------------------------------------------------------------------------
# Finding #4: denylist must traverse list / tuple / set / frozenset containers
# — inspecting mapping keys only, never scalar text.
# These tests are RED until _check_forbidden_keys recurses into sequences.
# ---------------------------------------------------------------------------


def test_forbidden_key_in_list_value_rejected() -> None:
    """A Mapping with a forbidden key embedded inside a list value must be rejected
    with BoundaryViolation(FORBIDDEN_FIELD)."""
    doc = _make_loaded_doc()
    mapping: dict[str, Any] = {
        "document": doc,
        "paper_id": doc.paper_id,
        "promoter_name": "pA",
        "property": Property.TSS,
        "annotations": [{"GT_para_referencia": "TATAAT"}],
    }
    with pytest.raises(BoundaryViolation) as exc_info:
        _FACTORY.create(mapping)
    assert exc_info.value.code == "FORBIDDEN_FIELD"


def test_forbidden_key_in_tuple_value_rejected() -> None:
    """Forbidden key inside a tuple container → BoundaryViolation(FORBIDDEN_FIELD)."""
    doc = _make_loaded_doc()
    mapping: dict[str, Any] = {
        "document": doc,
        "paper_id": doc.paper_id,
        "promoter_name": "pA",
        "property": Property.TSS,
        "rows": ({"Valor_RegulonDB": "GCACTTT"},),
    }
    with pytest.raises(BoundaryViolation) as exc_info:
        _FACTORY.create(mapping)
    assert exc_info.value.code == "FORBIDDEN_FIELD"


def test_forbidden_key_in_nested_list_inside_mapping_rejected() -> None:
    """Forbidden key two containers deep (mapping → list → mapping) → FORBIDDEN_FIELD."""
    doc = _make_loaded_doc()
    mapping: dict[str, Any] = {
        "document": doc,
        "paper_id": doc.paper_id,
        "promoter_name": "pA",
        "property": Property.TSS,
        "outer": {"inner_list": [{"Fila_origen": "row42"}]},
    }
    with pytest.raises(BoundaryViolation) as exc_info:
        _FACTORY.create(mapping)
    assert exc_info.value.code == "FORBIDDEN_FIELD"


def test_clean_list_value_passes_denylist() -> None:
    """A list value with no forbidden keys must NOT raise BoundaryViolation."""
    doc = _make_loaded_doc()
    # This mapping has an unknown key, which should raise UNKNOWN_FIELD
    # (not FORBIDDEN_FIELD); verify the list itself is not the problem.
    mapping: dict[str, Any] = {
        "document": doc,
        "paper_id": doc.paper_id,
        "promoter_name": "pA",
        "property": Property.TSS,
        "safe_list": [{"safe_key": "safe_value"}],
    }
    with pytest.raises(BoundaryViolation) as exc_info:
        _FACTORY.create(mapping)
    # Should be UNKNOWN_FIELD (for "safe_list"), not FORBIDDEN_FIELD
    assert exc_info.value.code == "UNKNOWN_FIELD"


# ---------------------------------------------------------------------------
# Finding #5: normalize repeated / mixed separators → single underscore.
# GT__para__referencia must still match GT_para_referencia in the denylist.
# These tests are RED until _normalize_key collapses repeated underscores.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "variant_key",
    [
        "GT__para__referencia",          # double underscore
        "GT___para___referencia",        # triple underscore
        "GT_-para_-referencia",          # mixed hyphen+underscore
        "GT - para - referencia",        # spaces around hyphens
        "Valor__RegulonDB",              # double underscore in canonical field
        "Sin__dato__en__RegulonDB",      # repeated separators
    ],
)
def test_repeated_separator_variant_rejected(variant_key: str) -> None:
    """Repeated or mixed separators must normalize to a single underscore so the
    denylist still catches the field — BoundaryViolation(FORBIDDEN_FIELD)."""
    mapping = _valid_mapping()
    mapping[variant_key] = "synthetic_value"
    with pytest.raises(BoundaryViolation) as exc_info:
        _FACTORY.create(mapping)
    assert exc_info.value.code == "FORBIDDEN_FIELD"
