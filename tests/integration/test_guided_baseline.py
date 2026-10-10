"""Synthetic TXT/TEI end-to-end wiring — T034 (RED) / T035 (GREEN)."""
from __future__ import annotations

from pathlib import Path

import pytest

from promoter_ai_extraction.application import GuidedBaselineApplication
from promoter_ai_extraction.documents import DocumentSource
from promoter_ai_extraction.evaluation.metrics import EvaluationReport
from promoter_ai_extraction.extraction import RawPropertyPayload, RawValuePayload
from promoter_ai_extraction.models import Property
from fakes import ScriptedBackend
from synthetic_gold import write_synthetic_gold

_BODY = (
    "The promoter lacZp1 TSS is -42 with Caja -10 TATAAT, "
    "Caja -35 TTGACA, and sigma70."
)
_TEI = f"""\
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text><body><p>{_BODY}</p></body></text>
</TEI>
"""


def _extracted(value: str, segment_id: str) -> RawPropertyPayload:
    return RawPropertyPayload(
        status="EXTRACTED",
        values=(
            RawValuePayload(
                value_raw=value,
                qualifier=None,
                evidence_segment_ids=(segment_id,),
                evidence_fragments=(_BODY,),
            ),
        ),
        candidates=(),
        abstention_reason=None,
        result_evidence=(),
    )


def _backend(segment_id: str) -> ScriptedBackend:
    return ScriptedBackend(
        {
            Property.TSS: _extracted("-42", segment_id),
            Property.CAJA_10: _extracted("TATAAT", segment_id),
            Property.CAJA_35: _extracted("TTGACA", segment_id),
            Property.FACTOR_SIGMA: _extracted("sigma70", segment_id),
        }
    )


def _gold_rows() -> list[dict[str, str]]:
    return [
        {
            "ID_paper": "PMC12345",
            "Nombre_promotor": "lacZp1",
            "Propiedad": "TSS",
            "GT_para_referencia": "-42",
            "Modalidad_origen": "texto_explicito",
        },
        {
            "ID_paper": "PMC12345",
            "Nombre_promotor": "lacZp1",
            "Propiedad": "Caja -10",
            "GT_para_referencia": "TATAAT",
            "Modalidad_origen": "texto_explicito",
        },
        {
            "ID_paper": "PMC12345",
            "Nombre_promotor": "lacZp1",
            "Propiedad": "Caja -35",
            "GT_para_referencia": "TTGACA",
            "Modalidad_origen": "texto_explicito",
        },
        {
            "ID_paper": "PMC12345",
            "Nombre_promotor": "lacZp1",
            "Propiedad": "Factor sigma",
            "GT_para_referencia": "sigma70",
            "Modalidad_origen": "texto_explicito",
        },
    ]


@pytest.mark.parametrize(
    ("fmt", "content", "segment_id"),
    [
        ("TXT", _BODY, "txt:p:0000"),
        ("TEI/XML", _TEI, "tei:p:0000"),
    ],
)
def test_synthetic_extract_persist_evaluate(
    tmp_path: Path,
    fmt: str,
    content: str,
    segment_id: str,
) -> None:
    gold = write_synthetic_gold(tmp_path / "gold.xlsx", _gold_rows())
    app = GuidedBaselineApplication(backend=_backend(segment_id))
    source = DocumentSource(
        paper_id="PMC12345",
        path=None,
        content=content,
        format=fmt,  # type: ignore[arg-type]
    )
    outcome = app.run(
        source=source,
        promoter_name="lacZp1",
        gold_path=gold,
        prediction_dir=tmp_path / "predictions",
        run_id=f"e2e-{fmt.replace('/', '-')}",
    )
    assert isinstance(outcome, EvaluationReport)
    assert outcome.evaluated_rows == 4
    assert outcome.parse_failures == 0
    assert outcome.technical_failures == 0
    for prop in Property:
        metrics = outcome.by_property[prop]
        assert metrics.tp == 1
        assert metrics.fp == 0
        assert metrics.fn == 0
        assert metrics.exact_row_accuracy == 1.0
    assert "false-assertion" in outcome.limitation_note
