"""HTTP contract for the Anthropic tool-use agent. Synthetic inputs only."""
from __future__ import annotations

import copy
import inspect
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from promoter_ai_extraction import agent as agent_module
from promoter_ai_extraction import baseline, application
from promoter_ai_extraction.api import create_app
from promoter_ai_extraction.backends.anthropic_backend import MODEL_ID
from promoter_ai_extraction.extraction import RawPropertyPayload, RawValuePayload, SafeExtractionInput
from promoter_ai_extraction.models import Property, ScientificStatus

_PARA = "The promoter lacZp1 TSS is -42."
_HIDDEN = "UNIQUE_NOT_IN_TOOL_RESULTS"
_REASONING = "UNIQUE_PRIVATE_REASONING"
_DOCUMENT = f"{_PARA}\n\n{_HIDDEN}\n"
_PROPERTIES = ("TSS", "Caja -10", "Caja -35", "Factor sigma")


def _extracted(value: str) -> RawPropertyPayload:
    return RawPropertyPayload(
        status="EXTRACTED",
        values=(
            RawValuePayload(
                value_raw=value,
                qualifier=None,
                evidence_segment_ids=("txt:p:0000",),
                evidence_fragments=(_PARA,),
            ),
        ),
        candidates=(),
        abstention_reason=None,
        result_evidence=(),
    )


class CountingBackend:
    def __init__(self) -> None:
        self.calls = 0
        self.seen: list[SafeExtractionInput] = []
        self._payloads = {
            Property.TSS: _extracted("-42"),
            Property.CAJA_10: _extracted("TATAAT"),
            Property.CAJA_35: _extracted("TTGACA"),
            Property.FACTOR_SIGMA: _extracted("sigma70"),
        }

    def generate(self, safe_input: SafeExtractionInput) -> RawPropertyPayload:
        self.calls += 1
        self.seen.append(safe_input)
        return self._payloads[safe_input.property]


class _IdenticalEmbedder:
    model_id = "synthetic-identical"

    def embed(self, texts: list[str]) -> list[tuple[float, ...]]:
        return [(1.0, 0.0) for _ in texts]


class ScriptedOrchestrator:
    def __init__(self, responses: list[object]) -> None:
        self._pending = list(responses)
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> object:
        self.calls.append(copy.deepcopy(kwargs))
        if not self._pending:
            raise AssertionError("unexpected orchestrator call")
        return self._pending.pop(0)


def _use(tool_id: str, name: str, payload: dict[str, object]) -> SimpleNamespace:
    return SimpleNamespace(type="tool_use", id=tool_id, name=name, input=payload)


def _response(stop_reason: str, content: list[object]) -> SimpleNamespace:
    return SimpleNamespace(stop_reason=stop_reason, content=content)


def _body(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "paper_id": "PMC12345",
        "promoter_name": "lacZp1",
        "document_format": "TXT",
        "document": _DOCUMENT,
    }
    payload.update(overrides)
    return payload


def _tool_round(prefix: str, name: str) -> list[SimpleNamespace]:
    return [
        _use(f"{prefix}-{index}", name, {"property": prop})
        for index, prop in enumerate(_PROPERTIES, start=1)
    ]


def _client(
    tmp_path: Path,
    orchestrator: object | None,
    backend: CountingBackend | None = None,
    *,
    embedder: object | None = None,
) -> tuple[TestClient, CountingBackend]:
    active = backend if backend is not None else CountingBackend()
    app = create_app(
        backend=active,
        prediction_dir=tmp_path,
        embedder=embedder if embedder is not None else _IdenticalEmbedder(),
        orchestrator=orchestrator,
    )
    return TestClient(app), active


def _stored(tmp_path: Path) -> dict[str, object]:
    files = list(tmp_path.glob("*.json"))
    assert len(files) == 1
    loaded = json.loads(files[0].read_text())
    assert isinstance(loaded, dict)
    return loaded


def test_four_properties_record_tool_ids_without_document_text(tmp_path: Path) -> None:
    orchestrator = ScriptedOrchestrator(
        [
            _response("tool_use", _tool_round("ret", "retrieve_evidence")),
            _response("tool_use", _tool_round("ext", "extract_property")),
            _response("end_turn", [SimpleNamespace(type="text", text=_REASONING)]),
        ]
    )
    client, backend = _client(tmp_path, orchestrator)
    response = client.post("/agent/extract", json=_body())
    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == "PMC12345__lacZp1"
    assert body["provider"] == "anthropic"
    assert body["model"] == "claude-sonnet-5-5"
    assert body["model"] == MODEL_ID
    assert backend.calls == 4
    assert {item.property for item in backend.seen} == set(Property)
    assert {item.paper_id for item in backend.seen} == {"PMC12345"}
    assert {item.promoter_name for item in backend.seen} == {"lacZp1"}
    for prop in _PROPERTIES:
        slot = body["properties"][prop]
        assert slot["kind"] == "scientific"
        assert slot["status"] == "EXTRACTED"
    first = orchestrator.calls[0]
    assert _PARA not in json.dumps(first, default=str)
    assert _HIDDEN not in json.dumps(first, default=str)
    assert first["model"] == "claude-sonnet-5-5"
    assert first["max_tokens"] == 1024
    assert [tool["name"] for tool in first["tools"]] == [
        "retrieve_evidence",
        "extract_property",
    ]
    results = orchestrator.calls[1]["messages"][-1]["content"]
    assert [item["tool_use_id"] for item in results] == ["ret-1", "ret-2", "ret-3", "ret-4"]
    extracted = orchestrator.calls[2]["messages"][-1]["content"]
    assert [item["tool_use_id"] for item in extracted] == ["ext-1", "ext-2", "ext-3", "ext-4"]
    retrieve = json.loads(results[0]["content"])
    assert retrieve["mode"] == "retrieved"
    assert retrieve["segment_ids"]
    assert "char_count" in retrieve
    assert _PARA not in results[0]["content"]
    assert _HIDDEN not in results[0]["content"]
    trace = body["agent"]
    assert trace["termination"] == "end_turn"
    assert trace["limits"]["max_rounds"] == 6
    assert trace["limits"]["max_tool_executions"] == 8
    assert trace["limits"]["orchestrator_max_tokens"] == 1024
    assert trace["limits"]["extraction_max_tokens"] == 4096
    assert [step["tool"] for step in trace["steps"]] == [
        "retrieve_evidence",
    ] * 4 + ["extract_property"] * 4
    stored = _stored(tmp_path)
    fingerprint = stored["system_fingerprint"]
    assert fingerprint["agent"]["steps"][0]["segment_ids"]
    blob = json.dumps(fingerprint["agent"])
    assert _PARA not in blob
    assert _HIDDEN not in blob
    assert _REASONING not in blob
    assert _REASONING not in response.text


def test_unknown_tool_is_not_executed(tmp_path: Path) -> None:
    orchestrator = ScriptedOrchestrator(
        [
            _response("tool_use", [_use("bad-1", "read_file", {"path": "/tmp/gold"})]),
            _response("end_turn", []),
        ]
    )
    client, backend = _client(tmp_path, orchestrator)
    response = client.post("/agent/extract", json=_body(paper_id="PMC-unknown"))
    assert response.status_code == 200
    assert backend.calls == 0
    assert response.json()["properties"]["TSS"]["code"] == "AGENT_SKIPPED"
    result = json.loads(orchestrator.calls[1]["messages"][-1]["content"][0]["content"])
    assert result["code"] == "UNKNOWN_TOOL"
    assert "/tmp/gold" not in response.text


def test_extra_arguments_cannot_change_identity(tmp_path: Path) -> None:
    orchestrator = ScriptedOrchestrator(
        [
            _response(
                "tool_use",
                [
                    _use(
                        "bad-1",
                        "retrieve_evidence",
                        {
                            "property": "TSS",
                            "paper_id": "evilPaper",
                            "promoter_name": "evilPromoter",
                            "path": "/tmp/gold",
                            "gold_value": "SECRET_GOLD",
                        },
                    )
                ],
            ),
            _response("end_turn", []),
        ]
    )
    client, backend = _client(tmp_path, orchestrator)
    response = client.post("/agent/extract", json=_body(paper_id="PMC-identity"))
    assert response.status_code == 200
    assert backend.calls == 0
    body = response.json()
    assert body["paper_id"] == "PMC-identity"
    assert body["promoter_name"] == "lacZp1"
    assert "evilPaper" not in response.text
    assert "SECRET_GOLD" not in response.text
    stored = json.dumps(_stored(tmp_path))
    assert "evilPaper" not in stored
    assert "evilPromoter" not in stored
    assert "SECRET_GOLD" not in stored
    echoed = orchestrator.calls[1]["messages"][-1]["content"][0]["content"]
    assert "evilPaper" not in echoed
    assert "SECRET_GOLD" not in echoed


def test_invalid_property_is_rejected(tmp_path: Path) -> None:
    orchestrator = ScriptedOrchestrator(
        [
            _response(
                "tool_use",
                [_use("bad-1", "retrieve_evidence", {"property": "gold_value"})],
            ),
            _response("end_turn", []),
        ]
    )
    client, backend = _client(tmp_path, orchestrator)
    response = client.post("/agent/extract", json=_body(paper_id="PMC-invalid"))
    assert response.status_code == 200
    assert backend.calls == 0
    result = json.loads(orchestrator.calls[1]["messages"][-1]["content"][0]["content"])
    assert result["code"] == "INVALID_PROPERTY"
    assert "gold_value" not in result["code"]
    assert "gold_value" not in json.dumps(response.json()["agent"])


def test_same_round_extract_waits_for_the_retrieval_result(tmp_path: Path) -> None:
    orchestrator = ScriptedOrchestrator(
        [
            _response(
                "tool_use",
                [
                    _use("ret-1", "retrieve_evidence", {"property": "TSS"}),
                    _use("ext-1", "extract_property", {"property": "TSS"}),
                ],
            ),
            _response(
                "tool_use",
                [_use("ext-2", "extract_property", {"property": "TSS"})],
            ),
            _response("end_turn", []),
        ]
    )
    client, backend = _client(tmp_path, orchestrator)
    response = client.post("/agent/extract", json=_body(paper_id="PMC-order"))
    assert response.status_code == 200
    assert backend.calls == 1
    delivered = orchestrator.calls[1]["messages"][-1]["content"]
    assert [item["tool_use_id"] for item in delivered] == ["ret-1", "ext-1"]
    assert json.loads(delivered[0]["content"])["mode"] == "retrieved"
    pending = json.loads(delivered[1]["content"])
    assert pending["code"] == "RETRIEVAL_RESULT_PENDING"
    assert delivered[1]["is_error"] is True
    assert _PARA not in delivered[1]["content"]
    recovered = orchestrator.calls[2]["messages"][-1]["content"]
    assert recovered[0]["tool_use_id"] == "ext-2"
    assert json.loads(recovered[0]["content"])["status"] == "EXTRACTED"
    body = response.json()
    assert body["properties"]["TSS"]["status"] == "EXTRACTED"
    for prop in ("Caja -10", "Caja -35", "Factor sigma"):
        assert body["properties"][prop]["code"] == "AGENT_SKIPPED"


def test_extract_without_retrieval_does_not_call_the_extractor(tmp_path: Path) -> None:
    orchestrator = ScriptedOrchestrator(
        [
            _response(
                "tool_use",
                [_use("ext-1", "extract_property", {"property": "TSS"})],
            ),
            _response("end_turn", []),
        ]
    )
    client, backend = _client(tmp_path, orchestrator)
    response = client.post("/agent/extract", json=_body(paper_id="PMC-noretrieve"))
    assert response.status_code == 200
    assert backend.calls == 0
    slot = response.json()["properties"]["TSS"]
    assert slot["kind"] == "technical"
    assert slot["code"] == "AGENT_SKIPPED"
    assert "status" not in slot


def test_insufficient_retrieval_is_not_a_scientific_abstention(tmp_path: Path) -> None:
    from promoter_ai_extraction.retrieval import MAX_RETRIEVED_CHARS

    orchestrator = ScriptedOrchestrator(
        [
            _response(
                "tool_use",
                [
                    _use("ret-1", "retrieve_evidence", {"property": "TSS"}),
                    _use("ext-1", "extract_property", {"property": "TSS"}),
                ],
            ),
            _response("end_turn", []),
        ]
    )
    client, backend = _client(tmp_path, orchestrator)
    huge = "x" * (MAX_RETRIEVED_CHARS + 1)
    response = client.post(
        "/agent/extract",
        json=_body(paper_id="PMC-budget", document=huge),
    )
    assert response.status_code == 200
    assert backend.calls == 0
    slot = response.json()["properties"]["TSS"]
    assert slot["kind"] == "technical"
    assert slot["code"] == "INSUFFICIENT_RETRIEVAL"
    assert slot["code"] not in {status.value for status in ScientificStatus}
    assert "status" not in slot


def test_finish_while_retrieval_is_unseen_marks_the_property_skipped(tmp_path: Path) -> None:
    orchestrator = ScriptedOrchestrator(
        [
            _response(
                "tool_use",
                [
                    _use("ret-1", "retrieve_evidence", {"property": "TSS"}),
                    _use("ext-1", "extract_property", {"property": "TSS"}),
                ],
            ),
            _response("end_turn", []),
        ]
    )
    client, backend = _client(tmp_path, orchestrator)
    response = client.post("/agent/extract", json=_body(paper_id="PMC-unseen"))
    assert response.status_code == 200
    assert backend.calls == 0
    assert response.json()["properties"]["TSS"]["code"] == "AGENT_SKIPPED"
    pending = json.loads(orchestrator.calls[1]["messages"][-1]["content"][1]["content"])
    assert pending["code"] == "RETRIEVAL_RESULT_PENDING"


def test_early_stop_marks_pending_properties_skipped(tmp_path: Path) -> None:
    orchestrator = ScriptedOrchestrator(
        [
            _response(
                "tool_use",
                [_use("ret-1", "retrieve_evidence", {"property": "TSS"})],
            ),
            _response(
                "tool_use",
                [_use("ext-1", "extract_property", {"property": "TSS"})],
            ),
            _response("end_turn", []),
        ]
    )
    client, backend = _client(tmp_path, orchestrator)
    response = client.post("/agent/extract", json=_body(paper_id="PMC-skip"))
    assert response.status_code == 200
    assert backend.calls == 1
    body = response.json()
    assert body["properties"]["TSS"]["status"] == "EXTRACTED"
    for prop in ("Caja -10", "Caja -35", "Factor sigma"):
        slot = body["properties"][prop]
        assert slot["code"] == "AGENT_SKIPPED"
        assert "status" not in slot
    assert body["agent"]["termination"] == "end_turn"


def test_tool_limit_stops_before_the_ninth_execution(tmp_path: Path) -> None:
    blocks = [
        _use(f"ret-{index}", "retrieve_evidence", {"property": "TSS"}) for index in range(1, 10)
    ]
    orchestrator = ScriptedOrchestrator([_response("tool_use", blocks), _response("end_turn", [])])
    client, backend = _client(tmp_path, orchestrator)
    response = client.post("/agent/extract", json=_body(paper_id="PMC-limit"))
    assert response.status_code == 200
    assert backend.calls == 0
    assert len(orchestrator.calls) == 1
    body = response.json()
    assert body["agent"]["termination"] == "tool_limit"
    assert len(body["agent"]["steps"]) == 8
    assert body["properties"]["TSS"]["code"] == "AGENT_STEP_LIMIT"
    assert "status" not in body["properties"]["TSS"]


def test_round_limit_does_not_request_a_seventh_turn(tmp_path: Path) -> None:
    responses = [
        _response("tool_use", [_use(f"ret-{index}", "retrieve_evidence", {"property": "TSS"})])
        for index in range(1, 8)
    ]
    orchestrator = ScriptedOrchestrator(responses)
    client, backend = _client(tmp_path, orchestrator)
    response = client.post("/agent/extract", json=_body(paper_id="PMC-rounds"))
    assert response.status_code == 200
    assert backend.calls == 0
    assert len(orchestrator.calls) == 6
    assert response.json()["agent"]["termination"] == "round_limit"
    assert response.json()["properties"]["Caja -10"]["code"] == "AGENT_STEP_LIMIT"


def test_orchestrator_error_is_not_a_scientific_status(tmp_path: Path) -> None:
    orchestrator = ScriptedOrchestrator([_response("max_tokens", [])])
    client, backend = _client(tmp_path, orchestrator)
    response = client.post("/agent/extract", json=_body(paper_id="PMC-orch"))
    assert response.status_code == 200
    assert backend.calls == 0
    slot = response.json()["properties"]["TSS"]
    assert slot["code"] == "ORCHESTRATOR_ERROR"
    assert slot["code"] not in {status.value for status in ScientificStatus}


def test_missing_credential_does_not_save_or_call(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client, backend = _client(tmp_path, orchestrator=None, backend=None)
    response = client.post("/agent/extract", json=_body(paper_id="PMC-key"))
    assert response.status_code == 503
    assert response.json()["code"] == "MISSING_CREDENTIAL"
    assert backend.calls == 0
    assert list(tmp_path.glob("*.json")) == []


def test_existing_prediction_is_409_before_the_orchestrator(tmp_path: Path) -> None:
    class _Boom:
        def create(self, **kwargs: object) -> object:
            raise AssertionError("orchestrator was called")

    backend = CountingBackend()
    client, _ = _client(tmp_path, _Boom(), backend)
    first = client.post("/extract", json=_body(paper_id="PMC-shared"))
    assert first.status_code == 200
    assert backend.calls == 4
    second = client.post("/agent/extract", json=_body(paper_id="PMC-shared"))
    assert second.status_code == 409
    assert second.json()["code"] == "FILE_EXISTS"
    assert backend.calls == 4
    assert len(list(tmp_path.glob("*.json"))) == 1


def test_gold_fields_are_rejected_before_the_orchestrator(tmp_path: Path) -> None:
    class _Boom:
        def create(self, **kwargs: object) -> object:
            raise AssertionError("orchestrator was called")

    client, backend = _client(tmp_path, _Boom())
    response = client.post(
        "/agent/extract",
        json=_body(gold_value="SECRET_GOLD", document_path="/tmp/gold"),
    )
    assert response.status_code == 422
    assert backend.calls == 0
    assert "SECRET_GOLD" not in response.text
    assert list(tmp_path.glob("*.json")) == []


def test_extract_route_does_not_call_the_orchestrator(tmp_path: Path) -> None:
    class _Boom:
        def create(self, **kwargs: object) -> object:
            raise AssertionError("orchestrator was called")

    client, backend = _client(tmp_path, _Boom())
    response = client.post("/extract", json=_body(paper_id="PMC-plain"))
    assert response.status_code == 200
    assert "retrieval" in response.json()
    assert backend.calls == 4


def test_openai_provider_and_oversized_limits_do_not_call(tmp_path: Path) -> None:
    class _Boom:
        def create(self, **kwargs: object) -> object:
            raise AssertionError("orchestrator was called")

    client, backend = _client(tmp_path, _Boom())
    openai = client.post("/agent/extract", json=_body(provider="openai"))
    assert openai.status_code == 422
    oversized = client.post("/agent/extract", json=_body(max_output_tokens=128000))
    assert oversized.status_code == 422
    huge = client.post("/agent/extract", json=_body(document="x" * 100_001))
    assert huge.status_code == 413
    assert backend.calls == 0
    assert list(tmp_path.glob("*.json")) == []


def test_live_extractor_receives_the_http_output_cap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: dict[str, int] = {}

    class _FakeBackend:
        def __init__(self, *, max_output_tokens: int) -> None:
            seen["max_output_tokens"] = max_output_tokens

        def generate(self, safe_input: SafeExtractionInput) -> RawPropertyPayload:
            return _extracted("-42")

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-not-a-real-key")
    monkeypatch.setattr(
        "promoter_ai_extraction.api.AnthropicModelBackend",
        _FakeBackend,
    )
    orchestrator = ScriptedOrchestrator(
        [
            _response(
                "tool_use",
                [
                    _use("ret-1", "retrieve_evidence", {"property": "TSS"}),
                    _use("ext-1", "extract_property", {"property": "TSS"}),
                ],
            ),
            _response("end_turn", []),
        ]
    )
    app = create_app(
        backend=None,
        prediction_dir=tmp_path,
        embedder=_IdenticalEmbedder(),
        orchestrator=orchestrator,
    )
    omitted = TestClient(app).post("/agent/extract", json=_body(paper_id="PMC-cap"))
    assert omitted.status_code == 200
    assert seen["max_output_tokens"] == 4096


def test_agent_source_has_no_gold_or_general_framework() -> None:
    source = inspect.getsource(agent_module)
    assert "gold_loader" not in source
    assert "EvaluationService" not in source
    assert "langchain" not in source.lower()
    assert "GuidedExtractionService" not in source
    for module in (baseline, application):
        text = Path(module.__file__).read_text(encoding="utf-8")
        assert "promoter_ai_extraction.agent" not in text


def test_live_orchestrator_disables_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, object] = {}

    class _FakeAnthropic:
        def __init__(self, *, api_key: str, max_retries: int) -> None:
            seen["api_key"] = api_key
            seen["max_retries"] = max_retries

        @property
        def messages(self) -> str:
            return "messages-handle"

    import anthropic

    monkeypatch.setattr(anthropic, "Anthropic", _FakeAnthropic)
    assert agent_module.build_orchestrator("test-not-a-real-key") == "messages-handle"
    assert seen == {"api_key": "test-not-a-real-key", "max_retries": 0}
