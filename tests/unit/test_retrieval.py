"""Synthetic retrieval. No model download and no gold workbook."""
from __future__ import annotations

import inspect

from promoter_ai_extraction.boundary import ExtractionRequestFactory
from promoter_ai_extraction.documents import DocumentSegment, LoadedDocument
from promoter_ai_extraction.extraction import (
    GuidedExtractionService,
    PropertyExtractor,
    RawPropertyPayload,
)
from promoter_ai_extraction.models import Property, ScientificStatus, TechnicalFailure
from promoter_ai_extraction.retrieval import (
    EMBEDDING_MODEL_ID,
    EMBEDDING_WINDOW_CHARS,
    MAX_RETRIEVED_CHARS,
    FastEmbedEmbedder,
    RetrievalFailure,
    embedding_windows,
    prepare_document_retrieval,
    property_query,
)
from promoter_ai_extraction.validation import OutputValidator

_PHRASES = {
    Property.TSS: "transcription start site of this promoter",
    Property.CAJA_10: "minus 10 box of this promoter",
    Property.CAJA_35: "minus 35 box of this promoter",
    Property.FACTOR_SIGMA: "sigma factor of this promoter",
}


class PhraseEmbedder:
    model_id = "synthetic-phrase"

    def embed(self, texts: list[str]) -> list[tuple[float, ...]]:
        vectors: list[tuple[float, ...]] = []
        for text in texts:
            folded = text.casefold()
            if _PHRASES[Property.TSS] in folded:
                vectors.append((1.0, 0.0, 0.0, 0.0))
            elif _PHRASES[Property.CAJA_10] in folded:
                vectors.append((0.0, 1.0, 0.0, 0.0))
            elif _PHRASES[Property.CAJA_35] in folded:
                vectors.append((0.0, 0.0, 1.0, 0.0))
            elif _PHRASES[Property.FACTOR_SIGMA] in folded:
                vectors.append((0.0, 0.0, 0.0, 1.0))
            else:
                vectors.append((0.0, 0.0, 0.0, 0.0))
        return vectors


class RecordingEmbedder:
    def __init__(self) -> None:
        self.batches: list[list[str]] = []

    def embed(self, texts: list[str]) -> list[tuple[float, ...]]:
        self.batches.append(list(texts))
        return [(1.0, 0.0) for _ in texts]


def _segment(index: int, text: str) -> DocumentSegment:
    return DocumentSegment(
        segment_id=f"txt:p:{index:04d}",
        text=text,
        source_type="body_text",
        location=f"lines:{index + 1}-{index + 1}",
    )


def _document(segments: tuple[DocumentSegment, ...], paper_id: str = "PMC1") -> LoadedDocument:
    return LoadedDocument(
        paper_id=paper_id,
        format="TXT",
        segments=segments,
        document_hash="abc123",
    )


def _ids(selected: tuple[DocumentSegment, ...] | TechnicalFailure) -> set[str]:
    assert isinstance(selected, tuple)
    return {segment.segment_id for segment in selected}


def test_four_properties_keep_anchor_neighbor_and_planted_segment() -> None:
    anchor = _segment(0, "The promoter WidgetP, also called radC, is identified here.")
    neighbor = _segment(1, "Nearby regulatory context.")
    planted = {
        Property.TSS: _segment(2, f"The {_PHRASES[Property.TSS]} is -42."),
        Property.CAJA_10: _segment(3, f"The {_PHRASES[Property.CAJA_10]} is CATAAT."),
        Property.CAJA_35: _segment(4, f"The {_PHRASES[Property.CAJA_35]} is TTGAAA."),
        Property.FACTOR_SIGMA: _segment(5, f"The {_PHRASES[Property.FACTOR_SIGMA]} is RpoD."),
    }
    document = _document((anchor, neighbor, *planted.values()))
    retrieval = prepare_document_retrieval(
        document,
        PhraseEmbedder(),
        promoter_name="WidgetP",
        paper_gene_synonym="radC",
    )
    hits = 0
    for prop, segment in planted.items():
        selected = retrieval.context_for(
            document,
            prop,
            promoter_name="WidgetP",
            paper_gene_synonym="radC",
        )
        assert isinstance(selected, tuple)
        found = {item.segment_id: item for item in selected}
        assert segment.segment_id in found
        assert anchor.segment_id in found
        assert neighbor.segment_id in found
        assert found[segment.segment_id] is segment
        assert found[segment.segment_id].location == segment.location
        assert found[segment.segment_id].text == segment.text
        hits += 1
    assert hits == 4
    trace = retrieval.public_trace()
    assert trace["max_chars"] == MAX_RETRIEVED_CHARS
    encoded = str(trace)
    assert "WidgetP, also called radC" not in encoded
    assert "vector" not in encoded


def test_synonym_anchor_is_included_when_the_promoter_name_is_absent() -> None:
    synonym_only = _segment(0, "The paper calls this gene radC.")
    fillers = tuple(
        _segment(index, f"The {_PHRASES[Property.TSS]} extra {index}.")
        for index in range(1, 11)
    )
    document = _document((synonym_only, *fillers))
    retrieval = prepare_document_retrieval(
        document,
        PhraseEmbedder(),
        promoter_name="WidgetP",
        paper_gene_synonym="radC",
    )
    selected = retrieval.context_for(
        document,
        Property.TSS,
        promoter_name="WidgetP",
        paper_gene_synonym="radC",
    )
    assert synonym_only.segment_id in _ids(selected)


def test_rank_limit_keeps_the_anchor_neighbor_and_drops_a_later_match() -> None:
    segments = [
        _segment(0, "Left of the identity sentence."),
        _segment(1, "The promoter WidgetP is named here."),
        _segment(2, "Right of the identity sentence."),
    ]
    segments.extend(
        _segment(index, f"The {_PHRASES[Property.TSS]} filler {index}.")
        for index in range(3, 15)
    )
    segments.append(_segment(15, "FAR_UNUSED metabolism."))
    document = _document(tuple(segments))
    retrieval = prepare_document_retrieval(
        document,
        PhraseEmbedder(),
        promoter_name="WidgetP",
        paper_gene_synonym=None,
    )
    selected = _ids(
        retrieval.context_for(
            document,
            Property.TSS,
            promoter_name="WidgetP",
            paper_gene_synonym=None,
        )
    )
    assert "txt:p:0000" in selected
    assert "txt:p:0001" in selected
    assert "txt:p:0003" in selected
    assert "txt:p:0012" not in selected
    assert "txt:p:0015" not in selected


def test_low_similarity_does_not_drop_every_segment() -> None:
    class _Low:
        def embed(self, texts: list[str]) -> list[tuple[float, ...]]:
            vectors: list[tuple[float, ...]] = []
            for text in texts:
                if "LOW_A" in text:
                    vectors.append((0.02, 0.9998))
                elif "LOW_B" in text:
                    vectors.append((0.01, 0.99995))
                else:
                    vectors.append((1.0, 0.0))
            return vectors

    document = _document((_segment(0, "LOW_A note"), _segment(1, "LOW_B note")))
    retrieval = prepare_document_retrieval(
        document,
        _Low(),
        promoter_name="WidgetP",
        paper_gene_synonym=None,
    )
    selected = retrieval.context_for(
        document,
        Property.TSS,
        promoter_name="WidgetP",
        paper_gene_synonym=None,
    )
    assert _ids(selected) == {"txt:p:0000", "txt:p:0001"}
    scores = retrieval.public_trace()["properties"]["TSS"]["scores"]
    assert scores
    assert all(0 < item["score"] < 0.05 for item in scores)


def test_character_budget_skips_what_does_not_fit_without_cutting_text() -> None:
    suffix = " promoter WidgetP"
    first = _segment(0, ("A" * (8_000 - len(suffix))) + suffix)
    second = _segment(1, ("B" * (8_000 - len(suffix))) + suffix)
    semantic = _segment(2, f"The {_PHRASES[Property.TSS]} remains.")
    document = _document((first, second, semantic))
    retrieval = prepare_document_retrieval(
        document,
        PhraseEmbedder(),
        promoter_name="WidgetP",
        paper_gene_synonym=None,
    )
    selected = retrieval.context_for(
        document,
        Property.TSS,
        promoter_name="WidgetP",
        paper_gene_synonym=None,
    )
    assert isinstance(selected, tuple)
    assert [item.segment_id for item in selected] == ["txt:p:0000", "txt:p:0002"]
    assert selected[0].text == first.text
    assert sum(len(item.text) for item in selected) <= MAX_RETRIEVED_CHARS


def test_segment_larger_than_the_budget_is_insufficient_not_scientific() -> None:
    document = _document((_segment(0, "Z" * (MAX_RETRIEVED_CHARS + 1)),))
    retrieval = prepare_document_retrieval(
        document,
        PhraseEmbedder(),
        promoter_name="WidgetP",
        paper_gene_synonym=None,
    )
    selected = retrieval.context_for(
        document,
        Property.TSS,
        promoter_name="WidgetP",
        paper_gene_synonym=None,
    )
    assert isinstance(selected, TechnicalFailure)
    assert selected.code == "INSUFFICIENT_RETRIEVAL"
    assert selected.code not in {status.value for status in ScientificStatus}
    assert retrieval.public_trace()["properties"]["TSS"]["mode"] == "insufficient"


def test_exact_budget_still_retrieves_the_segment() -> None:
    document = _document((_segment(0, "Q" * MAX_RETRIEVED_CHARS),))
    retrieval = prepare_document_retrieval(
        document,
        PhraseEmbedder(),
        promoter_name="WidgetP",
        paper_gene_synonym=None,
    )
    selected = retrieval.context_for(
        document,
        Property.TSS,
        promoter_name="WidgetP",
        paper_gene_synonym=None,
    )
    assert _ids(selected) == {"txt:p:0000"}


def test_embedding_windows_point_back_at_the_original_segment() -> None:
    phrase = f"The {_PHRASES[Property.TSS]} is -42."
    text = ("n" * EMBEDDING_WINDOW_CHARS) + phrase
    windows = embedding_windows(text)
    assert phrase not in windows[0]
    assert phrase in windows[-1]
    parent = _segment(0, text)
    other = _segment(1, "Unrelated sentence.")
    document = _document((parent, other))
    retrieval = prepare_document_retrieval(
        document,
        PhraseEmbedder(),
        promoter_name="WidgetP",
        paper_gene_synonym=None,
    )
    selected = retrieval.context_for(
        document,
        Property.TSS,
        promoter_name="WidgetP",
        paper_gene_synonym=None,
    )
    assert isinstance(selected, tuple)
    match = next(item for item in selected if item.segment_id == parent.segment_id)
    assert match is parent
    assert match.text == text
    assert match.location == "lines:1-1"


def test_two_documents_do_not_share_an_index() -> None:
    embedder = RecordingEmbedder()
    alpha = _document((_segment(0, "ALPHA_TOKEN promoter WidgetP"),), paper_id="A")
    beta = _document((_segment(0, "BETA_TOKEN promoter WidgetP"),), paper_id="B")
    first = prepare_document_retrieval(
        alpha, embedder, promoter_name="WidgetP", paper_gene_synonym=None
    )
    second = prepare_document_retrieval(
        beta, embedder, promoter_name="WidgetP", paper_gene_synonym=None
    )
    assert all("ALPHA_TOKEN" not in text for text in embedder.batches[1])
    selected = second.context_for(
        beta, Property.TSS, promoter_name="WidgetP", paper_gene_synonym=None
    )
    assert _ids(selected) == {"txt:p:0000"}
    assert selected[0].text.startswith("BETA_TOKEN")
    mismatch = first.context_for(
        beta, Property.TSS, promoter_name="WidgetP", paper_gene_synonym=None
    )
    assert isinstance(mismatch, TechnicalFailure)
    assert mismatch.code == "RETRIEVAL_ERROR"


def test_queries_and_module_do_not_carry_gold_or_consensus_motifs() -> None:
    import promoter_ai_extraction.retrieval as retrieval

    source = inspect.getsource(retrieval)
    for banned in ("TATAAT", "TTGACA", "gold_loader", "EvaluationService", "Valor_RegulonDB"):
        assert banned not in source
    for prop in Property:
        query = property_query(prop, "WidgetP", "radC")
        assert "TATAAT" not in query
        assert "TTGACA" not in query
        assert "Valor_RegulonDB" not in query
        assert "SUBSET_GOLD" not in query


def test_fastembed_wrapper_uses_the_approved_model_without_downloading(monkeypatch) -> None:
    constructed: dict[str, str] = {}

    class _FakeEmbedding:
        def __init__(self, model_name: str) -> None:
            constructed["model_name"] = model_name

        def embed(self, texts: list[str]):
            return ((1.0, 0.0) for _ in texts)

    monkeypatch.setattr("fastembed.TextEmbedding", _FakeEmbedding)
    vectors = FastEmbedEmbedder().embed(["segment text"])
    assert constructed["model_name"] == EMBEDDING_MODEL_ID
    assert vectors == [(1.0, 0.0)]


def test_fastembed_load_failure_is_embedder_unavailable(monkeypatch) -> None:
    class _Broken:
        def __init__(self, model_name: str) -> None:
            raise RuntimeError(f"download blocked for {model_name}")

    monkeypatch.setattr("fastembed.TextEmbedding", _Broken)
    try:
        FastEmbedEmbedder().embed(["segment text"])
    except Exception as exc:
        assert type(exc).__name__ == "EmbedderUnavailable"
        assert "download blocked" not in str(exc)
    else:
        raise AssertionError("load failure must surface as EmbedderUnavailable")


def test_vector_count_mismatch_is_a_retrieval_failure() -> None:
    class _Short:
        def embed(self, texts: list[str]) -> list[tuple[float, ...]]:
            return []

    document = _document((_segment(0, "The promoter WidgetP is here."),))
    try:
        prepare_document_retrieval(
            document, _Short(), promoter_name="WidgetP", paper_gene_synonym=None
        )
    except RetrievalFailure:
        return
    raise AssertionError("a short vector batch must fail indexing")


def test_default_service_still_sends_every_segment() -> None:
    segments = (
        _segment(0, "The promoter lacZp1 was described."),
        _segment(1, "A second paragraph stays available."),
    )
    document = _document(segments)
    received: list[tuple[str, ...]] = []

    class _Backend:
        def generate(self, safe_input):
            received.append(tuple(segment.segment_id for segment in safe_input.document_segments))
            assert safe_input.document_segments[1].location == "lines:2-2"
            assert not hasattr(safe_input, "document_hash")
            return RawPropertyPayload(
                status="NOT_FOUND",
                values=(),
                candidates=(),
                abstention_reason="No property sentence was supplied.",
                result_evidence=(),
            )

    service = GuidedExtractionService(
        PropertyExtractor(backend=_Backend(), validator=OutputValidator()),
        ExtractionRequestFactory(),
    )
    run = service.run(document, "lacZp1")
    assert received == [("txt:p:0000", "txt:p:0001")] * 4
    assert run.tss.status.value == "NOT_FOUND"


def test_service_does_not_call_the_model_for_an_empty_or_failed_context() -> None:
    document = _document((_segment(0, "The promoter lacZp1 was described."),))
    calls: list[Property] = []

    class _Backend:
        def generate(self, safe_input):
            calls.append(safe_input.property)
            return RawPropertyPayload(
                status="NOT_FOUND",
                values=(),
                candidates=(),
                abstention_reason="The supplied paragraphs do not state it.",
                result_evidence=(),
            )

    class _Source:
        def context_for(self, document, prop, *, promoter_name, paper_gene_synonym):
            del document, promoter_name, paper_gene_synonym
            if prop is Property.TSS:
                return TechnicalFailure(
                    stage="retrieval",
                    code="INSUFFICIENT_RETRIEVAL",
                    message="No usable context was retrieved for this property.",
                    cause="EmptyContext",
                )
            if prop is Property.CAJA_10:
                return ()
            return document_segments

    document_segments = document.segments
    service = GuidedExtractionService(
        PropertyExtractor(backend=_Backend(), validator=OutputValidator()),
        ExtractionRequestFactory(),
        _Source(),
    )
    run = service.run(document, "lacZp1")
    assert calls == [Property.CAJA_35, Property.FACTOR_SIGMA]
    assert isinstance(run.tss, TechnicalFailure)
    assert run.tss.code == "INSUFFICIENT_RETRIEVAL"
    assert isinstance(run.caja_10, TechnicalFailure)
    assert run.caja_10.code == "INSUFFICIENT_RETRIEVAL"
    assert run.caja_35.status.value == "NOT_FOUND"


def test_cli_modules_do_not_import_retrieval() -> None:
    import promoter_ai_extraction.application as application
    import promoter_ai_extraction.baseline as baseline

    assert "retrieval" not in inspect.getsource(baseline)
    assert "retrieval" not in inspect.getsource(application)
