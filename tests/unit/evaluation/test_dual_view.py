"""T031 dual-view numerators and denominators for the T042 report."""
from __future__ import annotations

import pytest

from promoter_ai_extraction.evaluation.comparison import compare_sets
from promoter_ai_extraction.evaluation.metrics import (
    aggregate_report,
    headline_property_counts,
)
from promoter_ai_extraction.evaluation.report import serialize_benchmark_report
from promoter_ai_extraction.models import Property


def _row(prop: Property, gold: str, predicted: frozenset[str]) -> object:
    return compare_sets(
        paper_id="PMC12345",
        promoter_name="lacZp1",
        property=prop,
        gold_value_set=frozenset({gold}),
        predicted_value_set=predicted,
        modalidad_origen="texto_explicito",
    )


def test_technical_failure_on_positive_gold_is_headline_fn_not_scientific_target() -> None:
    rows = (_row(Property.TSS, "-42", frozenset({"-42"})),)
    report = aggregate_report(
        rows,
        parse_failures=0,
        technical_failures=1,
        technical_failures_by_property={
            Property.TSS: 0,
            Property.CAJA_10: 0,
            Property.CAJA_35: 1,
            Property.FACTOR_SIGMA: 0,
        },
    )
    scientific_35 = report.by_property[Property.CAJA_35]
    assert scientific_35.n_targets == 0
    assert scientific_35.tp == 0
    assert scientific_35.fn == 0
    headline_35 = headline_property_counts(scientific_35, technical_failures=1)
    assert headline_35["tp"] == 0
    assert headline_35["fp"] == 0
    assert headline_35["fn"] == 1
    assert headline_35["n_targets"] == 1
    assert headline_35["recall"] == pytest.approx(0.0)

    scientific_tss = report.by_property[Property.TSS]
    headline_tss = headline_property_counts(scientific_tss, technical_failures=0)
    assert headline_tss["tp"] == 1
    assert headline_tss["fn"] == 0
    assert headline_tss["n_targets"] == 1
    assert headline_tss["recall"] == pytest.approx(1.0)


def test_scientific_abstention_is_fn_in_both_views_and_not_a_technical_failure() -> None:
    rows = (_row(Property.CAJA_10, "TATAAT", frozenset()),)
    report = aggregate_report(
        rows,
        parse_failures=0,
        technical_failures=0,
        technical_failures_by_property={prop: 0 for prop in Property},
    )
    assert report.scientific_abstentions == 1
    assert report.technical_failures == 0
    scientific = report.by_property[Property.CAJA_10]
    assert scientific.fn == 1
    assert scientific.n_targets == 1
    headline = headline_property_counts(scientific, technical_failures=0)
    assert headline["fn"] == 1
    assert headline["n_targets"] == 1
    assert headline["tp"] == 0


def test_serialized_report_exposes_both_views_and_versions() -> None:
    rows = (_row(Property.TSS, "-42", frozenset({"-42"})),)
    report = aggregate_report(
        rows,
        parse_failures=0,
        technical_failures=1,
        technical_failures_by_property={
            Property.TSS: 0,
            Property.CAJA_10: 0,
            Property.CAJA_35: 1,
            Property.FACTOR_SIGMA: 0,
        },
    )
    payload = serialize_benchmark_report(
        report,
        software_version="0.1.0",
        parser_version="current-workset-v1",
        model_versions={"provider": "scripted", "model": "fake", "prompt_version": "test"},
    )
    assert payload["headline"] == "end_to_end"
    assert "false-assertion" in payload["limitation_note"]
    assert payload["parser_version"] == "current-workset-v1"
    assert payload["software_version"] == "0.1.0"
    assert payload["technical_failures"] == 1
    assert payload["scientific_abstentions"] == 0
    assert payload["end_to_end"]["by_property"]["Caja -35"]["fn"] == 1
    assert payload["end_to_end"]["by_property"]["Caja -35"]["n_targets"] == 1
    assert payload["scientific"]["by_property"]["Caja -35"]["n_targets"] == 0
    assert payload["scientific"]["by_property"]["TSS"]["tp"] == 1
    assert payload["scientific"]["by_property"]["TSS"]["recall_texto_explicito"] == pytest.approx(1.0)
    assert payload["model_versions"]["model"] == "fake"
    assert payload["end_to_end"]["by_property"]["Caja -35"]["fn"] != payload["scientific"]["by_property"]["Caja -35"]["fn"]
    assert payload["technical_failure_rate"] == pytest.approx(1 / 2)


def test_multivalue_technical_failure_adds_one_fn_per_gold_value() -> None:
    rows = (_row(Property.TSS, "-42", frozenset({"-42"})),)
    report = aggregate_report(
        rows,
        parse_failures=0,
        technical_failures=1,
        technical_failures_by_property={
            Property.TSS: 0,
            Property.CAJA_10: 1,
            Property.CAJA_35: 0,
            Property.FACTOR_SIGMA: 0,
        },
        technical_failure_gold_values={
            Property.TSS: 0,
            Property.CAJA_10: 2,
            Property.CAJA_35: 0,
            Property.FACTOR_SIGMA: 0,
        },
    )
    assert report.technical_failures == 1
    assert report.technical_failure_rate == pytest.approx(1 / 2)
    scientific = report.by_property[Property.CAJA_10]
    assert scientific.n_targets == 0
    assert scientific.tp == 0
    assert scientific.fp == 0
    assert scientific.fn == 0
    headline = headline_property_counts(
        scientific,
        technical_failures=1,
        unrecovered_gold_values=2,
    )
    assert headline["tp"] == 0
    assert headline["fp"] == 0
    assert headline["fn"] == 2
    assert headline["n_targets"] == 1
    assert headline["precision"] == pytest.approx(0.0)
    assert headline["recall"] == pytest.approx(0.0)
    assert headline["f1"] == pytest.approx(0.0)
    serialized = serialize_benchmark_report(
        report,
        software_version="0.1.0",
        parser_version="current-workset-v1",
        model_versions={"model": "fake"},
    )
    end_10 = serialized["end_to_end"]["by_property"]["Caja -10"]
    sci_10 = serialized["scientific"]["by_property"]["Caja -10"]
    assert end_10["fn"] == 2
    assert end_10["tp"] == 0
    assert end_10["fp"] == 0
    assert sci_10["n_targets"] == 0
    assert sci_10["fn"] == 0
    assert serialized["technical_failures"] == 1
    assert serialized["technical_failure_rate"] == pytest.approx(0.5)


def test_multivalue_scientific_abstention_keeps_value_level_fn_in_both_views() -> None:
    rows = (
        compare_sets(
            paper_id="PMC12345",
            promoter_name="lacZp1",
            property=Property.CAJA_10,
            gold_value_set=frozenset({"TATAAT", "TAAAAT"}),
            predicted_value_set=frozenset(),
            modalidad_origen="texto_explicito",
        ),
    )
    report = aggregate_report(
        rows,
        parse_failures=0,
        technical_failures=0,
        technical_failures_by_property={prop: 0 for prop in Property},
        technical_failure_gold_values={prop: 0 for prop in Property},
    )
    assert report.scientific_abstentions == 1
    assert report.technical_failures == 0
    assert report.technical_failure_rate == pytest.approx(0.0)
    scientific = report.by_property[Property.CAJA_10]
    assert scientific.fn == 2
    assert scientific.n_targets == 1
    assert scientific.tp == 0
    assert scientific.precision == pytest.approx(0.0)
    assert scientific.recall == pytest.approx(0.0)
    assert scientific.f1 == pytest.approx(0.0)
    headline = headline_property_counts(
        scientific, technical_failures=0, unrecovered_gold_values=0
    )
    assert headline["fn"] == 2
    assert headline["n_targets"] == 1
    assert headline["recall"] == pytest.approx(0.0)
