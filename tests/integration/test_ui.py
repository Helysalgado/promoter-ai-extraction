"""Local scientific UI. Synthetic HTTP only. No provider calls."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from fakes import ScriptedBackend
from promoter_ai_extraction.api import MAX_DOCUMENT_CHARS, create_app
from promoter_ai_extraction.extraction import (
    BackendFailure,
    RawCandidatePayload,
    RawPropertyPayload,
    RawValuePayload,
    SafeExtractionInput,
)
from promoter_ai_extraction.models import Property

_PARA = "The promoter narnZp9 uses TATAGT."
_ROOT = Path(__file__).resolve().parents[2]
_UI = _ROOT / "src" / "promoter_ai_extraction" / "ui"
_PROPERTIES = ("TSS", "Caja -10", "Caja -35", "Factor sigma")


def _extracted(value: str) -> RawPropertyPayload:
    return RawPropertyPayload(
        status="EXTRACTED",
        values=(
            RawValuePayload(
                value_raw=value,
                qualifier="putative",
                evidence_segment_ids=("txt:p:0000",),
                evidence_fragments=(_PARA,),
            ),
        ),
        candidates=(),
        abstention_reason=None,
        result_evidence=(),
    )


def _four(
    replacements: dict[Property, RawPropertyPayload | BackendFailure] | None = None,
) -> ScriptedBackend:
    scripted: dict[Property, RawPropertyPayload | BackendFailure] = {
        Property.TSS: _extracted("-42"),
        Property.CAJA_10: _extracted("TATAGT"),
        Property.CAJA_35: _extracted("TTGATA"),
        Property.FACTOR_SIGMA: _extracted("sigma32"),
    }
    if replacements:
        scripted.update(replacements)
    return ScriptedBackend(scripted)


class _CountingBackend:
    def __init__(self, inner: ScriptedBackend) -> None:
        self._inner = inner
        self.calls = 0

    def generate(self, safe_input: SafeExtractionInput):
        self.calls += 1
        return self._inner.generate(safe_input)


class _IdenticalEmbedder:
    model_id = "synthetic-identical"

    def embed(self, texts: list[str]) -> list[tuple[float, ...]]:
        return [(1.0, 0.0) for _ in texts]


def _client(tmp_path: Path, backend: _CountingBackend | None = None) -> TestClient:
    app = create_app(
        backend=backend,
        prediction_dir=tmp_path,
        embedder=_IdenticalEmbedder(),
    )
    return TestClient(app)


def _body(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "paper_id": "SYNTH-UI-01",
        "promoter_name": "narnZp9",
        "document_format": "TXT",
        "document": _PARA,
    }
    payload.update(overrides)
    return payload


def _text(name: str) -> str:
    return (_UI / name).read_text(encoding="utf-8")


def _brace(source: str, open_at: int) -> str:
    depth = 0
    for index in range(open_at, len(source)):
        char = source[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[open_at : index + 1]
    raise AssertionError("unbalanced brace")


def _function_body(source: str, name: str) -> str:
    token = f"function {name}"
    start = source.index(token)
    brace = source.index("{", start)
    return _brace(source, brace)


def _rules(source: str) -> dict[str, object]:
    marker = "const UI_RULES = "
    start = source.index(marker)
    brace = source.index("{", start)
    return json.loads(_brace(source, brace))


def _detect(name: str, formats: list[list[str]]) -> str:
    lower = name.lower()
    for suffix, fmt in formats:
        if lower.endswith(suffix):
            return fmt
    return ""


def test_get_root_returns_the_spanish_page(tmp_path: Path) -> None:
    response = _client(tmp_path).get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    page = response.text
    assert 'lang="es"' in page
    assert "PMID/ID" in page
    assert 'href="/ui/app.css"' in page
    assert 'src="/ui/app.js"' in page
    for name in _PROPERTIES:
        assert f'data-property="{name}"' in page
    assert 'id="confirm-call"' in page
    assert 'id="run"' in page
    assert "disabled" in page
    assert "Cambiar el método o el proveedor no evita el error 409" in page


def test_static_assets_are_served_from_ui_mount(tmp_path: Path) -> None:
    client = _client(tmp_path)
    css = client.get("/ui/app.css")
    script = client.get("/ui/app.js")
    assert css.status_code == 200
    assert "text/css" in css.headers["content-type"]
    assert script.status_code == 200
    assert "javascript" in script.headers["content-type"]
    assert "@media" in css.text
    assert ":focus-visible" in css.text
    assert "@keyframes" not in css.text


def test_existing_endpoints_remain_available(tmp_path: Path) -> None:
    client = _client(tmp_path, _CountingBackend(_four()))
    health = client.get("/health")
    docs = client.get("/docs")
    schema = client.get("/openapi.json")
    extracted = client.post("/extract", json=_body())
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert docs.status_code == 200
    paths = schema.json()["paths"]
    assert "/health" in paths
    assert "/extract" in paths
    assert "/agent/extract" in paths
    assert extracted.status_code == 200
    assert set(extracted.json()["properties"]) == set(_PROPERTIES)


def test_loading_the_page_does_not_call_the_backend(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    backend = _CountingBackend(_four())
    client = _client(tmp_path, backend)
    assert client.get("/").status_code == 200
    assert client.get("/ui/app.js").status_code == 200
    assert backend.calls == 0
    script = _text("app.js")
    submit = _function_body(script, "submitExtraction")
    load = _function_body(script, "loadSaved")
    assert script.count("fetch(") == 2
    assert "fetch(" in submit
    assert 'fetch("/predictions/"' in load
    rest = script.replace(submit, "", 1).replace(load, "", 1)
    assert "fetch(" not in rest


def test_form_contract_uses_only_allowed_request_fields() -> None:
    script = _text("app.js")
    page = _text("index.html")
    rules = _rules(script)
    payload = _function_body(script, "payload")
    assert rules["requestFields"] == [
        "paper_id",
        "promoter_name",
        "promoter_id",
        "paper_gene_synonym",
        "document_format",
        "document",
        "provider",
    ]
    for field in rules["requestFields"]:
        assert field in payload
    for banned in ("gold", "max_output_tokens", "document_path", "credential"):
        assert banned not in payload
        assert banned not in page
    assert "readAsText" in script
    assert "UTF-8" in script
    identity = _function_body(script, "identityKey")
    assert "paper-id" in identity
    assert "promoter-name" in identity
    assert "provider" not in identity
    assert "method" not in identity


def test_file_suffixes_map_to_the_http_format() -> None:
    formats = _rules(_text("app.js"))["formats"]
    assert isinstance(formats, list)
    assert formats[0] == [".tei.xml", "TEI/XML"]
    detect = _function_body(_text("app.js"), "detectFormat")
    assert "UI_RULES.formats" in detect
    assert _detect("note.txt", formats) == "TXT"
    assert _detect("paper.xml", formats) == "TEI/XML"
    assert _detect("paper.TEI.XML", formats) == "TEI/XML"
    assert _detect("paper.tei", formats) == "TEI/XML"
    assert _detect("paper.pdf", formats) == ""


def test_renderer_keeps_technical_failures_out_of_scientific_status() -> None:
    script = _text("app.js")
    badge = _function_body(script, "badgeFor")
    assert 'attempt.kind === "technical"' in badge
    assert "Fallo técnico" in badge
    assert "NOT_FOUND" not in badge
    rules = _rules(script)
    assert "NOT_FOUND" in rules["scientificStatuses"]
    assert "EXTRACTED" in rules["scientificStatuses"]


def test_rejected_candidates_stay_out_of_accepted_values() -> None:
    script = _text("app.js")
    accepted = _function_body(script, "renderAccepted")
    rejected = _function_body(script, "renderRejected")
    assert "value_raw" in accepted
    assert "candidate_raw" not in accepted
    assert "candidate_raw" in rejected
    assert "value_normalized" not in rejected
    assert 'data-region="accepted"' in script
    assert 'data-region="rejected"' in script
    assert "innerHTML" not in script


def test_confirmation_and_duplicate_policy_are_in_the_page() -> None:
    script = _text("app.js")
    gate = _function_body(script, "canSubmit")
    assert "confirm-call" in gate
    assert "state.sending" in gate
    assert "persistedKey" in gate
    assert "identityKey" in gate
    assert "FILE_EXISTS" in script or "409" in script
    page = _text("index.html")
    assert page.index('id="run"') > page.index('id="confirm-call"')
    assert "disabled" in page


def test_http_limits_gold_and_secrets_stay_out_of_the_ui(tmp_path: Path) -> None:
    script = _text("app.js")
    page = _text("index.html")
    style = _text("app.css")
    rules = _rules(script)
    assert rules["maxDocumentChars"] == MAX_DOCUMENT_CHARS
    blob = "\n".join((page, style, script))
    for banned in ("https://", "http://", "sk-", "/Users/", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
        assert banned not in blob
    project = (_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    for name in ("index.html", "app.css", "app.js"):
        assert f"promoter_ai_extraction/ui/{name}" in project
    backend = _CountingBackend(_four())
    client = _client(tmp_path, backend)
    gold = client.post("/extract", json=_body(gold_value="hidden"))
    huge = client.post("/extract", json=_body(document="a" * (MAX_DOCUMENT_CHARS + 1)))
    assert gold.status_code == 422
    assert gold.json()["code"] == "INVALID_REQUEST"
    assert huge.status_code == 413
    assert huge.json()["code"] == "DOCUMENT_TOO_LARGE"
    assert backend.calls == 0


def test_server_keeps_technical_results_and_rejected_candidates_distinct(
    tmp_path: Path,
) -> None:
    rejected = RawPropertyPayload(
        status="NOT_FOUND",
        values=(),
        candidates=(
            RawCandidatePayload(
                candidate_raw="NOT-A-VALUE",
                rule_violated="ambiguous promoter association",
                evidence_segment_id="txt:p:0000",
                evidence_fragment=_PARA,
            ),
        ),
        abstention_reason="The association stayed ambiguous.",
        result_evidence=(),
    )
    backend = _CountingBackend(
        _four(
            {
                Property.TSS: BackendFailure(
                    code="INVALID_BACKEND_PAYLOAD",
                    message="mismatched evidence",
                ),
                Property.CAJA_10: rejected,
            }
        )
    )
    response = _client(tmp_path, backend).post("/extract", json=_body())
    assert response.status_code == 200
    properties = response.json()["properties"]
    tss = properties["TSS"]
    box = properties["Caja -10"]
    assert tss["kind"] == "technical"
    assert tss["code"] == "INVALID_BACKEND_PAYLOAD"
    assert "status" not in tss
    assert box["kind"] == "scientific"
    assert box["status"] == "NOT_FOUND"
    assert box["values"] == []
    assert box["candidates"][0]["candidate_raw"] == "NOT-A-VALUE"
    assert box["candidates"][0]["candidate_raw"] not in [
        item.get("value_raw") for item in box["values"]
    ]


def test_duplicate_identity_is_409_for_either_method(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    backend = _CountingBackend(_four())
    client = _client(tmp_path, backend)
    first = client.post("/extract", json=_body(provider="openai"))
    second = client.post(
        "/agent/extract",
        json=_body(provider="anthropic"),
    )
    assert first.status_code == 200
    assert second.status_code == 409
    assert second.json()["code"] == "FILE_EXISTS"
    assert backend.calls == 4
