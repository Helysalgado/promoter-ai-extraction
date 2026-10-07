"""RED tests for PredictionStore atomic write, immutability, and hash verification (T021).

Behavioral contracts exercised:
- save() → PersistedPredictionRef (type and field validity).
- PersistedPredictionRef is frozen/immutable after creation.
- VerifiedPersistedPrediction is frozen/immutable after creation.
- Atomic write: file is present only after save() returns.
- No-overwrite: saving a second run with the same run_id returns
  PersistenceFailure (code FILE_EXISTS), file unchanged.
- load_verified() returns VerifiedPersistedPrediction whose run equals
  the original ExtractionRun.
- load_verified() reconstructs optional metadata (created_at, document_hash,
  system_fingerprint).
- Content hash in ref matches sha256 of actual file bytes.
- Corrupted file (byte flip) causes load_verified() to return
  PersistenceFailure (code HASH_MISMATCH).
- Missing file causes load_verified() to return PersistenceFailure
  (code FILE_NOT_FOUND).
- Incomplete/malformed JSON record causes load_verified() to return
  PersistenceFailure (code CORRUPT_RECORD).
- Wrong schema_version in file causes load_verified() to return
  PersistenceFailure (code UNSUPPORTED_SCHEMA).
- Tampered hash in ref (while file is intact) causes load_verified() to
  return PersistenceFailure (code HASH_MISMATCH).
- Two runs with different run_ids are stored in isolated files; each
  verifies independently.
- All tests use tmp_path; no write outside tmp_path.
- PersistenceFailure codes never equal any ScientificStatus value.

Spec / plan references:
  constitution principle 7 (persist before gold)
  spec AC-19–AC-20
  plan §3 PredictionStore contract
  plan §4 PersistedPredictionRef, VerifiedPersistedPrediction
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from promoter_ai_extraction.models import (
    EvidenceItem,
    ExtractedValue,
    ExtractionRun,
    Property,
    PropertyResult,
    ScientificStatus,
    TechnicalFailure,
)
from promoter_ai_extraction.persistence import (
    SCHEMA_VERSION,
    PersistedPredictionRef,
    PersistenceFailure,
    PredictionStore,
    VerifiedPersistedPrediction,
)


# ─── Fixture helpers ──────────────────────────────────────────────────────────


def _evidence(seg_id: str = "seg:0001") -> EvidenceItem:
    return EvidenceItem(
        fragment="The TSS was at +1.",
        segment_id=seg_id,
        source_type="body_text",
        location="section 1",
    )


def _not_found_result(prop: Property, paper_id: str = "PMC12345") -> PropertyResult:
    return PropertyResult(
        paper_id=paper_id,
        promoter_name="rpoS_p1",
        property=prop,
        status=ScientificStatus.NOT_FOUND,
        values=(),
        candidate_values=(),
        evidence=(_evidence(),),
        abstention_reason="Not found.",
    )


def _extracted_result(paper_id: str = "PMC12345") -> PropertyResult:
    val = ExtractedValue(
        value_raw="-42",
        value_normalized="-42",
        qualifier=None,
        derivation_note=None,
        evidence=(_evidence(),),
    )
    return PropertyResult(
        paper_id=paper_id,
        promoter_name="rpoS_p1",
        property=Property.TSS,
        status=ScientificStatus.EXTRACTED,
        values=(val,),
        candidate_values=(),
        evidence=(_evidence(),),
        abstention_reason=None,
    )


def _make_run(
    run_id: str = "run-store-001",
    paper_id: str = "PMC12345",
) -> ExtractionRun:
    return ExtractionRun(
        run_id=run_id,
        paper_id=paper_id,
        promoter_name="rpoS_p1",
        tss=_extracted_result(paper_id=paper_id),
        caja_10=_not_found_result(prop=Property.CAJA_10, paper_id=paper_id),
        caja_35=_not_found_result(prop=Property.CAJA_35, paper_id=paper_id),
        sigma=_not_found_result(prop=Property.FACTOR_SIGMA, paper_id=paper_id),
    )


def _store(tmp_path: Path) -> PredictionStore:
    return PredictionStore(tmp_path / "predictions")


# ─── T021-A: save() returns a valid PersistedPredictionRef ────────────────────


def test_save_returns_persisted_prediction_ref(tmp_path: Path) -> None:
    run = _make_run()
    store = _store(tmp_path)
    result = store.save(run)
    assert isinstance(result, PersistedPredictionRef)


def test_persisted_ref_run_id_matches_run(tmp_path: Path) -> None:
    run = _make_run(run_id="unique-run-42")
    store = _store(tmp_path)
    ref = store.save(run)
    assert isinstance(ref, PersistedPredictionRef)
    assert ref.run_id == "unique-run-42"


def test_persisted_ref_schema_version_is_1(tmp_path: Path) -> None:
    run = _make_run()
    store = _store(tmp_path)
    ref = store.save(run)
    assert isinstance(ref, PersistedPredictionRef)
    assert ref.schema_version == SCHEMA_VERSION


def test_persisted_ref_file_path_is_absolute(tmp_path: Path) -> None:
    run = _make_run()
    store = _store(tmp_path)
    ref = store.save(run)
    assert isinstance(ref, PersistedPredictionRef)
    assert Path(ref.file_path).is_absolute()


def test_persisted_ref_content_hash_starts_with_sha256(tmp_path: Path) -> None:
    run = _make_run()
    store = _store(tmp_path)
    ref = store.save(run)
    assert isinstance(ref, PersistedPredictionRef)
    assert ref.content_hash.startswith("sha256:")


def test_persisted_ref_content_hash_matches_actual_file(tmp_path: Path) -> None:
    """The hash in the ref must match sha256 of the actual bytes on disk."""
    run = _make_run()
    store = _store(tmp_path)
    ref = store.save(run)
    assert isinstance(ref, PersistedPredictionRef)
    actual_bytes = Path(ref.file_path).read_bytes()
    expected_hash = "sha256:" + hashlib.sha256(actual_bytes).hexdigest()
    assert ref.content_hash == expected_hash


# ─── T021-B: Immutability of PersistedPredictionRef ──────────────────────────


def test_persisted_prediction_ref_is_frozen(tmp_path: Path) -> None:
    """PersistedPredictionRef must be frozen (immutable after construction)."""
    run = _make_run()
    store = _store(tmp_path)
    ref = store.save(run)
    assert isinstance(ref, PersistedPredictionRef)
    with pytest.raises((AttributeError, TypeError)):
        ref.run_id = "tampered"  # type: ignore[misc]


def test_persisted_prediction_ref_is_frozen_file_path(tmp_path: Path) -> None:
    """Attempting to set file_path on a frozen PersistedPredictionRef raises."""
    run = _make_run()
    store = _store(tmp_path)
    ref = store.save(run)
    assert isinstance(ref, PersistedPredictionRef)
    with pytest.raises((AttributeError, TypeError)):
        ref.file_path = "/tampered/path"  # type: ignore[misc]


def test_persisted_prediction_ref_is_frozen_schema_version(tmp_path: Path) -> None:
    run = _make_run()
    store = _store(tmp_path)
    ref = store.save(run)
    assert isinstance(ref, PersistedPredictionRef)
    with pytest.raises((AttributeError, TypeError)):
        ref.schema_version = 999  # type: ignore[misc]


def test_persisted_prediction_ref_is_frozen_content_hash(tmp_path: Path) -> None:
    run = _make_run()
    store = _store(tmp_path)
    ref = store.save(run)
    assert isinstance(ref, PersistedPredictionRef)
    with pytest.raises((AttributeError, TypeError)):
        ref.content_hash = "sha256:tampered"  # type: ignore[misc]


# ─── T021-C: File is created on disk ─────────────────────────────────────────


def test_file_exists_after_save(tmp_path: Path) -> None:
    run = _make_run()
    store = _store(tmp_path)
    ref = store.save(run)
    assert isinstance(ref, PersistedPredictionRef)
    assert Path(ref.file_path).exists()


def test_file_contains_valid_json(tmp_path: Path) -> None:
    run = _make_run()
    store = _store(tmp_path)
    ref = store.save(run)
    assert isinstance(ref, PersistedPredictionRef)
    raw = Path(ref.file_path).read_text(encoding="utf-8")
    record = json.loads(raw)
    assert record["run_id"] == run.run_id
    assert record["schema_version"] == SCHEMA_VERSION


# ─── T021-D: No-overwrite behavior ───────────────────────────────────────────


def test_save_same_run_id_twice_returns_failure(tmp_path: Path) -> None:
    """A second save with the same run_id must return PersistenceFailure."""
    run = _make_run(run_id="dup-run")
    store = _store(tmp_path)
    first = store.save(run)
    assert isinstance(first, PersistedPredictionRef)
    second = store.save(run)
    assert isinstance(second, PersistenceFailure)
    assert second.code == "FILE_EXISTS"


def test_save_same_run_id_does_not_overwrite_file(tmp_path: Path) -> None:
    """The original file must be unchanged after a failed second save."""
    run_a = _make_run(run_id="no-overwrite-test")
    store = _store(tmp_path)
    ref = store.save(run_a)
    assert isinstance(ref, PersistedPredictionRef)
    original_bytes = Path(ref.file_path).read_bytes()
    # Try to overwrite.
    store.save(run_a)
    # File must be identical.
    assert Path(ref.file_path).read_bytes() == original_bytes


def test_no_overwrite_failure_code_not_scientific_status(tmp_path: Path) -> None:
    """FILE_EXISTS failure code must not equal any ScientificStatus value."""
    scientific_values = {s.value for s in ScientificStatus}
    assert "FILE_EXISTS" not in scientific_values


# ─── T021-E: load_verified — correct path ────────────────────────────────────


def test_load_verified_returns_verified_persisted_prediction(tmp_path: Path) -> None:
    run = _make_run()
    store = _store(tmp_path)
    ref = store.save(run)
    assert isinstance(ref, PersistedPredictionRef)
    result = store.load_verified(ref)
    assert isinstance(result, VerifiedPersistedPrediction)


def test_load_verified_run_equals_original(tmp_path: Path) -> None:
    run = _make_run()
    store = _store(tmp_path)
    ref = store.save(run)
    assert isinstance(ref, PersistedPredictionRef)
    vpp = store.load_verified(ref)
    assert isinstance(vpp, VerifiedPersistedPrediction)
    assert vpp.run == run


def test_load_verified_ref_is_same_ref(tmp_path: Path) -> None:
    run = _make_run()
    store = _store(tmp_path)
    ref = store.save(run)
    assert isinstance(ref, PersistedPredictionRef)
    vpp = store.load_verified(ref)
    assert isinstance(vpp, VerifiedPersistedPrediction)
    assert vpp.ref == ref


def test_load_verified_created_at_is_reconstructed(tmp_path: Path) -> None:
    run = _make_run()
    store = _store(tmp_path)
    ref = store.save(run, created_at="2026-10-07T08:00:00Z")
    assert isinstance(ref, PersistedPredictionRef)
    vpp = store.load_verified(ref)
    assert isinstance(vpp, VerifiedPersistedPrediction)
    assert vpp.created_at == "2026-10-07T08:00:00Z"


def test_load_verified_document_hash_is_reconstructed(tmp_path: Path) -> None:
    run = _make_run()
    store = _store(tmp_path)
    ref = store.save(run, document_hash="sha256:aabbccdd")
    assert isinstance(ref, PersistedPredictionRef)
    vpp = store.load_verified(ref)
    assert isinstance(vpp, VerifiedPersistedPrediction)
    assert vpp.document_hash == "sha256:aabbccdd"


def test_load_verified_system_fingerprint_is_reconstructed(tmp_path: Path) -> None:
    fp = {"model": "test-model", "version": "1.0"}
    run = _make_run()
    store = _store(tmp_path)
    ref = store.save(run, system_fingerprint=fp)
    assert isinstance(ref, PersistedPredictionRef)
    vpp = store.load_verified(ref)
    assert isinstance(vpp, VerifiedPersistedPrediction)
    assert vpp.system_fingerprint == fp


# ─── T021-F: Immutability of VerifiedPersistedPrediction ─────────────────────


def test_verified_persisted_prediction_is_frozen(tmp_path: Path) -> None:
    run = _make_run()
    store = _store(tmp_path)
    ref = store.save(run)
    assert isinstance(ref, PersistedPredictionRef)
    vpp = store.load_verified(ref)
    assert isinstance(vpp, VerifiedPersistedPrediction)
    with pytest.raises((AttributeError, TypeError)):
        vpp.run = run  # type: ignore[misc]


# ─── T021-G: Corruption and hash verification ────────────────────────────────


def test_load_verified_corrupted_file_returns_hash_mismatch(tmp_path: Path) -> None:
    """A single-byte corruption in the file must cause HASH_MISMATCH."""
    run = _make_run()
    store = _store(tmp_path)
    ref = store.save(run)
    assert isinstance(ref, PersistedPredictionRef)
    # Corrupt the file.
    file_path = Path(ref.file_path)
    original = file_path.read_bytes()
    corrupted = bytes([original[0] ^ 0xFF]) + original[1:]
    file_path.write_bytes(corrupted)
    result = store.load_verified(ref)
    assert isinstance(result, PersistenceFailure)
    assert result.code == "HASH_MISMATCH"


def test_load_verified_tampered_hash_in_ref_returns_hash_mismatch(tmp_path: Path) -> None:
    """A tampered content_hash in the ref (file intact) must cause HASH_MISMATCH."""
    run = _make_run()
    store = _store(tmp_path)
    ref = store.save(run)
    assert isinstance(ref, PersistedPredictionRef)
    tampered_ref = PersistedPredictionRef(
        run_id=ref.run_id,
        file_path=ref.file_path,
        schema_version=ref.schema_version,
        content_hash="sha256:0000000000000000000000000000000000000000000000000000000000000000",
    )
    result = store.load_verified(tampered_ref)
    assert isinstance(result, PersistenceFailure)
    assert result.code == "HASH_MISMATCH"


def test_load_verified_missing_file_returns_file_not_found(tmp_path: Path) -> None:
    """A missing file must cause FILE_NOT_FOUND."""
    fake_ref = PersistedPredictionRef(
        run_id="nonexistent-run",
        file_path=str(tmp_path / "predictions" / "nonexistent.json"),
        schema_version=SCHEMA_VERSION,
        content_hash="sha256:aabb",
    )
    store = _store(tmp_path)
    result = store.load_verified(fake_ref)
    assert isinstance(result, PersistenceFailure)
    assert result.code == "FILE_NOT_FOUND"


# ─── T021-H: Incomplete/malformed record ─────────────────────────────────────


def test_load_verified_invalid_json_returns_corrupt_record(tmp_path: Path) -> None:
    """A file with invalid JSON must cause CORRUPT_RECORD."""
    store = _store(tmp_path)
    run = _make_run(run_id="corrupt-json-test")
    ref = store.save(run)
    assert isinstance(ref, PersistedPredictionRef)
    # Overwrite with invalid JSON (recalculate hash so hash check passes,
    # then verify that corrupt JSON is caught at parse stage).
    corrupt_data = b"NOT { valid json ]"
    corrupt_hash = "sha256:" + hashlib.sha256(corrupt_data).hexdigest()
    Path(ref.file_path).write_bytes(corrupt_data)
    bad_ref = PersistedPredictionRef(
        run_id=ref.run_id,
        file_path=ref.file_path,
        schema_version=ref.schema_version,
        content_hash=corrupt_hash,
    )
    result = store.load_verified(bad_ref)
    assert isinstance(result, PersistenceFailure)
    assert result.code == "CORRUPT_RECORD"


def test_load_verified_wrong_schema_version_returns_unsupported_schema(tmp_path: Path) -> None:
    """A file with schema_version != 1 must cause UNSUPPORTED_SCHEMA."""
    store = _store(tmp_path)
    run = _make_run(run_id="wrong-schema-test")
    ref = store.save(run)
    assert isinstance(ref, PersistedPredictionRef)
    # Read, modify schema_version, rewrite, update hash.
    raw = Path(ref.file_path).read_bytes()
    record = json.loads(raw.decode("utf-8"))
    record["schema_version"] = 999
    new_data = json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")
    new_hash = "sha256:" + hashlib.sha256(new_data).hexdigest()
    Path(ref.file_path).write_bytes(new_data)
    bad_ref = PersistedPredictionRef(
        run_id=ref.run_id,
        file_path=ref.file_path,
        schema_version=ref.schema_version,
        content_hash=new_hash,
    )
    result = store.load_verified(bad_ref)
    assert isinstance(result, PersistenceFailure)
    assert result.code == "UNSUPPORTED_SCHEMA"


def test_load_verified_missing_required_field_returns_corrupt_record(tmp_path: Path) -> None:
    """A record missing required fields must cause CORRUPT_RECORD."""
    store = _store(tmp_path)
    run = _make_run(run_id="missing-field-test")
    ref = store.save(run)
    assert isinstance(ref, PersistedPredictionRef)
    raw = Path(ref.file_path).read_bytes()
    record = json.loads(raw.decode("utf-8"))
    # Remove a required field.
    del record["tss"]
    new_data = json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")
    new_hash = "sha256:" + hashlib.sha256(new_data).hexdigest()
    Path(ref.file_path).write_bytes(new_data)
    bad_ref = PersistedPredictionRef(
        run_id=ref.run_id,
        file_path=ref.file_path,
        schema_version=ref.schema_version,
        content_hash=new_hash,
    )
    result = store.load_verified(bad_ref)
    assert isinstance(result, PersistenceFailure)
    assert result.code == "CORRUPT_RECORD"


# ─── T021-I: Isolation between run ids ───────────────────────────────────────


def test_two_runs_stored_in_separate_files(tmp_path: Path) -> None:
    """Different run_ids produce different files."""
    store = _store(tmp_path)
    run_a = _make_run(run_id="iso-run-A")
    run_b = _make_run(run_id="iso-run-B")
    ref_a = store.save(run_a)
    ref_b = store.save(run_b)
    assert isinstance(ref_a, PersistedPredictionRef)
    assert isinstance(ref_b, PersistedPredictionRef)
    assert ref_a.file_path != ref_b.file_path


def test_two_runs_verify_independently(tmp_path: Path) -> None:
    """Each run verifies independently; corrupting one does not affect the other."""
    store = _store(tmp_path)
    run_a = _make_run(run_id="iso-verif-A")
    run_b = _make_run(run_id="iso-verif-B")
    ref_a = store.save(run_a)
    ref_b = store.save(run_b)
    assert isinstance(ref_a, PersistedPredictionRef)
    assert isinstance(ref_b, PersistedPredictionRef)

    # Corrupt run_a's file.
    path_a = Path(ref_a.file_path)
    orig = path_a.read_bytes()
    path_a.write_bytes(bytes([orig[0] ^ 0xFF]) + orig[1:])

    # run_a fails.
    result_a = store.load_verified(ref_a)
    assert isinstance(result_a, PersistenceFailure)

    # run_b still passes.
    result_b = store.load_verified(ref_b)
    assert isinstance(result_b, VerifiedPersistedPrediction)
    assert result_b.run == run_b


def test_load_verified_run_a_does_not_load_run_b_data(tmp_path: Path) -> None:
    """load_verified with run_a's ref must return run_a's data."""
    store = _store(tmp_path)
    run_a = _make_run(run_id="data-iso-A", paper_id="PMC11111")
    run_b = _make_run(run_id="data-iso-B", paper_id="PMC22222")
    ref_a = store.save(run_a)
    store.save(run_b)
    assert isinstance(ref_a, PersistedPredictionRef)
    vpp = store.load_verified(ref_a)
    assert isinstance(vpp, VerifiedPersistedPrediction)
    assert vpp.run.paper_id == "PMC11111"
    assert vpp.run.run_id == "data-iso-A"


# ─── T021-J: PersistenceFailure codes do not equal ScientificStatus ───────────


def test_persistence_failure_code_not_scientific_status() -> None:
    """PersistenceFailure must reject codes that equal a ScientificStatus value."""
    scientific_codes = {s.value for s in ScientificStatus}
    for code in ("FILE_EXISTS", "HASH_MISMATCH", "FILE_NOT_FOUND", "CORRUPT_RECORD",
                 "WRITE_ERROR", "UNSUPPORTED_SCHEMA", "LOAD_ERROR"):
        assert code not in scientific_codes, (
            f"PersistenceFailure code {code!r} must not equal a ScientificStatus value."
        )


def test_persistence_failure_raises_on_scientific_status_code() -> None:
    """Constructing PersistenceFailure with a ScientificStatus code must raise."""
    with pytest.raises(ValueError, match="must not equal a ScientificStatus value"):
        PersistenceFailure(
            stage="write",
            code="EXTRACTED",  # this is a ScientificStatus value
            message="Should be rejected.",
            cause="test",
        )


# ─── T021-K: store directory created if absent ───────────────────────────────


def test_store_creates_directory_if_absent(tmp_path: Path) -> None:
    """PredictionStore must create the store directory if it does not exist."""
    new_dir = tmp_path / "brand_new_dir" / "nested"
    store = PredictionStore(new_dir)
    run = _make_run(run_id="dir-create-test")
    ref = store.save(run)
    assert isinstance(ref, PersistedPredictionRef)
    assert new_dir.exists()


# ─── T021-L: TechnicalFailure slots persist correctly ────────────────────────


def test_run_with_technical_failure_slot_persists_and_verifies(tmp_path: Path) -> None:
    """An ExtractionRun with a TechnicalFailure in one slot round-trips."""
    tf = TechnicalFailure(
        stage="extraction",
        code="BACKEND_ERROR",
        message="The backend timed out.",
        cause="TimeoutError",
    )
    run = ExtractionRun(
        run_id="tf-slot-run",
        paper_id="PMC99999",
        promoter_name="prom_TF",
        tss=tf,
        caja_10=_not_found_result(prop=Property.CAJA_10),
        caja_35=_not_found_result(prop=Property.CAJA_35),
        sigma=_not_found_result(prop=Property.FACTOR_SIGMA),
    )
    store = _store(tmp_path)
    ref = store.save(run)
    assert isinstance(ref, PersistedPredictionRef)
    vpp = store.load_verified(ref)
    assert isinstance(vpp, VerifiedPersistedPrediction)
    assert isinstance(vpp.run.tss, TechnicalFailure)
    assert vpp.run.tss.code == "BACKEND_ERROR"
    assert vpp.run == run
