"""Prediction persistence: schema version 1, serialization, and PredictionStore (T020/T022).

Public surface
--------------
SCHEMA_VERSION          – integer constant; schema version 1.
PersistedPredictionRef  – frozen carrier: run_id, file path, schema version, content hash.
VerifiedPersistedPrediction – frozen capability: immutable run + verification proof.
PersistenceFailure      – frozen technical failure for persistence-specific errors.
serialize_run           – produce deterministic JSON bytes from an ExtractionRun.
deserialize_run         – reconstruct an ExtractionRun from a parsed schema-v1 record.
PredictionStore         – write-once atomic local JSON store with hash verification.

Design decisions (recorded in progress ledger, not decisions.md):
  - Persistence metadata (created_at, document_hash, system_fingerprint) is kept
    explicit in the serialized record rather than added to ExtractionRun.  This
    avoids changing the extraction-side data model for persistence concerns.
  - Deterministic JSON: json.dumps with sort_keys=True and compact separators
    ensures identical bytes for identical logical content.
  - Type tags ("property_result" / "technical_failure") in each slot enable
    unambiguous deserialization without sentinel fields.
  - Atomic write uses tempfile.NamedTemporaryFile + os.rename (POSIX rename is
    atomic).  On Windows, os.replace is used instead.  The final file is opened
    for creation only (x-mode) if the store uses exclusive-creation semantics;
    for the atomic-rename path the rename itself is the gate.
  - No overwrite: before persisting, the store checks that no file exists at the
    target path.  If a file already exists the save() returns PersistenceFailure.
  - Content hash: sha256 of the UTF-8 encoded JSON bytes, stored in
    PersistedPredictionRef and verified by load_verified() before returning a
    VerifiedPersistedPrediction.
  - PersistenceFailure codes never equal any ScientificStatus value (constitution
    principle 6 applied to the persistence layer by analogy).
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from promoter_ai_extraction.models import (
    CandidateRejectionReason,
    EvidenceItem,
    ExtractedValue,
    ExtractionRun,
    Property,
    PropertyResult,
    RejectedCandidate,
    ScientificStatus,
    TechnicalFailure,
    PropertyAttempt,
)

__all__ = [
    "SCHEMA_VERSION",
    "PersistedPredictionRef",
    "VerifiedPersistedPrediction",
    "PersistenceFailure",
    "serialize_run",
    "deserialize_run",
    "PredictionStore",
]

# ─── Schema version ───────────────────────────────────────────────────────────

SCHEMA_VERSION: int = 1

# ─── Immutable reference and capability carriers ──────────────────────────────


@dataclass(frozen=True, slots=True)
class PersistedPredictionRef:
    """Immutable reference to a successfully persisted prediction file.

    Carries enough information to locate and verify the persisted record without
    holding the full in-memory run.  Evaluation code must require this type rather
    than accepting an in-memory ExtractionRun (spec AC-19; constitution principle 7).

    Attributes
    ----------
    run_id:
        The run identifier embedded in the persisted file.
    file_path:
        Absolute path to the persisted JSON file as a string.
    schema_version:
        The schema version written in the file (integer).
    content_hash:
        ``sha256:<hex>`` digest of the persisted file's UTF-8 bytes.
    """

    run_id: str
    file_path: str
    schema_version: int
    content_hash: str


@dataclass(frozen=True, slots=True)
class VerifiedPersistedPrediction:
    """An immutable, verified persisted prediction with a capability token.

    Evaluation code must accept this type rather than a direct ExtractionRun.
    The presence of this object proves that (a) the run was atomically written
    to disk, and (b) the content hash was verified before this object was created.

    Attributes
    ----------
    ref:
        The persisted reference that was verified.
    run:
        The reconstructed ExtractionRun from the verified file.
    created_at:
        ISO-8601 timestamp embedded in the persisted record, or None.
    document_hash:
        Document hash embedded in the persisted record, or None.
    system_fingerprint:
        System/model/config fingerprint embedded in the persisted record, or None.
    """

    ref: PersistedPredictionRef
    run: ExtractionRun
    created_at: str | None
    document_hash: str | None
    system_fingerprint: dict[str, Any] | None


# ─── Persistence-specific failure ────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class PersistenceFailure:
    """A technical failure specific to the persistence layer.

    Never carries a ScientificStatus code (constitution principle 6 by analogy).
    Failures are persistence-specific (e.g. FILE_EXISTS, HASH_MISMATCH,
    WRITE_ERROR, CORRUPT_RECORD) and never represent scientific abstentions.

    Attributes
    ----------
    stage:
        Persistence sub-stage: ``"write"`` or ``"load"``.
    code:
        Stable failure code.  Must not equal any ScientificStatus value.
    message:
        Human-readable, safe description.  No private data.
    cause:
        Exception type or cause category.
    """

    stage: str
    code: str
    message: str
    cause: str

    _SCIENTIFIC_CODES = frozenset(s.value for s in ScientificStatus)

    def __post_init__(self) -> None:
        if self.code in self._SCIENTIFIC_CODES:
            raise ValueError(
                f"PersistenceFailure.code must not equal a ScientificStatus value "
                f"(constitution principle 6 analogy). Got: {self.code!r}."
            )


# ─── Serialization helpers ────────────────────────────────────────────────────

def _serialize_evidence_item(ev: EvidenceItem) -> dict[str, Any]:
    return {
        "fragment": ev.fragment,
        "segment_id": ev.segment_id,
        "source_type": ev.source_type,
        "location": ev.location,
    }


def _deserialize_evidence_item(d: dict[str, Any]) -> EvidenceItem:
    return EvidenceItem(
        fragment=d["fragment"],
        segment_id=d["segment_id"],
        source_type=d["source_type"],
        location=d.get("location"),
    )


def _serialize_extracted_value(v: ExtractedValue) -> dict[str, Any]:
    return {
        "value_raw": v.value_raw,
        "value_normalized": v.value_normalized,
        "qualifier": v.qualifier,
        "derivation_note": v.derivation_note,
        "evidence": [_serialize_evidence_item(e) for e in v.evidence],
    }


def _deserialize_extracted_value(d: dict[str, Any]) -> ExtractedValue:
    return ExtractedValue(
        value_raw=d["value_raw"],
        value_normalized=d["value_normalized"],
        qualifier=d.get("qualifier"),
        derivation_note=d.get("derivation_note"),
        evidence=tuple(_deserialize_evidence_item(e) for e in d.get("evidence", [])),
    )


def _serialize_rejected_candidate(rc: RejectedCandidate) -> dict[str, Any]:
    return {
        "candidate_raw": rc.candidate_raw,
        "rejection_reason": rc.rejection_reason.value,
        "evidence": _serialize_evidence_item(rc.evidence) if rc.evidence is not None else None,
        "rule_violated": rc.rule_violated,
    }


def _deserialize_rejected_candidate(d: dict[str, Any]) -> RejectedCandidate:
    ev_dict = d.get("evidence")
    return RejectedCandidate(
        candidate_raw=d["candidate_raw"],
        rejection_reason=CandidateRejectionReason(d["rejection_reason"]),
        evidence=_deserialize_evidence_item(ev_dict) if ev_dict is not None else None,
        rule_violated=d["rule_violated"],
    )


def _serialize_property_result(r: PropertyResult) -> dict[str, Any]:
    return {
        "type": "property_result",
        "paper_id": r.paper_id,
        "promoter_name": r.promoter_name,
        "property": r.property.value,
        "status": r.status.value,
        "values": [_serialize_extracted_value(v) for v in r.values],
        "candidate_values": [_serialize_rejected_candidate(c) for c in r.candidate_values],
        "evidence": [_serialize_evidence_item(e) for e in r.evidence],
        "abstention_reason": r.abstention_reason,
    }


def _deserialize_property_result(d: dict[str, Any]) -> PropertyResult:
    return PropertyResult(
        paper_id=d["paper_id"],
        promoter_name=d["promoter_name"],
        property=Property(d["property"]),
        status=ScientificStatus(d["status"]),
        values=tuple(_deserialize_extracted_value(v) for v in d.get("values", [])),
        candidate_values=tuple(
            _deserialize_rejected_candidate(c) for c in d.get("candidate_values", [])
        ),
        evidence=tuple(_deserialize_evidence_item(e) for e in d.get("evidence", [])),
        abstention_reason=d.get("abstention_reason"),
    )


def _serialize_technical_failure(tf: TechnicalFailure) -> dict[str, Any]:
    return {
        "type": "technical_failure",
        "stage": tf.stage,
        "code": tf.code,
        "message": tf.message,
        "cause": tf.cause,
    }


def _deserialize_technical_failure(d: dict[str, Any]) -> TechnicalFailure:
    return TechnicalFailure(
        stage=d["stage"],
        code=d["code"],
        message=d["message"],
        cause=d["cause"],
    )


def _serialize_attempt(attempt: PropertyAttempt) -> dict[str, Any]:
    if isinstance(attempt, TechnicalFailure):
        return _serialize_technical_failure(attempt)
    return _serialize_property_result(attempt)


def _deserialize_attempt(d: dict[str, Any]) -> PropertyAttempt:
    type_tag = d.get("type", "")
    if type_tag == "technical_failure":
        return _deserialize_technical_failure(d)
    if type_tag == "property_result":
        return _deserialize_property_result(d)
    raise ValueError(
        f"Unknown attempt type tag in persisted record: {type_tag!r}. "
        "Expected 'property_result' or 'technical_failure'."
    )


# ─── Public serialization API ─────────────────────────────────────────────────


def serialize_run(
    run: ExtractionRun,
    *,
    created_at: str | None = None,
    document_hash: str | None = None,
    system_fingerprint: dict[str, Any] | None = None,
) -> str:
    """Serialize an ExtractionRun to a deterministic JSON string (schema v1).

    The output is fully deterministic: identical logical content always
    produces identical bytes.  Optional persistence metadata is embedded in
    the top-level record without modifying the ExtractionRun object.

    Parameters
    ----------
    run:
        The extraction run to serialize.
    created_at:
        ISO-8601 timestamp string, or None.
    document_hash:
        Document hash (e.g. ``"sha256:<hex>"``), or None.
    system_fingerprint:
        System/model/config fingerprint mapping, or None.

    Returns
    -------
    str
        Deterministic compact JSON string.
    """
    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run.run_id,
        "created_at": created_at,
        "paper_id": run.paper_id,
        "promoter_name": run.promoter_name,
        "document_hash": document_hash,
        "system_fingerprint": system_fingerprint,
        "tss": _serialize_attempt(run.tss),
        "caja_10": _serialize_attempt(run.caja_10),
        "caja_35": _serialize_attempt(run.caja_35),
        "sigma": _serialize_attempt(run.sigma),
    }
    return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def deserialize_run(record: dict[str, Any]) -> ExtractionRun:
    """Reconstruct an ExtractionRun from a parsed schema-v1 record.

    Parameters
    ----------
    record:
        Parsed JSON dict (e.g. the output of ``json.loads(serialize_run(...))``)

    Returns
    -------
    ExtractionRun
        Immutable, reconstructed extraction run.

    Raises
    ------
    ValueError
        If the record contains an unrecognized schema version, missing
        required fields, or an unknown type tag.
    KeyError
        If required fields are absent from the record.
    """
    schema_v = record.get("schema_version")
    if schema_v != SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported schema version: {schema_v!r}. Expected {SCHEMA_VERSION}."
        )
    return ExtractionRun(
        run_id=record["run_id"],
        paper_id=record["paper_id"],
        promoter_name=record["promoter_name"],
        tss=_deserialize_attempt(record["tss"]),
        caja_10=_deserialize_attempt(record["caja_10"]),
        caja_35=_deserialize_attempt(record["caja_35"]),
        sigma=_deserialize_attempt(record["sigma"]),
    )


# ─── PredictionStore ──────────────────────────────────────────────────────────


def _sha256_of(data: bytes) -> str:
    """Return ``sha256:<hex>`` digest of *data*."""
    return "sha256:" + hashlib.sha256(data).hexdigest()


class PredictionStore:
    """Write-once atomic local JSON prediction store.

    Each run is persisted as one JSON file.  The file name is derived from the
    run_id and the store directory.  Persistence is:

    1. **Atomic** — written via a temp file in the same directory, then renamed.
    2. **No-overwrite** — if a file already exists for the target path,
       ``save()`` returns a :class:`PersistenceFailure` rather than overwriting.
    3. **Hash-verified** — ``load_verified()`` rechecks the sha256 digest before
       returning a :class:`VerifiedPersistedPrediction`.

    Parameters
    ----------
    store_dir:
        Directory where prediction JSON files are written.  Created on first
        write if absent.
    """

    def __init__(self, store_dir: Path) -> None:
        self._store_dir = store_dir

    def _target_path(self, run_id: str) -> Path:
        """Return the expected file path for *run_id*."""
        # Sanitize run_id: replace filesystem-unsafe characters.
        safe_id = run_id.replace("/", "_").replace("\\", "_").replace(":", "_")
        return self._store_dir / f"{safe_id}.json"

    def save(
        self,
        run: ExtractionRun,
        *,
        created_at: str | None = None,
        document_hash: str | None = None,
        system_fingerprint: dict[str, Any] | None = None,
    ) -> PersistedPredictionRef | PersistenceFailure:
        """Atomically persist *run* to disk and return a reference.

        If ``created_at`` is None a UTC timestamp is generated automatically.

        Returns
        -------
        PersistedPredictionRef
            On success: immutable reference containing run_id, file path,
            schema version, and content hash.
        PersistenceFailure
            On any error: FILE_EXISTS if the target already exists, or
            WRITE_ERROR for I/O failures.
        """
        effective_created_at = created_at or datetime.now(timezone.utc).isoformat()
        target = self._target_path(run.run_id)

        # No-overwrite check before attempting write.
        if target.exists():
            return PersistenceFailure(
                stage="write",
                code="FILE_EXISTS",
                message=(
                    f"A persisted prediction for run_id {run.run_id!r} already "
                    f"exists at {target}. Overwriting is not permitted."
                ),
                cause="FileExistsError",
            )

        try:
            self._store_dir.mkdir(parents=True, exist_ok=True)
            json_str = serialize_run(
                run,
                created_at=effective_created_at,
                document_hash=document_hash,
                system_fingerprint=system_fingerprint,
            )
            data = json_str.encode("utf-8")
            content_hash = _sha256_of(data)

            # Atomic write: temp file in same directory → rename.
            fd, tmp_path_str = tempfile.mkstemp(
                dir=self._store_dir, prefix=".tmp_pred_", suffix=".json"
            )
            try:
                with os.fdopen(fd, "wb") as fh:
                    fh.write(data)
                os.replace(tmp_path_str, str(target))
            except Exception:
                # Clean up temp file if rename failed.
                try:
                    os.unlink(tmp_path_str)
                except OSError:
                    pass
                raise

        except Exception as exc:
            return PersistenceFailure(
                stage="write",
                code="WRITE_ERROR",
                message=f"Failed to write prediction to disk: {exc!s}",
                cause=type(exc).__name__,
            )

        return PersistedPredictionRef(
            run_id=run.run_id,
            file_path=str(target.resolve()),
            schema_version=SCHEMA_VERSION,
            content_hash=content_hash,
        )

    def load_verified(
        self,
        ref: PersistedPredictionRef,
    ) -> VerifiedPersistedPrediction | PersistenceFailure:
        """Load and verify a persisted prediction from *ref*.

        Steps:
        1. Read the file at ``ref.file_path``.
        2. Recompute sha256 of the file bytes.
        3. Compare with ``ref.content_hash``; fail on mismatch.
        4. Parse JSON and deserialize the ExtractionRun.
        5. Return an immutable :class:`VerifiedPersistedPrediction`.

        Returns
        -------
        VerifiedPersistedPrediction
            Immutable verified prediction with run and optional metadata.
        PersistenceFailure
            FILE_NOT_FOUND, HASH_MISMATCH, CORRUPT_RECORD, or LOAD_ERROR.
        """
        file_path = Path(ref.file_path)

        try:
            data = file_path.read_bytes()
        except FileNotFoundError:
            return PersistenceFailure(
                stage="load",
                code="FILE_NOT_FOUND",
                message=f"Persisted prediction file not found: {file_path}",
                cause="FileNotFoundError",
            )
        except OSError as exc:
            return PersistenceFailure(
                stage="load",
                code="LOAD_ERROR",
                message=f"Cannot read persisted prediction file: {exc!s}",
                cause=type(exc).__name__,
            )

        # Verify hash.
        actual_hash = _sha256_of(data)
        if actual_hash != ref.content_hash:
            return PersistenceFailure(
                stage="load",
                code="HASH_MISMATCH",
                message=(
                    f"Content hash mismatch for run {ref.run_id!r}. "
                    f"Expected {ref.content_hash!r}, got {actual_hash!r}."
                ),
                cause="HashMismatch",
            )

        # Parse JSON.
        try:
            record: dict[str, Any] = json.loads(data.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            return PersistenceFailure(
                stage="load",
                code="CORRUPT_RECORD",
                message=f"Persisted prediction file is not valid JSON: {exc!s}",
                cause=type(exc).__name__,
            )

        # Verify schema version.
        schema_v = record.get("schema_version")
        if schema_v != SCHEMA_VERSION:
            return PersistenceFailure(
                stage="load",
                code="UNSUPPORTED_SCHEMA",
                message=(
                    f"Persisted file has unsupported schema version {schema_v!r}. "
                    f"Expected {SCHEMA_VERSION}."
                ),
                cause="SchemaVersionError",
            )

        # Deserialize.
        try:
            run = deserialize_run(record)
        except (KeyError, ValueError) as exc:
            return PersistenceFailure(
                stage="load",
                code="CORRUPT_RECORD",
                message=f"Failed to deserialize persisted prediction: {exc!s}",
                cause=type(exc).__name__,
            )

        return VerifiedPersistedPrediction(
            ref=ref,
            run=run,
            created_at=record.get("created_at"),
            document_hash=record.get("document_hash"),
            system_fingerprint=record.get("system_fingerprint"),
        )
