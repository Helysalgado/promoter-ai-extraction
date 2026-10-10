"""T042 CLI and persisted fingerprint tests. Synthetic fixtures only. No live OpenAI."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from promoter_ai_extraction.baseline import main
from promoter_ai_extraction.extraction import (
    BackendFailure,
    RawPropertyPayload,
    RawValuePayload,
    SafeExtractionInput,
)
from promoter_ai_extraction.models import Property, ScientificStatus
from fakes import ScriptedBackend
from .test_baseline_runner import (
    _BODY,
    _matching_backend,
    _rewrite_document_path,
    _write_layout,
)

_REPO = Path(__file__).resolve().parents[2]


class FingerprintBackend(ScriptedBackend):
    def __init__(self, responses: dict[Property, RawPropertyPayload | BackendFailure]) -> None:
        super().__init__(responses)
        self._by_property: dict[str, dict[str, str | None]] = {}

    def generate(self, safe_input: SafeExtractionInput) -> RawPropertyPayload | BackendFailure:
        outcome = super().generate(safe_input)
        self._by_property[safe_input.property.value] = {
            "model_snapshot": f"snap-{safe_input.property.value}",
            "system_fingerprint": f"fp-{safe_input.property.value}",
        }
        return outcome

    def reproducibility_metadata(self) -> dict[str, object]:
        return {
            "common": {
                "provider": "scripted",
                "model": "fake-model",
                "api": "none",
                "prompt_version": "safe-extraction-v1",
                "schema_version": "raw-property-payload-v1",
            },
            "by_property": dict(self._by_property),
        }


def test_cli_success_exit_zero_writes_dual_view_report(tmp_path: Path) -> None:
    manifest, documents, gold, predictions, report = _write_layout(tmp_path)
    backend = FingerprintBackend(_matching_backend()._responses)
    code = main(
        [
            "--manifest",
            str(manifest),
            "--documents",
            str(documents),
            "--gold",
            str(gold),
            "--predictions",
            str(predictions),
            "--report",
            str(report),
        ],
        backend=backend,
    )
    assert code == 0
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["evaluated_rows"] == 4
    assert payload["headline"] == "end_to_end"
    assert payload["parser_version"] == "current-workset-v1"
    assert payload["software_version"]
    assert payload["model_versions"]["model"] == "fake-model"
    assert payload["end_to_end"]["by_property"]["TSS"]["tp"] == 1
    assert payload["scientific"]["by_property"]["TSS"]["recall_texto_explicito"] == 1.0
    assert payload["technical_failures"] == 0
    assert payload["technical_failure_rate"] == pytest.approx(0.0)
    assert "false-assertion" in payload["limitation_note"]


def test_cli_persists_per_property_fingerprints_and_document_hash(tmp_path: Path) -> None:
    manifest, documents, gold, predictions, report = _write_layout(tmp_path)
    backend = FingerprintBackend(_matching_backend()._responses)
    assert (
        main(
            [
                "--manifest",
                str(manifest),
                "--documents",
                str(documents),
                "--gold",
                str(gold),
                "--predictions",
                str(predictions),
                "--report",
                str(report),
            ],
            backend=backend,
        )
        == 0
    )
    persisted = json.loads(next(predictions.glob("*.json")).read_text(encoding="utf-8"))
    fingerprint = persisted["system_fingerprint"]
    assert persisted["document_hash"]
    assert fingerprint["document_hash"] == persisted["document_hash"]
    by_property = fingerprint["by_property"]
    assert by_property["TSS"]["model_snapshot"] == "snap-TSS"
    assert by_property["Caja -35"]["model_snapshot"] == "snap-Caja -35"
    assert by_property["TSS"]["system_fingerprint"] != by_property["Caja -35"]["system_fingerprint"]
    dumped = json.dumps(persisted)
    assert "sk-" not in dumped
    assert "OPENAI_API_KEY" not in dumped
    assert "GT_para_referencia" not in dumped


def test_cli_leaky_manifest_exits_nonzero(tmp_path: Path) -> None:
    manifest, documents, gold, predictions, report = _write_layout(tmp_path)
    leaky = json.loads(manifest.read_text(encoding="utf-8"))
    leaky["cases"][0]["GT_para_referencia"] = "-42"
    manifest.write_text(json.dumps(leaky), encoding="utf-8")
    code = main(
        [
            "--manifest",
            str(manifest),
            "--documents",
            str(documents),
            "--gold",
            str(gold),
            "--predictions",
            str(predictions),
            "--report",
            str(report),
        ],
        backend=_matching_backend(),
    )
    assert code != 0
    assert not report.is_file()
    assert not list(predictions.glob("*.json"))


def test_cli_path_escape_exits_nonzero(tmp_path: Path) -> None:
    manifest, documents, gold, predictions, report = _write_layout(tmp_path)
    (tmp_path / "secret.txt").write_text(_BODY, encoding="utf-8")
    _rewrite_document_path(manifest, "../secret.txt")
    code = main(
        [
            "--manifest",
            str(manifest),
            "--documents",
            str(documents),
            "--gold",
            str(gold),
            "--predictions",
            str(predictions),
            "--report",
            str(report),
        ],
        backend=_matching_backend(),
    )
    assert code != 0
    assert not report.is_file()


def test_cli_technical_failure_is_headline_fn_not_scientific_abstention(
    tmp_path: Path,
) -> None:
    from .test_baseline_runner import _abstention, _extracted

    manifest, documents, gold, predictions, report = _write_layout(tmp_path)
    backend = FingerprintBackend(
        {
            Property.TSS: _extracted("-42", "txt:p:0000"),
            Property.CAJA_10: _abstention("txt:p:0000"),
            Property.CAJA_35: BackendFailure(code="TIMEOUT", message="synthetic timeout"),
            Property.FACTOR_SIGMA: _extracted("sigma70", "txt:p:0000"),
        }
    )
    assert (
        main(
            [
                "--manifest",
                str(manifest),
                "--documents",
                str(documents),
                "--gold",
                str(gold),
                "--predictions",
                str(predictions),
                "--report",
                str(report),
            ],
            backend=backend,
        )
        == 0
    )
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["technical_failures"] == 1
    assert payload["technical_failure_rate"] == pytest.approx(1 / 4)
    assert payload["scientific_abstentions"] == 1
    end_35 = payload["end_to_end"]["by_property"]["Caja -35"]
    sci_35 = payload["scientific"]["by_property"]["Caja -35"]
    assert end_35["fn"] == 1
    assert end_35["n_targets"] == 1
    assert sci_35["n_targets"] == 0
    assert sci_35["fn"] == 0
    sci_10 = payload["scientific"]["by_property"]["Caja -10"]
    end_10 = payload["end_to_end"]["by_property"]["Caja -10"]
    assert sci_10["fn"] == 1
    assert sci_10["n_targets"] == 1
    assert end_10["fn"] == 1
    persisted = json.loads(next(predictions.glob("*.json")).read_text(encoding="utf-8"))
    assert persisted["caja_35"]["type"] == "technical_failure"
    assert persisted["caja_35"]["code"] not in {status.value for status in ScientificStatus}
    assert persisted["caja_10"]["status"] == "INSUFFICIENT_EVIDENCE"


def test_cli_multivalue_timeout_counts_fn_per_gold_value(tmp_path: Path) -> None:
    from .test_baseline_runner import _extracted
    from synthetic_gold import write_synthetic_gold

    manifest, documents, _old_gold, predictions, report = _write_layout(tmp_path)
    gold = write_synthetic_gold(
        tmp_path / "gold-multi.xlsx",
        [
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
                "GT_para_referencia": "TATAAT + TAAAAT",
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
        ],
    )
    backend = FingerprintBackend(
        {
            Property.TSS: _extracted("-42", "txt:p:0000"),
            Property.CAJA_10: BackendFailure(code="TIMEOUT", message="synthetic timeout"),
            Property.CAJA_35: _extracted("TTGACA", "txt:p:0000"),
            Property.FACTOR_SIGMA: _extracted("sigma70", "txt:p:0000"),
        }
    )
    assert (
        main(
            [
                "--manifest",
                str(manifest),
                "--documents",
                str(documents),
                "--gold",
                str(gold),
                "--predictions",
                str(predictions),
                "--report",
                str(report),
            ],
            backend=backend,
        )
        == 0
    )
    payload = json.loads(report.read_text(encoding="utf-8"))
    end_10 = payload["end_to_end"]["by_property"]["Caja -10"]
    sci_10 = payload["scientific"]["by_property"]["Caja -10"]
    assert payload["technical_failures"] == 1
    assert payload["technical_failure_rate"] == pytest.approx(1 / 4)
    assert end_10["tp"] == 0
    assert end_10["fp"] == 0
    assert end_10["fn"] == 2
    assert end_10["n_targets"] == 1
    assert end_10["precision"] == pytest.approx(0.0)
    assert end_10["recall"] == pytest.approx(0.0)
    assert end_10["f1"] == pytest.approx(0.0)
    assert sci_10["n_targets"] == 0
    assert sci_10["fn"] == 0
    assert payload["scientific_abstentions"] == 0


def test_cli_missing_credential_exits_nonzero_without_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest, documents, gold, predictions, report = _write_layout(tmp_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    code = main(
        [
            "--manifest",
            str(manifest),
            "--documents",
            str(documents),
            "--gold",
            str(gold),
            "--predictions",
            str(predictions),
            "--report",
            str(report),
        ]
    )
    assert code != 0
    assert not report.is_file()
    assert not list(predictions.glob("*.json"))


def test_module_help_exits_zero() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "promoter_ai_extraction.baseline", "--help"],
        cwd=_REPO,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert "--manifest" in completed.stdout
    assert "--documents" in completed.stdout
    assert "--gold" in completed.stdout
    assert "--predictions" in completed.stdout
    assert "--report" in completed.stdout
    assert "--max-output-tokens" in completed.stdout


def test_cli_forwards_output_cap_to_backend(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: dict[str, object] = {}

    class _CaptureBackend:
        def __init__(self, **kwargs: object) -> None:
            seen.update(kwargs)

        def generate(self, safe_input: SafeExtractionInput) -> BackendFailure:
            return BackendFailure(code="STOPPED", message="cost-control test")

        def reproducibility_metadata(self) -> dict[str, object]:
            return {"common": {}, "by_property": {}}

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-a-real-key-do-not-leak")
    monkeypatch.setattr(
        "promoter_ai_extraction.baseline.OpenAIModelBackend",
        _CaptureBackend,
    )
    manifest, documents, gold, predictions, report = _write_layout(tmp_path)
    code = main(
        [
            "--manifest",
            str(manifest),
            "--documents",
            str(documents),
            "--gold",
            str(gold),
            "--predictions",
            str(predictions),
            "--report",
            str(report),
            "--max-output-tokens",
            "4096",
        ]
    )
    assert seen["max_output_tokens"] == 4096
    assert code in (0, 1)


def test_cli_rejects_non_positive_output_cap(tmp_path: Path) -> None:
    manifest, documents, gold, predictions, report = _write_layout(tmp_path)
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "promoter_ai_extraction.baseline",
            "--manifest",
            str(manifest),
            "--documents",
            str(documents),
            "--gold",
            str(gold),
            "--predictions",
            str(predictions),
            "--report",
            str(report),
            "--max-output-tokens",
            "0",
        ],
        cwd=_REPO,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode != 0
    assert "positive integer" in completed.stderr
    assert "unrecognized arguments" not in completed.stderr
    assert not report.is_file()
    assert "sk-" not in completed.stdout
    assert "sk-" not in completed.stderr


def test_module_missing_args_exits_nonzero() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "promoter_ai_extraction.baseline"],
        cwd=_REPO,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode != 0
