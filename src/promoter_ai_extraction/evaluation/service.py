"""Evaluator service: verified persistence, then gold, then scoring (T033)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from promoter_ai_extraction.evaluation.comparison import compare_sets, predicted_value_set
from promoter_ai_extraction.evaluation.gold_loader import GoldLoadError, GoldLoader, GoldRecord
from promoter_ai_extraction.evaluation.gold_parser import GoldParseError, GoldParser, ParsedGoldValue
from promoter_ai_extraction.evaluation.metrics import EvaluationReport, aggregate_report
from promoter_ai_extraction.models import ExtractionRun, Property, ScientificStatus
from promoter_ai_extraction.persistence import (
    PersistedPredictionRef,
    PersistenceFailure,
    PredictionStore,
    VerifiedPersistedPrediction,
)

__all__ = ["EvaluationError", "EvaluationService"]

_SCIENTIFIC_CODES = frozenset(status.value for status in ScientificStatus)
_SLOT = {
    Property.TSS: "tss",
    Property.CAJA_10: "caja_10",
    Property.CAJA_35: "caja_35",
    Property.FACTOR_SIGMA: "sigma",
}


@dataclass(frozen=True, slots=True)
class EvaluationError:
    stage: str
    code: str
    message: str
    cause: str

    def __post_init__(self) -> None:
        if self.code in _SCIENTIFIC_CODES:
            raise ValueError(
                "EvaluationError.code must not equal a ScientificStatus value."
            )


class EvaluationService:
    """Score a persisted run against gold. Gold is unreachable without verification."""

    def __init__(
        self,
        store: PredictionStore,
        *,
        loader: GoldLoader | None = None,
        parser: GoldParser | None = None,
    ) -> None:
        self._store = store
        self._loader = loader or GoldLoader()
        self._parser = parser or GoldParser()

    def evaluate(
        self, source: object, gold_path: Path
    ) -> EvaluationReport | EvaluationError:
        if isinstance(source, ExtractionRun) or not isinstance(
            source, PersistedPredictionRef
        ):
            return _fail(
                "MISSING_VERIFIED_PERSISTENCE",
                "Evaluation requires a persisted prediction reference. "
                "In-memory runs and failed persistence records are rejected.",
                "TypeError",
            )
        verified = self._store.load_verified(source)
        if isinstance(verified, PersistenceFailure):
            return EvaluationError(
                stage="persistence",
                code=verified.code,
                message=verified.message,
                cause=verified.cause,
            )
        dataset = self._loader.load(verified, gold_path)
        if isinstance(dataset, GoldLoadError):
            return EvaluationError(
                stage=dataset.stage,
                code=dataset.code,
                message=dataset.message,
                cause=dataset.cause,
            )
        return self._score(verified, dataset.records)

    def _score(
        self,
        verified: VerifiedPersistedPrediction,
        records: tuple[GoldRecord, ...],
    ) -> EvaluationReport:
        run = verified.run
        comparisons = []
        parse_failures = 0
        technical_failures = 0
        tf_by_property: dict[Property, int] = {prop: 0 for prop in Property}
        tf_gold_values: dict[Property, int] = {prop: 0 for prop in Property}
        for record in records:
            if record.paper_id != run.paper_id or record.promoter_name != run.promoter_name:
                continue
            parsed = self._parser.parse(record)
            if isinstance(parsed, GoldParseError):
                parse_failures += 1
                continue
            attempt = getattr(run, _SLOT[record.property])
            predicted = predicted_value_set(attempt)
            if predicted is None:
                technical_failures += 1
                tf_by_property[record.property] += 1
                tf_gold_values[record.property] += len(parsed.gold_value_set)
                continue
            assert isinstance(parsed, ParsedGoldValue)
            comparisons.append(
                compare_sets(
                    paper_id=record.paper_id,
                    promoter_name=record.promoter_name,
                    property=record.property,
                    gold_value_set=parsed.gold_value_set,
                    predicted_value_set=predicted,
                    modalidad_origen=record.modalidad_origen,
                )
            )
        return aggregate_report(
            comparisons,
            parse_failures=parse_failures,
            technical_failures=technical_failures,
            technical_failures_by_property=tf_by_property,
            technical_failure_gold_values=tf_gold_values,
        )


def _fail(code: str, message: str, cause: str) -> EvaluationError:
    return EvaluationError(
        stage="evaluation",
        code=code,
        message=message,
        cause=cause,
    )
