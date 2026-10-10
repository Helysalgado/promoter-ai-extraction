"""RED tests for schema version 1 and deterministic ExtractionRun serialization (T019).

RED: collection fails because ``promoter_ai_extraction.persistence`` does not
exist yet.  After T020 implementation all tests pass (GREEN).

Coverage:
- schema_version == 1 in every serialized record.
- Round-trip: serialize → deserialize → equivalent ExtractionRun for all
  field combinations (EXTRACTED, all abstentions, TechnicalFailure, multiple
  values, rejected candidates, distributed evidence, None optional fields).
- Determinism: the same ExtractionRun serializes to identical bytes on
  repeated calls.
- Required top-level fields are present in the serialized record.
- Optional metadata fields (created_at, document_hash, system_fingerprint)
  are preserved through round-trip when supplied.
- Enum values serialized as strings (not as Python repr).
- All four property slots (tss, caja_10, caja_35, sigma) survive round-trip.

Spec / plan references:
  plan §3 PredictionStore.save/load_verified contract
  plan §4 PersistedPredictionRef, VerifiedPersistedPrediction entities
  spec AC-19–AC-20
"""
from __future__ import annotations

import json

import pytest

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
)
from promoter_ai_extraction.persistence import (
    SCHEMA_VERSION,
    deserialize_run,
    serialize_run,
)


# ─── Fixture helpers ──────────────────────────────────────────────────────────


def _evidence(fragment: str = "The TSS was at +1.", seg_id: str = "seg:0001") -> EvidenceItem:
    return EvidenceItem(
        fragment=fragment,
        segment_id=seg_id,
        source_type="body_text",
        location="section 2, paragraph 1",
    )


def _extracted_value(
    raw: str = "-42",
    normalized: str = "-42",
    qualifier: str | None = None,
    derivation: str | None = None,
) -> ExtractedValue:
    return ExtractedValue(
        value_raw=raw,
        value_normalized=normalized,
        qualifier=qualifier,
        derivation_note=derivation,
        evidence=(_evidence(),),
    )


def _rejected_candidate(
    raw: str = "TATAAT",
    rule: str = "sequence too short",
    with_evidence: bool = True,
) -> RejectedCandidate:
    return RejectedCandidate(
        candidate_raw=raw,
        rejection_reason=CandidateRejectionReason.INVALID_CANDIDATE,
        evidence=_evidence() if with_evidence else None,
        rule_violated=rule,
    )


def _property_result(
    status: ScientificStatus = ScientificStatus.EXTRACTED,
    values: tuple[ExtractedValue, ...] = (),
    candidates: tuple[RejectedCandidate, ...] = (),
    evidence: tuple[EvidenceItem, ...] = (),
    abstention_reason: str | None = None,
    prop: Property = Property.TSS,
) -> PropertyResult:
    return PropertyResult(
        paper_id="PMC12345",
        promoter_name="rpoS_p1",
        property=prop,
        status=status,
        values=values,
        candidate_values=candidates,
        evidence=evidence,
        abstention_reason=abstention_reason,
    )


def _technical_failure(
    stage: str = "extraction",
    code: str = "BACKEND_ERROR",
    message: str = "The backend timed out.",
    cause: str = "TimeoutError",
) -> TechnicalFailure:
    return TechnicalFailure(stage=stage, code=code, message=message, cause=cause)


def _minimal_run(run_id: str = "run-001") -> ExtractionRun:
    """ExtractionRun with EXTRACTED TSS and NOT_FOUND for the other three."""
    ev = _evidence()
    val = _extracted_value()
    return ExtractionRun(
        run_id=run_id,
        paper_id="PMC12345",
        promoter_name="rpoS_p1",
        tss=_property_result(
            prop=Property.TSS,
            status=ScientificStatus.EXTRACTED,
            values=(val,),
            evidence=(ev,),
        ),
        caja_10=_property_result(
            prop=Property.CAJA_10,
            status=ScientificStatus.NOT_FOUND,
            evidence=(ev,),
            abstention_reason="No caja -10 sequence found.",
        ),
        caja_35=_property_result(
            prop=Property.CAJA_35,
            status=ScientificStatus.NOT_FOUND,
            evidence=(),
            abstention_reason="No caja -35 sequence found.",
        ),
        sigma=_property_result(
            prop=Property.FACTOR_SIGMA,
            status=ScientificStatus.AMBIGUOUS,
            evidence=(ev,),
            abstention_reason="Multiple sigma factors mentioned without assignment.",
        ),
    )


# ─── T019-A: Schema version ───────────────────────────────────────────────────


def test_schema_version_constant_is_1() -> None:
    """SCHEMA_VERSION exported from persistence module must equal 1."""
    assert SCHEMA_VERSION == 1


def test_serialized_record_contains_schema_version_1() -> None:
    """Every serialized run embeds schema_version == 1."""
    run = _minimal_run()
    record = json.loads(serialize_run(run))
    assert record["schema_version"] == 1


# ─── T019-B: Required top-level fields ───────────────────────────────────────


def test_serialized_record_contains_run_id() -> None:
    run = _minimal_run(run_id="abc-123")
    record = json.loads(serialize_run(run))
    assert record["run_id"] == "abc-123"


def test_serialized_record_contains_paper_id() -> None:
    run = _minimal_run()
    record = json.loads(serialize_run(run))
    assert record["paper_id"] == "PMC12345"


def test_serialized_record_contains_promoter_name() -> None:
    run = _minimal_run()
    record = json.loads(serialize_run(run))
    assert record["promoter_name"] == "rpoS_p1"


def test_serialized_record_contains_created_at_when_supplied() -> None:
    run = _minimal_run()
    record = json.loads(serialize_run(run, created_at="2026-10-07T08:00:00Z"))
    assert record["created_at"] == "2026-10-07T08:00:00Z"


def test_serialized_record_contains_null_created_at_when_not_supplied() -> None:
    run = _minimal_run()
    record = json.loads(serialize_run(run))
    assert "created_at" in record
    assert record["created_at"] is None


def test_serialized_record_contains_document_hash_when_supplied() -> None:
    run = _minimal_run()
    digest = "sha256:deadbeef"
    record = json.loads(serialize_run(run, document_hash=digest))
    assert record["document_hash"] == digest


def test_serialized_record_contains_null_document_hash_when_not_supplied() -> None:
    run = _minimal_run()
    record = json.loads(serialize_run(run))
    assert "document_hash" in record
    assert record["document_hash"] is None


def test_serialized_record_contains_system_fingerprint_when_supplied() -> None:
    run = _minimal_run()
    fp = {"model": "gpt-test-1", "config_hash": "abc123"}
    record = json.loads(serialize_run(run, system_fingerprint=fp))
    assert record["system_fingerprint"] == fp


def test_serialized_record_contains_null_system_fingerprint_when_not_supplied() -> None:
    run = _minimal_run()
    record = json.loads(serialize_run(run))
    assert "system_fingerprint" in record
    assert record["system_fingerprint"] is None


def test_serialized_record_contains_all_four_property_slots() -> None:
    run = _minimal_run()
    record = json.loads(serialize_run(run))
    for slot in ("tss", "caja_10", "caja_35", "sigma"):
        assert slot in record, f"Missing slot: {slot}"


# ─── T019-C: Enum serialization ───────────────────────────────────────────────


def test_property_enum_serialized_as_string() -> None:
    """Property enum values must serialize as their string representation."""
    run = _minimal_run()
    record = json.loads(serialize_run(run))
    tss_block = record["tss"]
    assert tss_block["property"] == "TSS"


def test_scientific_status_enum_serialized_as_string() -> None:
    run = _minimal_run()
    record = json.loads(serialize_run(run))
    tss_block = record["tss"]
    assert tss_block["status"] == "EXTRACTED"


# ─── T019-D: Round-trip correctness ───────────────────────────────────────────


def test_round_trip_minimal_run() -> None:
    """Serialize then deserialize produces an equivalent ExtractionRun."""
    original = _minimal_run()
    serialized = serialize_run(original)
    record = json.loads(serialized)
    restored = deserialize_run(record)
    assert restored == original


def test_round_trip_technical_failure_in_all_slots() -> None:
    """TechnicalFailure in every slot round-trips correctly."""
    tf = _technical_failure()
    run = ExtractionRun(
        run_id="run-tf",
        paper_id="PMC99999",
        promoter_name="test_p",
        tss=tf,
        caja_10=tf,
        caja_35=tf,
        sigma=tf,
    )
    record = json.loads(serialize_run(run))
    restored = deserialize_run(record)
    assert restored == run


def test_round_trip_extracted_value_with_qualifier() -> None:
    """An ExtractedValue with a qualifier and derivation note round-trips."""
    val = ExtractedValue(
        value_raw="+1",
        value_normalized="+1",
        qualifier="putative",
        derivation_note="Plus sign designates TSS anchor.",
        evidence=(_evidence(fragment="putative TSS +1", seg_id="seg:A"),),
    )
    run = ExtractionRun(
        run_id="run-qual",
        paper_id="PMC11111",
        promoter_name="prom_A",
        tss=_property_result(
            prop=Property.TSS,
            status=ScientificStatus.EXTRACTED,
            values=(val,),
            evidence=(_evidence(),),
        ),
        caja_10=_property_result(prop=Property.CAJA_10, status=ScientificStatus.NOT_FOUND, abstention_reason="none"),
        caja_35=_property_result(prop=Property.CAJA_35, status=ScientificStatus.NOT_FOUND, abstention_reason="none"),
        sigma=_property_result(prop=Property.FACTOR_SIGMA, status=ScientificStatus.NOT_FOUND, abstention_reason="none"),
    )
    record = json.loads(serialize_run(run))
    restored = deserialize_run(record)
    tss_result = restored.tss
    assert isinstance(tss_result, PropertyResult)
    assert len(tss_result.values) == 1
    v = tss_result.values[0]
    assert v.qualifier == "putative"
    assert v.derivation_note == "Plus sign designates TSS anchor."


def test_round_trip_multiple_values() -> None:
    """Multiple accepted values for one property all survive round-trip."""
    v1 = _extracted_value(raw="TATAAT", normalized="TATAAT")
    v2 = _extracted_value(raw="TATAAG", normalized="TATAAG")
    run = ExtractionRun(
        run_id="run-multi",
        paper_id="PMC22222",
        promoter_name="prom_B",
        tss=_property_result(prop=Property.TSS, status=ScientificStatus.NOT_FOUND, abstention_reason="x"),
        caja_10=_property_result(
            prop=Property.CAJA_10,
            status=ScientificStatus.EXTRACTED,
            values=(v1, v2),
            evidence=(_evidence(),),
        ),
        caja_35=_property_result(prop=Property.CAJA_35, status=ScientificStatus.NOT_FOUND, abstention_reason="x"),
        sigma=_property_result(prop=Property.FACTOR_SIGMA, status=ScientificStatus.NOT_FOUND, abstention_reason="x"),
    )
    record = json.loads(serialize_run(run))
    restored = deserialize_run(record)
    caja_10 = restored.caja_10
    assert isinstance(caja_10, PropertyResult)
    assert len(caja_10.values) == 2
    assert caja_10.values[0].value_raw == "TATAAT"
    assert caja_10.values[1].value_raw == "TATAAG"


def test_round_trip_rejected_candidate_with_evidence() -> None:
    """A RejectedCandidate with evidence round-trips correctly."""
    cand = _rejected_candidate(with_evidence=True)
    run = ExtractionRun(
        run_id="run-cand",
        paper_id="PMC33333",
        promoter_name="prom_C",
        tss=_property_result(
            prop=Property.TSS,
            status=ScientificStatus.NOT_FOUND,
            candidates=(cand,),
            abstention_reason="rejected",
        ),
        caja_10=_property_result(prop=Property.CAJA_10, status=ScientificStatus.NOT_FOUND, abstention_reason="x"),
        caja_35=_property_result(prop=Property.CAJA_35, status=ScientificStatus.NOT_FOUND, abstention_reason="x"),
        sigma=_property_result(prop=Property.FACTOR_SIGMA, status=ScientificStatus.NOT_FOUND, abstention_reason="x"),
    )
    record = json.loads(serialize_run(run))
    restored = deserialize_run(record)
    tss = restored.tss
    assert isinstance(tss, PropertyResult)
    assert len(tss.candidate_values) == 1
    rc = tss.candidate_values[0]
    assert rc.candidate_raw == "TATAAT"
    assert rc.rejection_reason == CandidateRejectionReason.INVALID_CANDIDATE
    assert rc.evidence is not None
    assert rc.evidence.fragment == "The TSS was at +1."


def test_round_trip_rejected_candidate_without_evidence() -> None:
    cand = _rejected_candidate(with_evidence=False)
    run = ExtractionRun(
        run_id="run-cand-noev",
        paper_id="PMC44444",
        promoter_name="prom_D",
        tss=_property_result(
            prop=Property.TSS,
            status=ScientificStatus.NOT_FOUND,
            candidates=(cand,),
            abstention_reason="rejected",
        ),
        caja_10=_property_result(prop=Property.CAJA_10, status=ScientificStatus.NOT_FOUND, abstention_reason="x"),
        caja_35=_property_result(prop=Property.CAJA_35, status=ScientificStatus.NOT_FOUND, abstention_reason="x"),
        sigma=_property_result(prop=Property.FACTOR_SIGMA, status=ScientificStatus.NOT_FOUND, abstention_reason="x"),
    )
    record = json.loads(serialize_run(run))
    restored = deserialize_run(record)
    tss = restored.tss
    assert isinstance(tss, PropertyResult)
    rc = tss.candidate_values[0]
    assert rc.evidence is None


def test_round_trip_distributed_evidence() -> None:
    """Multiple evidence items on a single property result all survive."""
    ev1 = _evidence(fragment="TSS located at -42.", seg_id="seg:0001")
    ev2 = _evidence(fragment="Mapping confirmed by primer extension.", seg_id="seg:0002")
    val = ExtractedValue(
        value_raw="-42",
        value_normalized="-42",
        qualifier=None,
        derivation_note=None,
        evidence=(ev1, ev2),
    )
    run = ExtractionRun(
        run_id="run-distrib",
        paper_id="PMC55555",
        promoter_name="prom_E",
        tss=_property_result(
            prop=Property.TSS,
            status=ScientificStatus.EXTRACTED,
            values=(val,),
            evidence=(ev1, ev2),
        ),
        caja_10=_property_result(prop=Property.CAJA_10, status=ScientificStatus.NOT_FOUND, abstention_reason="x"),
        caja_35=_property_result(prop=Property.CAJA_35, status=ScientificStatus.NOT_FOUND, abstention_reason="x"),
        sigma=_property_result(prop=Property.FACTOR_SIGMA, status=ScientificStatus.NOT_FOUND, abstention_reason="x"),
    )
    record = json.loads(serialize_run(run))
    restored = deserialize_run(record)
    tss = restored.tss
    assert isinstance(tss, PropertyResult)
    assert len(tss.evidence) == 2
    assert len(tss.values[0].evidence) == 2


def test_round_trip_all_abstention_statuses() -> None:
    """All four scientific abstention statuses survive round-trip."""
    for status in (
        ScientificStatus.NOT_FOUND,
        ScientificStatus.INSUFFICIENT_EVIDENCE,
        ScientificStatus.UNSUPPORTED_MODALITY,
        ScientificStatus.AMBIGUOUS,
    ):
        result = _property_result(
            prop=Property.TSS,
            status=status,
            evidence=(_evidence(),),
            abstention_reason=f"{status} reason",
        )
        run = ExtractionRun(
            run_id=f"run-{status}",
            paper_id="PMC66666",
            promoter_name="prom_F",
            tss=result,
            caja_10=_property_result(prop=Property.CAJA_10, status=ScientificStatus.NOT_FOUND, abstention_reason="x"),
            caja_35=_property_result(prop=Property.CAJA_35, status=ScientificStatus.NOT_FOUND, abstention_reason="x"),
            sigma=_property_result(prop=Property.FACTOR_SIGMA, status=ScientificStatus.NOT_FOUND, abstention_reason="x"),
        )
        record = json.loads(serialize_run(run))
        restored = deserialize_run(record)
        tss = restored.tss
        assert isinstance(tss, PropertyResult)
        assert tss.status == status


def test_round_trip_none_location_in_evidence() -> None:
    """EvidenceItem with location=None survives round-trip."""
    ev = EvidenceItem(
        fragment="Some fragment.",
        segment_id="seg:X",
        source_type="body_text",
        location=None,
    )
    val = ExtractedValue(
        value_raw="sigma70",
        value_normalized="sigma70",
        qualifier=None,
        derivation_note=None,
        evidence=(ev,),
    )
    run = ExtractionRun(
        run_id="run-nullloc",
        paper_id="PMC77777",
        promoter_name="prom_G",
        tss=_property_result(prop=Property.TSS, status=ScientificStatus.NOT_FOUND, abstention_reason="x"),
        caja_10=_property_result(prop=Property.CAJA_10, status=ScientificStatus.NOT_FOUND, abstention_reason="x"),
        caja_35=_property_result(prop=Property.CAJA_35, status=ScientificStatus.NOT_FOUND, abstention_reason="x"),
        sigma=_property_result(
            prop=Property.FACTOR_SIGMA,
            status=ScientificStatus.EXTRACTED,
            values=(val,),
            evidence=(ev,),
        ),
    )
    record = json.loads(serialize_run(run))
    restored = deserialize_run(record)
    sigma = restored.sigma
    assert isinstance(sigma, PropertyResult)
    assert sigma.values[0].evidence[0].location is None


# ─── T019-E: Determinism ──────────────────────────────────────────────────────


def test_serialize_is_deterministic() -> None:
    """Serializing the same ExtractionRun twice yields identical bytes."""
    run = _minimal_run()
    assert serialize_run(run) == serialize_run(run)


def test_serialize_same_run_deterministic_with_metadata() -> None:
    """Determinism holds when optional metadata is supplied."""
    run = _minimal_run()
    fp = {"model": "m1", "version": "1.0"}
    s1 = serialize_run(run, created_at="2026-10-07T00:00:00Z", document_hash="sha256:aabb", system_fingerprint=fp)
    s2 = serialize_run(run, created_at="2026-10-07T00:00:00Z", document_hash="sha256:aabb", system_fingerprint=fp)
    assert s1 == s2


def test_serialize_different_runs_differ() -> None:
    """Two runs with different run_ids serialize to different bytes."""
    r1 = _minimal_run(run_id="run-AAA")
    r2 = _minimal_run(run_id="run-BBB")
    assert serialize_run(r1) != serialize_run(r2)


# ─── T019-F: Technical failure type tag ──────────────────────────────────────


def test_technical_failure_slot_carries_type_tag() -> None:
    """A TechnicalFailure slot in the serialized record is tagged as 'technical_failure'."""
    tf = _technical_failure()
    run = ExtractionRun(
        run_id="run-tftag",
        paper_id="PMC88888",
        promoter_name="prom_H",
        tss=tf,
        caja_10=_property_result(prop=Property.CAJA_10, status=ScientificStatus.NOT_FOUND, abstention_reason="x"),
        caja_35=_property_result(prop=Property.CAJA_35, status=ScientificStatus.NOT_FOUND, abstention_reason="x"),
        sigma=_property_result(prop=Property.FACTOR_SIGMA, status=ScientificStatus.NOT_FOUND, abstention_reason="x"),
    )
    record = json.loads(serialize_run(run))
    # The type tag must allow deserializer to reconstruct TechnicalFailure vs PropertyResult
    assert record["tss"]["type"] in ("technical_failure", "TechnicalFailure")


def test_property_result_slot_carries_type_tag() -> None:
    run = _minimal_run()
    record = json.loads(serialize_run(run))
    assert record["tss"]["type"] in ("property_result", "PropertyResult")
