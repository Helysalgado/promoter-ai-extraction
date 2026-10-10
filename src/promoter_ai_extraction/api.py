"""Minimal synchronous HTTP API over the guided extractor.

The client sends document text. It does not send a filesystem path, a
credential, a gold field, or a prediction directory. Evaluation is not
exposed here.
"""
from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from promoter_ai_extraction import __version__
from promoter_ai_extraction.backends import AnthropicModelBackend, OpenAIModelBackend
from promoter_ai_extraction.backends.anthropic_backend import MODEL_ID as ANTHROPIC_MODEL_ID
from promoter_ai_extraction.backends.openai_backend import MODEL_ID as OPENAI_MODEL_ID
from promoter_ai_extraction.boundary import ExtractionRequestFactory
from promoter_ai_extraction.documents import DocumentLoader, DocumentSource
from promoter_ai_extraction.extraction import (
    GuidedExtractionService,
    ModelBackend,
    PropertyExtractor,
)
from promoter_ai_extraction.models import (
    EvidenceItem,
    ExtractedValue,
    ExtractionRun,
    PropertyResult,
    RejectedCandidate,
    TechnicalFailure,
)
from promoter_ai_extraction.persistence import PersistenceFailure, PredictionStore
from promoter_ai_extraction.validation import OutputValidator

MAX_DOCUMENT_CHARS = 100_000
HTTP_MAX_OUTPUT_TOKENS = 4_096

_LOAD_MESSAGES = {
    "EMPTY_DOCUMENT": "The document is empty.",
    "MALFORMED_XML": "The TEI/XML document is not well formed.",
    "DECODING_ERROR": "The document is not valid UTF-8.",
    "UNSAFE_XML": "The document contains a disallowed XML construct.",
    "NO_TEXTUAL_CONTENT": "The document has no extractable text.",
    "INVALID_SOURCE": "The document source is invalid.",
}


class ExtractRequest(BaseModel):
    """Closed extract body. Unknown keys are rejected."""

    model_config = ConfigDict(extra="forbid")

    paper_id: str
    promoter_name: str
    promoter_id: str | None = None
    paper_gene_synonym: str | None = None
    document_format: Literal["TXT", "TEI/XML"]
    document: str
    provider: Literal["openai", "anthropic"] = "openai"
    max_output_tokens: int | None = Field(default=None)

    @field_validator("paper_id", "promoter_name")
    @classmethod
    def _required_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must be non-empty")
        return stripped

    @field_validator("promoter_id", "paper_gene_synonym")
    @classmethod
    def _optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


def create_app(
    *,
    backend: ModelBackend | None = None,
    prediction_dir: Path | None = None,
) -> FastAPI:
    """Build the app. An injected backend is for tests and skips credentials."""
    app = FastAPI(title="promoter-ai-extraction", version=__version__)
    app.state.backend = backend
    app.state.store = PredictionStore(
        prediction_dir or Path(os.environ.get("PREDICTION_DIR", "runs/http"))
    )
    app.state.guard = threading.Lock()
    app.state.locks = {}

    @app.exception_handler(RequestValidationError)
    async def reject_invalid(request: Request, exc: RequestValidationError) -> JSONResponse:
        fields = [_field_name(err.get("loc", ())) for err in exc.errors()]
        return _error(422, "INVALID_REQUEST", "The request was rejected.", fields=fields)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "software_version": __version__}

    @app.post("/extract")
    def extract(body: ExtractRequest, request: Request) -> JSONResponse:
        if len(body.document) > MAX_DOCUMENT_CHARS:
            return _error(
                413,
                "DOCUMENT_TOO_LARGE",
                "The document exceeds the server size limit.",
            )
        if body.max_output_tokens is not None and not 1 <= body.max_output_tokens <= HTTP_MAX_OUTPUT_TOKENS:
            return _error(
                422,
                "LIMIT_EXCEEDED",
                "max_output_tokens must be an integer from 1 to 4096.",
            )

        run_id = f"{body.paper_id}__{body.promoter_name}"
        store: PredictionStore = request.app.state.store
        with _lock_for(request.app, run_id):
            if store.exists(run_id):
                return _conflict()
            active = request.app.state.backend
            model_id: str | None = None
            if active is None:
                built = _live_backend(body.provider, body.max_output_tokens)
                if isinstance(built, JSONResponse):
                    return built
                active = built
                model_id = OPENAI_MODEL_ID if body.provider == "openai" else ANTHROPIC_MODEL_ID
            loaded = DocumentLoader().load(
                DocumentSource(
                    paper_id=body.paper_id,
                    path=None,
                    content=body.document,
                    format=body.document_format,
                )
            )
            if isinstance(loaded, TechnicalFailure):
                return _error(
                    422,
                    loaded.code,
                    _LOAD_MESSAGES.get(loaded.code, "The document could not be read."),
                )
            service = GuidedExtractionService(
                PropertyExtractor(backend=active, validator=OutputValidator()),
                ExtractionRequestFactory(),
            )
            run = service.run(
                loaded,
                body.promoter_name,
                promoter_id=body.promoter_id,
                paper_gene_synonym=body.paper_gene_synonym,
                run_id=run_id,
            )
            saved = store.save(run, document_hash=loaded.document_hash)
            if isinstance(saved, PersistenceFailure):
                if saved.code == "FILE_EXISTS":
                    return _conflict()
                return _error(500, "WRITE_ERROR", "The prediction could not be stored.")
        return JSONResponse(
            status_code=200,
            content=_public_run(run, provider=body.provider, model=model_id),
        )

    return app


def _live_backend(provider: str, max_output_tokens: int | None) -> ModelBackend | JSONResponse:
    """Construct one provider. There is no fallback to the other.

    The HTTP cap is 4096 for both providers, including when the client omits
    the field. CLI defaults stay in the backend modules.
    """
    cap = HTTP_MAX_OUTPUT_TOKENS if max_output_tokens is None else max_output_tokens
    if provider == "anthropic":
        if not (os.environ.get("ANTHROPIC_API_KEY") or "").strip():
            return _error(503, "MISSING_CREDENTIAL", "ANTHROPIC_API_KEY is not set.")
        return AnthropicModelBackend(max_output_tokens=cap)
    if not (os.environ.get("OPENAI_API_KEY") or "").strip():
        return _error(503, "MISSING_CREDENTIAL", "OPENAI_API_KEY is not set.")
    return OpenAIModelBackend(max_output_tokens=cap)


def _lock_for(app: FastAPI, run_id: str) -> threading.Lock:
    guard: threading.Lock = app.state.guard
    with guard:
        lock = app.state.locks.get(run_id)
        if lock is None:
            lock = threading.Lock()
            app.state.locks[run_id] = lock
        return lock


def _public_run(run: ExtractionRun, *, provider: str, model: str | None) -> dict[str, object]:
    return {
        "run_id": run.run_id,
        "paper_id": run.paper_id,
        "promoter_name": run.promoter_name,
        "provider": provider,
        "model": model,
        "properties": {
            "TSS": _public_attempt(run.tss),
            "Caja -10": _public_attempt(run.caja_10),
            "Caja -35": _public_attempt(run.caja_35),
            "Factor sigma": _public_attempt(run.sigma),
        },
    }


def _public_attempt(attempt: PropertyResult | TechnicalFailure) -> dict[str, object]:
    if isinstance(attempt, TechnicalFailure):
        return {
            "kind": "technical",
            "stage": attempt.stage,
            "code": attempt.code,
            "message": _safe_text(attempt.message),
        }
    return {
        "kind": "scientific",
        "status": attempt.status.value,
        "abstention_reason": attempt.abstention_reason,
        "values": [_public_value(value) for value in attempt.values],
        "candidates": [_public_candidate(item) for item in attempt.candidate_values],
        "evidence": [_public_evidence(item) for item in attempt.evidence],
    }


def _public_value(value: ExtractedValue) -> dict[str, object]:
    return {
        "value_raw": value.value_raw,
        "value_normalized": value.value_normalized,
        "qualifier": value.qualifier,
        "derivation_note": value.derivation_note,
        "evidence": [_public_evidence(item) for item in value.evidence],
    }


def _public_candidate(candidate: RejectedCandidate) -> dict[str, object]:
    return {
        "candidate_raw": candidate.candidate_raw,
        "rejection_reason": candidate.rejection_reason.value,
        "rule_violated": candidate.rule_violated,
        "evidence": None
        if candidate.evidence is None
        else _public_evidence(candidate.evidence),
    }


def _public_evidence(item: EvidenceItem) -> dict[str, object]:
    return {
        "segment_id": item.segment_id,
        "source_type": item.source_type,
        "location": item.location,
        "fragment": item.fragment,
    }


def _safe_text(message: str) -> str:
    if "sk-" in message:
        return "The request could not be completed."
    return message


def _conflict() -> JSONResponse:
    return _error(
        409,
        "FILE_EXISTS",
        "A prediction for this paper and promoter already exists.",
    )


def _error(
    status_code: int,
    code: str,
    message: str,
    *,
    fields: list[str] | None = None,
) -> JSONResponse:
    body: dict[str, object] = {"code": code, "message": message}
    if fields is not None:
        body["fields"] = fields
    return JSONResponse(status_code=status_code, content=body)


def _field_name(loc: object) -> str:
    if not isinstance(loc, tuple):
        return "body"
    parts = [str(part) for part in loc if part != "body"]
    return ".".join(parts) if parts else "body"


app = create_app()
