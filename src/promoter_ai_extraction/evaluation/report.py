"""Serialize the T042 dual-view evaluation report. Evaluator-only."""
from __future__ import annotations

from collections.abc import Mapping

from promoter_ai_extraction.evaluation.metrics import (
    EvaluationReport,
    headline_property_counts,
)

__all__ = ["serialize_benchmark_report"]


def serialize_benchmark_report(
    report: EvaluationReport,
    *,
    software_version: str,
    parser_version: str,
    model_versions: Mapping[str, object],
) -> dict[str, object]:
    scientific: dict[str, object] = {}
    end_to_end: dict[str, object] = {}
    for prop, metrics in report.by_property.items():
        tf_count = report.technical_failures_by_property.get(prop, 0)
        scientific[prop.value] = {
            "tp": metrics.tp,
            "fp": metrics.fp,
            "fn": metrics.fn,
            "n_targets": metrics.n_targets,
            "n_predictions_with_value": metrics.n_predictions_with_value,
            "precision": metrics.precision,
            "recall": metrics.recall,
            "f1": metrics.f1,
            "exact_row_accuracy": metrics.exact_row_accuracy,
            "recall_texto_explicito": metrics.recall_texto_explicito,
            "recall_imagen_only": metrics.recall_imagen_only,
        }
        end_to_end[prop.value] = headline_property_counts(
            metrics,
            technical_failures=tf_count,
            unrecovered_gold_values=report.technical_failure_gold_values.get(prop, 0),
        )
    versions = dict(model_versions)
    prompt_raw = versions.get("prompt_version")
    prompt_version = prompt_raw if isinstance(prompt_raw, str) else ""
    return {
        "evaluated_rows": report.evaluated_rows,
        "parse_failures": report.parse_failures,
        "technical_failures": report.technical_failures,
        "technical_failure_rate": report.technical_failure_rate,
        "scientific_abstentions": report.scientific_abstentions,
        "coverage": report.coverage,
        "limitation_note": report.limitation_note,
        "headline": "end_to_end",
        "software_version": software_version,
        "parser_version": parser_version,
        "prompt_version": prompt_version,
        "model_versions": versions,
        "end_to_end": {"by_property": end_to_end, "totals": _totals(end_to_end)},
        "scientific": {"by_property": scientific, "totals": _totals(scientific)},
    }


def _totals(by_property: Mapping[str, Mapping[str, object]]) -> dict[str, int | float]:
    tp = sum(int(item["tp"]) for item in by_property.values())
    fp = sum(int(item["fp"]) for item in by_property.values())
    fn = sum(int(item["fn"]) for item in by_property.values())
    n_targets = sum(int(item["n_targets"]) for item in by_property.values())
    precision = _ratio(tp, tp + fp)
    recall = _ratio(tp, tp + fn)
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "n_targets": n_targets,
        "precision": precision,
        "recall": recall,
        "f1": _f1(precision, recall),
    }


def _ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _f1(precision: float, recall: float) -> float:
    if precision == 0.0 and recall == 0.0:
        return 0.0
    denom = precision + recall
    if denom == 0.0:
        return 0.0
    return 2 * precision * recall / denom
