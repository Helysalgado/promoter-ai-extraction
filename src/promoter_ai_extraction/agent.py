"""Bounded Anthropic tool loop for one paper × promoter.

The orchestrator may call only retrieve_evidence and extract_property.
Scientific status still comes from PropertyExtractor and OutputValidator.
This module does not read gold, credentials, or the filesystem.
"""
from __future__ import annotations

import json
from typing import Any, Protocol

from promoter_ai_extraction.backends.anthropic_backend import MODEL_ID
from promoter_ai_extraction.boundary import BoundaryViolation, ExtractionRequestFactory
from promoter_ai_extraction.documents import DocumentSegment, LoadedDocument
from promoter_ai_extraction.extraction import PropertyExtractor
from promoter_ai_extraction.models import (
    ExtractionRun,
    Property,
    PropertyAttempt,
    TechnicalFailure,
)
from promoter_ai_extraction.retrieval import DocumentRetrieval

MAX_ROUNDS = 6
MAX_TOOL_EXECUTIONS = 8
ORCHESTRATOR_MAX_TOKENS = 1024
_PROVIDER = "anthropic"
_RETRIEVE = "retrieve_evidence"
_EXTRACT = "extract_property"
_ALLOWED_TOOLS = frozenset({_RETRIEVE, _EXTRACT})
_PROPERTIES: tuple[Property, ...] = (
    Property.TSS,
    Property.CAJA_10,
    Property.CAJA_35,
    Property.FACTOR_SIGMA,
)
_PROPERTY_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "property": {
            "type": "string",
            "enum": [prop.value for prop in _PROPERTIES],
        }
    },
    "required": ["property"],
    "additionalProperties": False,
}
_TOOLS: tuple[dict[str, object], ...] = (
    {
        "name": _RETRIEVE,
        "description": (
            "Return segment identifiers, scores, and context size for one "
            "promoter property. The response contains no document text."
        ),
        "input_schema": _PROPERTY_SCHEMA,
    },
    {
        "name": _EXTRACT,
        "description": (
            "Extract one property from segments already retrieved in this run. "
            "The response contains a status or technical code and evidence ids."
        ),
        "input_schema": _PROPERTY_SCHEMA,
    },
)
_TASK = (
    "Extract the four promoter properties TSS, Caja -10, Caja -35, and "
    "Factor sigma. For each property call retrieve_evidence, then "
    "extract_property. The server fixes the paper and the promoter. "
    "Call no other tool."
)
_SLOT_MESSAGES = {
    "AGENT_SKIPPED": "The agent finished without extracting this property.",
    "AGENT_STEP_LIMIT": "The agent reached the execution limit before extracting this property.",
    "ORCHESTRATOR_ERROR": "The orchestrator stopped because of a technical error.",
}


class OrchestratorClient(Protocol):
    """Messages handle. Production uses Anthropic with retries disabled."""

    def create(self, **kwargs: Any) -> Any:
        """Send one orchestration turn."""
        ...


def build_orchestrator(secret: str) -> Any:
    """Build the live Messages handle. Retries stay at zero. No fallback."""
    from anthropic import Anthropic

    return Anthropic(api_key=secret, max_retries=0).messages


def run_agent(
    *,
    document: LoadedDocument,
    retrieval: DocumentRetrieval,
    extractor: PropertyExtractor,
    factory: ExtractionRequestFactory,
    orchestrator: OrchestratorClient,
    promoter_name: str,
    promoter_id: str | None,
    paper_gene_synonym: str | None,
    run_id: str,
    extraction_max_tokens: int,
) -> tuple[ExtractionRun, dict[str, object]]:
    """Run the tool loop and return the four-slot run plus its trace."""
    loop = _ToolLoop(
        document=document,
        retrieval=retrieval,
        extractor=extractor,
        factory=factory,
        orchestrator=orchestrator,
        promoter_name=promoter_name,
        promoter_id=promoter_id,
        paper_gene_synonym=paper_gene_synonym,
        run_id=run_id,
        extraction_max_tokens=extraction_max_tokens,
    )
    return loop.run()


class _ToolLoop:
    def __init__(
        self,
        *,
        document: LoadedDocument,
        retrieval: DocumentRetrieval,
        extractor: PropertyExtractor,
        factory: ExtractionRequestFactory,
        orchestrator: OrchestratorClient,
        promoter_name: str,
        promoter_id: str | None,
        paper_gene_synonym: str | None,
        run_id: str,
        extraction_max_tokens: int,
    ) -> None:
        self._document = document
        self._retrieval = retrieval
        self._extractor = extractor
        self._factory = factory
        self._orchestrator = orchestrator
        self._promoter_name = promoter_name
        self._promoter_id = promoter_id
        self._synonym = paper_gene_synonym
        self._run_id = run_id
        self._extraction_max_tokens = extraction_max_tokens
        self._attempts: dict[Property, PropertyAttempt] = {}
        self._retrieved: dict[Property, tuple[DocumentSegment, ...]] = {}
        self._released: set[Property] = set()
        self._awaiting_release: set[Property] = set()
        self._steps: list[dict[str, object]] = []
        self._rounds = 0
        self._executions = 0
        self._termination = "round_limit"
        self._messages: list[dict[str, object]] = [{"role": "user", "content": _TASK}]

    def run(self) -> tuple[ExtractionRun, dict[str, object]]:
        while self._rounds < MAX_ROUNDS:
            self._rounds += 1
            try:
                response = self._orchestrator.create(
                    model=MODEL_ID,
                    max_tokens=ORCHESTRATOR_MAX_TOKENS,
                    tools=list(_TOOLS),
                    messages=self._messages,
                )
            except Exception as exc:
                self._termination = "orchestrator_error"
                self._fill("ORCHESTRATOR_ERROR", cause=type(exc).__name__)
                break
            if not self._consume(response):
                break
        else:
            self._termination = "round_limit"
            self._fill("AGENT_STEP_LIMIT", cause="AGENT_STEP_LIMIT")
        return self._run(), self._trace()

    def _consume(self, response: object) -> bool:
        stop = _field(response, "stop_reason")
        if stop == "end_turn":
            self._termination = "end_turn"
            self._fill("AGENT_SKIPPED", cause="AGENT_SKIPPED")
            return False
        if stop != "tool_use":
            self._termination = "orchestrator_error"
            self._fill("ORCHESTRATOR_ERROR", cause="ORCHESTRATOR_ERROR")
            return False
        blocks = [
            block
            for block in _content(response)
            if _field(block, "type") == "tool_use"
        ]
        if not blocks:
            self._termination = "orchestrator_error"
            self._fill("ORCHESTRATOR_ERROR", cause="ORCHESTRATOR_ERROR")
            return False
        results: list[dict[str, object]] = []
        for block in blocks:
            if self._executions >= MAX_TOOL_EXECUTIONS:
                self._termination = "tool_limit"
                self._fill("AGENT_STEP_LIMIT", cause="AGENT_STEP_LIMIT")
                return False
            self._executions += 1
            results.append(self._dispatch(block))
        self._messages.append({"role": "assistant", "content": _content(response)})
        self._messages.append({"role": "user", "content": results})
        self._released.update(self._awaiting_release)
        self._awaiting_release.clear()
        return True

    def _dispatch(self, block: object) -> dict[str, object]:
        name = _field(block, "name")
        tool_id = _field(block, "id")
        if not isinstance(tool_id, str) or not tool_id:
            tool_id = "missing-tool-id"
        if name not in _ALLOWED_TOOLS:
            self._remember(_safe_tool_name(name), None, [], "UNKNOWN_TOOL")
            return _tool_result(tool_id, {"kind": "rejected", "code": "UNKNOWN_TOOL"}, error=True)
        prop, code = _arguments(_field(block, "input"))
        if code is not None or prop is None:
            self._remember(str(name), prop, [], code or "REJECTED_ARGUMENTS")
            return _tool_result(
                tool_id,
                {"kind": "rejected", "code": code or "REJECTED_ARGUMENTS"},
                error=True,
            )
        if name == _RETRIEVE:
            payload = self._retrieve(prop)
            return _tool_result(tool_id, payload, error=payload.get("kind") == "rejected")
        return self._extract(tool_id, prop)

    def _retrieve(self, prop: Property) -> dict[str, object]:
        if prop in self._attempts:
            self._remember(_RETRIEVE, prop, [], "ALREADY_COMPLETE")
            return {"kind": "rejected", "code": "ALREADY_COMPLETE"}
        self._awaiting_release.add(prop)
        selected = self._retrieval.context_for(
            self._document,
            prop,
            promoter_name=self._promoter_name,
            paper_gene_synonym=self._synonym,
        )
        if isinstance(selected, TechnicalFailure):
            self._attempts[prop] = selected
            mode = "insufficient" if selected.code == "INSUFFICIENT_RETRIEVAL" else "error"
            self._steps.append(
                {
                    "tool": _RETRIEVE,
                    "property": prop.value,
                    "segment_ids": [],
                    "result": {"kind": "technical", "code": selected.code, "mode": mode},
                }
            )
            return {
                "kind": "technical",
                "code": selected.code,
                "mode": mode,
                "segment_ids": [],
                "scores": [],
                "char_count": 0,
            }
        self._retrieved[prop] = selected
        properties = self._retrieval.public_trace()["properties"]
        detail = properties[prop.value] if isinstance(properties, dict) else None
        if not isinstance(detail, dict):
            failure = TechnicalFailure(
                stage="retrieval",
                code="RETRIEVAL_ERROR",
                message="The retrieval trace could not be read.",
                cause="TraceShape",
            )
            self._attempts[prop] = failure
            self._retrieved.pop(prop, None)
            self._steps.append(
                {
                    "tool": _RETRIEVE,
                    "property": prop.value,
                    "segment_ids": [],
                    "result": {"kind": "technical", "code": failure.code, "mode": "error"},
                }
            )
            return {
                "kind": "technical",
                "code": failure.code,
                "mode": "error",
                "segment_ids": [],
                "scores": [],
                "char_count": 0,
            }
        segment_ids = [str(item) for item in detail["segment_ids"]]
        scores = detail["scores"]
        payload = {
            "mode": "retrieved",
            "segment_ids": segment_ids,
            "scores": scores,
            "char_count": sum(len(segment.text) for segment in selected),
        }
        self._steps.append(
            {
                "tool": _RETRIEVE,
                "property": prop.value,
                "segment_ids": segment_ids,
                "result": payload,
            }
        )
        return payload

    def _extract(self, tool_id: str, prop: Property) -> dict[str, object]:
        if prop not in self._released:
            seen = prop in self._awaiting_release or prop in self._retrieved or prop in self._attempts
            code = "RETRIEVAL_RESULT_PENDING" if seen else "NO_PRIOR_RETRIEVAL"
            payload: dict[str, object] = {"kind": "rejected", "code": code}
            if seen:
                payload["message"] = (
                    "The retrieval result for this property has not been "
                    "returned to the orchestrator yet."
                )
            self._remember(_EXTRACT, prop, [], code)
            return _tool_result(tool_id, payload, error=True)
        if prop in self._attempts or prop not in self._retrieved:
            code = "ALREADY_COMPLETE" if prop in self._attempts else "NO_PRIOR_RETRIEVAL"
            self._remember(_EXTRACT, prop, [], code)
            return _tool_result(tool_id, {"kind": "rejected", "code": code}, error=True)
        attempt = self._extract_selected(prop, self._retrieved[prop])
        self._attempts[prop] = attempt
        segment_ids = _attempt_segment_ids(attempt)
        if isinstance(attempt, TechnicalFailure):
            result: dict[str, object] = {"kind": "technical", "code": attempt.code}
        else:
            result = {"kind": "scientific", "status": attempt.status.value}
        self._steps.append(
            {
                "tool": _EXTRACT,
                "property": prop.value,
                "segment_ids": segment_ids,
                "result": result,
            }
        )
        return _tool_result(
            tool_id,
            {**result, "segment_ids": segment_ids},
            error=False,
        )

    def _extract_selected(
        self, prop: Property, segments: tuple[DocumentSegment, ...]
    ) -> PropertyAttempt:
        view = LoadedDocument(
            paper_id=self._document.paper_id,
            format=self._document.format,
            segments=segments,
            document_hash=self._document.document_hash,
        )
        try:
            request = self._factory.create(
                {
                    "document": view,
                    "paper_id": self._document.paper_id,
                    "promoter_name": self._promoter_name,
                    "promoter_id": self._promoter_id,
                    "paper_gene_synonym": self._synonym,
                    "property": prop,
                }
            )
        except BoundaryViolation:
            return TechnicalFailure(
                stage="extraction",
                code="REQUEST_BUILD_ERROR",
                message="The extraction request could not be built.",
                cause="BoundaryViolation",
            )
        return self._extractor.extract(request)

    def _remember(
        self, tool: str, prop: Property | None, segment_ids: list[str], code: str
    ) -> None:
        self._steps.append(
            {
                "tool": tool,
                "property": None if prop is None else prop.value,
                "segment_ids": segment_ids,
                "result": {"kind": "rejected", "code": code},
            }
        )

    def _fill(self, code: str, *, cause: str) -> None:
        for prop in _PROPERTIES:
            if prop in self._attempts:
                continue
            self._attempts[prop] = TechnicalFailure(
                stage="agent",
                code=code,
                message=_SLOT_MESSAGES[code],
                cause=cause,
            )

    def _run(self) -> ExtractionRun:
        return ExtractionRun(
            run_id=self._run_id,
            paper_id=self._document.paper_id,
            promoter_name=self._promoter_name,
            tss=self._attempts[Property.TSS],
            caja_10=self._attempts[Property.CAJA_10],
            caja_35=self._attempts[Property.CAJA_35],
            sigma=self._attempts[Property.FACTOR_SIGMA],
        )

    def _trace(self) -> dict[str, object]:
        return {
            "provider": _PROVIDER,
            "model": MODEL_ID,
            "termination": self._termination,
            "rounds": self._rounds,
            "tool_executions": self._executions,
            "limits": {
                "max_rounds": MAX_ROUNDS,
                "max_tool_executions": MAX_TOOL_EXECUTIONS,
                "orchestrator_max_tokens": ORCHESTRATOR_MAX_TOKENS,
                "extraction_max_tokens": self._extraction_max_tokens,
                "max_retries": 0,
            },
            "steps": self._steps,
        }


def _arguments(raw: object) -> tuple[Property | None, str | None]:
    if not isinstance(raw, dict) or set(raw) != {"property"}:
        return None, "REJECTED_ARGUMENTS"
    prop = raw.get("property")
    if not isinstance(prop, str):
        return None, "INVALID_PROPERTY"
    try:
        return Property(prop), None
    except ValueError:
        return None, "INVALID_PROPERTY"


def _attempt_segment_ids(attempt: PropertyAttempt) -> list[str]:
    if isinstance(attempt, TechnicalFailure):
        return []
    seen: list[str] = []
    for value in attempt.values:
        for item in value.evidence:
            if item.segment_id not in seen:
                seen.append(item.segment_id)
    for item in attempt.evidence:
        if item.segment_id not in seen:
            seen.append(item.segment_id)
    return seen


def _safe_tool_name(name: object) -> str:
    if isinstance(name, str) and name.isidentifier() and len(name) <= 64:
        return name
    return "rejected"


def _tool_result(tool_id: str, payload: dict[str, object], *, error: bool) -> dict[str, object]:
    return {
        "type": "tool_result",
        "tool_use_id": tool_id,
        "content": json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        "is_error": error,
    }


def _content(response: object) -> list[object]:
    content = _field(response, "content")
    if isinstance(content, list):
        return content
    return []


def _field(obj: object, name: str) -> object:
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)
