"""In-memory retrieval over one supplied document.

The index lives only for that document. It is built from segment text.
Gold fields, curator values, and expected predictions are not inputs.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Protocol

from promoter_ai_extraction.documents import DocumentSegment, LoadedDocument
from promoter_ai_extraction.models import Property, TechnicalFailure

MAX_RETRIEVED_CHARS = 12_000
SEMANTIC_TOP_K = 8
NEIGHBOR_RADIUS = 1
EMBEDDING_WINDOW_CHARS = 1_200
EMBEDDING_WINDOW_OVERLAP = 200
EMBEDDING_MODEL_ID = "BAAI/bge-small-en-v1.5"

PROPERTY_QUERY_PHRASES: dict[Property, str] = {
    Property.TSS: "transcription start site of this promoter",
    Property.CAJA_10: "minus 10 box of this promoter",
    Property.CAJA_35: "minus 35 box of this promoter",
    Property.FACTOR_SIGMA: "sigma factor of this promoter",
}

_PROPERTY_ORDER: tuple[Property, ...] = (
    Property.TSS,
    Property.CAJA_10,
    Property.CAJA_35,
    Property.FACTOR_SIGMA,
)


class EmbedderUnavailable(Exception):
    """The local embedding model could not be loaded or executed."""


class RetrievalFailure(Exception):
    """Indexing failed for a reason other than model availability."""


class Embedder(Protocol):
    """One batch of texts in, one vector per text out."""

    def embed(self, texts: list[str]) -> list[tuple[float, ...]]:
        """Return one numeric vector for each text, in the same order."""
        ...


class FastEmbedEmbedder:
    """Local embedder. The model is loaded on the first call, not at import."""

    def __init__(self, model_id: str = EMBEDDING_MODEL_ID) -> None:
        self.model_id = model_id
        self._model: object | None = None

    def embed(self, texts: list[str]) -> list[tuple[float, ...]]:
        if not texts:
            return []
        model = self._load()
        try:
            raw = list(model.embed(texts))  # type: ignore[attr-defined]
        except Exception as exc:
            raise EmbedderUnavailable("The embedding model is not available.") from exc
        if len(raw) != len(texts):
            raise RetrievalFailure("The embedder returned an unexpected number of vectors.")
        vectors: list[tuple[float, ...]] = []
        for item in raw:
            try:
                vector = tuple(float(value) for value in item)
            except (TypeError, ValueError) as exc:
                raise RetrievalFailure("The embedder returned a non-numeric vector.") from exc
            if not vector:
                raise RetrievalFailure("The embedder returned an empty vector.")
            vectors.append(vector)
        return vectors

    def _load(self) -> object:
        if self._model is not None:
            return self._model
        try:
            from fastembed import TextEmbedding

            self._model = TextEmbedding(model_name=self.model_id)
        except Exception as exc:
            raise EmbedderUnavailable("The embedding model is not available.") from exc
        return self._model


@dataclass(frozen=True, slots=True)
class _Trace:
    mode: str
    segment_ids: tuple[str, ...]
    scores: tuple[tuple[str, float], ...]


class DocumentRetrieval:
    """Property contexts for one document. The vectors are not serialised."""

    def __init__(
        self,
        document: LoadedDocument,
        owners: tuple[int, ...],
        window_vectors: tuple[tuple[float, ...], ...],
        query_vectors: dict[Property, tuple[float, ...]],
        *,
        promoter_name: str,
        paper_gene_synonym: str | None,
        model_id: str,
    ) -> None:
        self._document = document
        self._owners = owners
        self._window_vectors = window_vectors
        self._query_vectors = query_vectors
        self._promoter_name = promoter_name
        self._paper_gene_synonym = paper_gene_synonym
        self._model_id = model_id
        self._traces: dict[Property, _Trace] = {}

    def context_for(
        self,
        document: LoadedDocument,
        prop: Property,
        *,
        promoter_name: str,
        paper_gene_synonym: str | None,
    ) -> tuple[DocumentSegment, ...] | TechnicalFailure:
        """Return original segments for one property, or a technical failure."""
        del promoter_name, paper_gene_synonym
        if document.segments is not self._document.segments:
            self._traces[prop] = _Trace("error", (), ())
            return _failure(
                "RETRIEVAL_ERROR",
                "Retrieval was asked to use a different document.",
                "DocumentMismatch",
            )
        try:
            chosen, scores = self._choose(prop)
        except RetrievalFailure as exc:
            self._traces[prop] = _Trace("error", (), ())
            return _failure("RETRIEVAL_ERROR", "The document could not be indexed.", type(exc).__name__)
        if not chosen:
            self._traces[prop] = _Trace("insufficient", (), ())
            return _failure(
                "INSUFFICIENT_RETRIEVAL",
                "No usable context was retrieved for this property.",
                "EmptyContext",
            )
        ordered = tuple(self._document.segments[index] for index in sorted(chosen))
        self._traces[prop] = _Trace(
            "retrieved",
            tuple(segment.segment_id for segment in ordered),
            tuple(
                (self._document.segments[index].segment_id, _round_score(scores[index]))
                for index in sorted(chosen)
            ),
        )
        return ordered

    def public_trace(self) -> dict[str, object]:
        """Ids, scores, and mode. No vectors and no segment text."""
        properties: dict[str, object] = {}
        for prop in _PROPERTY_ORDER:
            trace = self._traces.get(prop, _Trace("error", (), ()))
            properties[prop.value] = {
                "mode": trace.mode,
                "segment_ids": list(trace.segment_ids),
                "scores": [
                    {"segment_id": segment_id, "score": score}
                    for segment_id, score in trace.scores
                ],
            }
        return {
            "embedding_model": self._model_id,
            "max_chars": MAX_RETRIEVED_CHARS,
            "properties": properties,
        }

    def _choose(self, prop: Property) -> tuple[list[int], list[float]]:
        segments = self._document.segments
        scores = self._segment_scores(prop)
        needles = _needles(self._promoter_name, self._paper_gene_synonym)
        anchors = [index for index, segment in enumerate(segments) if _is_anchor(segment.text, needles)]
        anchor_set = set(anchors)
        ranked = sorted(range(len(segments)), key=lambda index: (-scores[index], index))
        semantic: list[int] = []
        for index in ranked:
            if index in anchor_set:
                continue
            semantic.append(index)
            if len(semantic) == SEMANTIC_TOP_K:
                break
        seeds = [*anchors, *semantic]
        seed_set = set(seeds)
        neighbors: list[int] = []
        seen_neighbors: set[int] = set()
        for index in seeds:
            for offset in range(1, NEIGHBOR_RADIUS + 1):
                for neighbor in (index - offset, index + offset):
                    if neighbor < 0 or neighbor >= len(segments):
                        continue
                    if neighbor in seed_set or neighbor in seen_neighbors:
                        continue
                    seen_neighbors.add(neighbor)
                    neighbors.append(neighbor)
        neighbors.sort()
        priority: list[int] = []
        seen: set[int] = set()
        for index in [*anchors, *semantic, *neighbors]:
            if index in seen:
                continue
            seen.add(index)
            priority.append(index)
        chosen: list[int] = []
        used = 0
        for index in priority:
            size = len(segments[index].text)
            if size == 0:
                continue
            if used + size > MAX_RETRIEVED_CHARS:
                continue
            chosen.append(index)
            used += size
        return chosen, scores

    def _segment_scores(self, prop: Property) -> list[float]:
        query = self._query_vectors[prop]
        best = [0.0] * len(self._document.segments)
        for owner, vector in zip(self._owners, self._window_vectors, strict=True):
            score = _cosine(query, vector)
            if score > best[owner]:
                best[owner] = score
        return best


def prepare_document_retrieval(
    document: LoadedDocument,
    embedder: Embedder,
    *,
    promoter_name: str,
    paper_gene_synonym: str | None,
) -> DocumentRetrieval:
    """Embed this document's windows and the four property queries."""
    windows: list[str] = []
    owners: list[int] = []
    for index, segment in enumerate(document.segments):
        for window in embedding_windows(segment.text):
            windows.append(window)
            owners.append(index)
    queries = [
        property_query(prop, promoter_name, paper_gene_synonym) for prop in _PROPERTY_ORDER
    ]
    vectors = embedder.embed([*windows, *queries])
    if len(vectors) != len(windows) + len(queries):
        raise RetrievalFailure("The embedder returned an unexpected number of vectors.")
    widths = {len(vector) for vector in vectors}
    if vectors and len(widths) != 1:
        raise RetrievalFailure("The embedder returned vectors of different dimensions.")
    split = len(windows)
    return DocumentRetrieval(
        document,
        tuple(owners),
        tuple(vectors[:split]),
        {prop: vectors[split + offset] for offset, prop in enumerate(_PROPERTY_ORDER)},
        promoter_name=promoter_name,
        paper_gene_synonym=paper_gene_synonym,
        model_id=str(getattr(embedder, "model_id", "synthetic")),
    )


def property_query(prop: Property, promoter_name: str, paper_gene_synonym: str | None) -> str:
    """Property phrase plus the supplied identity. Consensus motifs are absent."""
    parts = [PROPERTY_QUERY_PHRASES[prop], promoter_name.strip()]
    if paper_gene_synonym and paper_gene_synonym.strip():
        parts.append(paper_gene_synonym.strip())
    return " ".join(parts)


def embedding_windows(text: str) -> tuple[str, ...]:
    """Split one segment for embedding. The caller keeps the original segment."""
    if not text:
        return ()
    if len(text) <= EMBEDDING_WINDOW_CHARS:
        return (text,)
    step = EMBEDDING_WINDOW_CHARS - EMBEDDING_WINDOW_OVERLAP
    windows: list[str] = []
    start = 0
    while start < len(text):
        windows.append(text[start : start + EMBEDDING_WINDOW_CHARS])
        if start + EMBEDDING_WINDOW_CHARS >= len(text):
            break
        start += step
    return tuple(windows)


def _needles(promoter_name: str, paper_gene_synonym: str | None) -> tuple[str, ...]:
    values: list[str] = []
    for raw in (promoter_name, paper_gene_synonym):
        if raw is None:
            continue
        token = raw.strip().casefold()
        if token and token not in values:
            values.append(token)
    return tuple(values)


def _is_anchor(text: str, needles: tuple[str, ...]) -> bool:
    folded = text.casefold()
    return any(needle in folded for needle in needles)


def _cosine(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    if len(left) != len(right) or not left:
        raise RetrievalFailure("The embedder returned vectors of different dimensions.")
    dot = sum(x * y for x, y in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(x * x for x in left))
    right_norm = math.sqrt(sum(y * y for y in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return dot / (left_norm * right_norm)


def _round_score(score: float) -> float:
    return round(float(score), 6)


def _failure(code: str, message: str, cause: str) -> TechnicalFailure:
    return TechnicalFailure(stage="retrieval", code=code, message=message, cause=cause)
