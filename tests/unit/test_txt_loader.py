"""TXT document loader tests — T005 (RED) / T006 (GREEN) + contract corrections.

All fixtures are synthetic; no real papers or gold data are accessed.
Covers: readable UTF-8 TXT → LoadedDocument with ordered paragraph segments,
stable segment IDs, line-based location, SHA-256 hash;
empty / unreadable / non-UTF-8 inputs → TechnicalFailure (not a ScientificStatus);
path XOR content enforcement (both set or both absent → INVALID_SOURCE).
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from promoter_ai_extraction.documents import (
    DocumentLoader,
    DocumentSource,
    LoadedDocument,
)
from promoter_ai_extraction.models import ScientificStatus, TechnicalFailure


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def loader() -> DocumentLoader:
    return DocumentLoader()


# ---------------------------------------------------------------------------
# Happy path — valid UTF-8 TXT
# ---------------------------------------------------------------------------


def test_txt_valid_returns_loaded_document(tmp_path: Path, loader: DocumentLoader) -> None:
    p = tmp_path / "paper.txt"
    p.write_text("First paragraph.\n\nSecond paragraph.", encoding="utf-8")
    source = DocumentSource(paper_id="P001", path=p, content=None, format="TXT")
    result = loader.load(source)
    assert isinstance(result, LoadedDocument)
    assert result.paper_id == "P001"
    assert result.format == "TXT"


def test_txt_segments_are_ordered_and_non_empty(tmp_path: Path, loader: DocumentLoader) -> None:
    p = tmp_path / "paper.txt"
    p.write_text("Alpha.\n\nBeta.\n\nGamma.", encoding="utf-8")
    source = DocumentSource(paper_id="P001", path=p, content=None, format="TXT")
    result = loader.load(source)
    assert isinstance(result, LoadedDocument)
    texts = [s.text for s in result.segments]
    assert texts == ["Alpha.", "Beta.", "Gamma."]


def test_txt_segment_ids_are_stable(tmp_path: Path, loader: DocumentLoader) -> None:
    """Same file loaded twice must produce identical segment IDs (deterministic)."""
    p = tmp_path / "paper.txt"
    p.write_text("Paragraph one.\n\nParagraph two.", encoding="utf-8")
    source = DocumentSource(paper_id="P001", path=p, content=None, format="TXT")
    r1 = loader.load(source)
    r2 = loader.load(source)
    assert isinstance(r1, LoadedDocument) and isinstance(r2, LoadedDocument)
    assert [s.segment_id for s in r1.segments] == [s.segment_id for s in r2.segments]


def test_txt_segment_ids_are_unique(tmp_path: Path, loader: DocumentLoader) -> None:
    p = tmp_path / "paper.txt"
    p.write_text("A.\n\nB.\n\nC.\n\nD.", encoding="utf-8")
    source = DocumentSource(paper_id="P001", path=p, content=None, format="TXT")
    result = loader.load(source)
    assert isinstance(result, LoadedDocument)
    ids = [s.segment_id for s in result.segments]
    assert len(ids) == len(set(ids)), "Segment IDs must be unique"


def test_txt_source_type_is_body_text_for_all_paragraphs(tmp_path: Path, loader: DocumentLoader) -> None:
    """Canonical vocabulary: plain text paragraphs must use source_type='body_text'."""
    p = tmp_path / "paper.txt"
    p.write_text("Para one.\n\nPara two.", encoding="utf-8")
    source = DocumentSource(paper_id="P001", path=p, content=None, format="TXT")
    result = loader.load(source)
    assert isinstance(result, LoadedDocument)
    assert all(s.source_type == "body_text" for s in result.segments)


def test_txt_segment_location_contains_line_range(tmp_path: Path, loader: DocumentLoader) -> None:
    """Each segment location must indicate line range; no invented fields."""
    p = tmp_path / "paper.txt"
    p.write_text("Line one.\nLine two.\n\nLine four.", encoding="utf-8")
    source = DocumentSource(paper_id="P001", path=p, content=None, format="TXT")
    result = loader.load(source)
    assert isinstance(result, LoadedDocument)
    for seg in result.segments:
        assert seg.location is not None
        assert "lines:" in seg.location


def test_txt_multiline_paragraph_has_correct_line_range(tmp_path: Path, loader: DocumentLoader) -> None:
    """A paragraph spanning lines 1-3 must report lines:1-3 (1-indexed)."""
    p = tmp_path / "paper.txt"
    p.write_text("Line one.\nLine two.\nLine three.\n\nSecond para.", encoding="utf-8")
    source = DocumentSource(paper_id="P001", path=p, content=None, format="TXT")
    result = loader.load(source)
    assert isinstance(result, LoadedDocument)
    assert len(result.segments) == 2
    first = result.segments[0]
    assert "lines:1-3" in first.location  # type: ignore[operator]


def test_txt_document_hash_is_sha256_hex(tmp_path: Path, loader: DocumentLoader) -> None:
    p = tmp_path / "paper.txt"
    p.write_text("Content for hashing.", encoding="utf-8")
    source = DocumentSource(paper_id="P001", path=p, content=None, format="TXT")
    result = loader.load(source)
    assert isinstance(result, LoadedDocument)
    assert len(result.document_hash) == 64
    int(result.document_hash, 16)  # valid hex — raises ValueError if not


def test_txt_hash_same_via_path_and_content(tmp_path: Path, loader: DocumentLoader) -> None:
    """Path-based and content-based loading of the same bytes must produce the same hash."""
    text = "Reproducible content.\n\nSecond paragraph."
    p = tmp_path / "paper.txt"
    p.write_bytes(text.encode("utf-8"))
    r_path = loader.load(DocumentSource(paper_id="P001", path=p, content=None, format="TXT"))
    r_content = loader.load(DocumentSource(paper_id="P001", path=None, content=text, format="TXT"))
    assert isinstance(r_path, LoadedDocument) and isinstance(r_content, LoadedDocument)
    assert r_path.document_hash == r_content.document_hash


def test_txt_loaded_document_is_immutable(tmp_path: Path, loader: DocumentLoader) -> None:
    p = tmp_path / "paper.txt"
    p.write_text("Some text.", encoding="utf-8")
    source = DocumentSource(paper_id="P001", path=p, content=None, format="TXT")
    result = loader.load(source)
    assert isinstance(result, LoadedDocument)
    with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
        result.paper_id = "other"  # type: ignore[misc]


def test_txt_segments_are_immutable(tmp_path: Path, loader: DocumentLoader) -> None:
    p = tmp_path / "paper.txt"
    p.write_text("Some text.", encoding="utf-8")
    source = DocumentSource(paper_id="P001", path=p, content=None, format="TXT")
    result = loader.load(source)
    assert isinstance(result, LoadedDocument)
    for seg in result.segments:
        with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
            seg.text = "modified"  # type: ignore[misc]


def test_txt_paper_id_preserved(tmp_path: Path, loader: DocumentLoader) -> None:
    p = tmp_path / "paper.txt"
    p.write_text("Content.", encoding="utf-8")
    source = DocumentSource(paper_id="PMID99999", path=p, content=None, format="TXT")
    result = loader.load(source)
    assert isinstance(result, LoadedDocument)
    assert result.paper_id == "PMID99999"


# ---------------------------------------------------------------------------
# Failure modes — TXT
# ---------------------------------------------------------------------------


def test_txt_empty_file_is_technical_failure(tmp_path: Path, loader: DocumentLoader) -> None:
    p = tmp_path / "empty.txt"
    p.write_text("", encoding="utf-8")
    source = DocumentSource(paper_id="P001", path=p, content=None, format="TXT")
    result = loader.load(source)
    assert isinstance(result, TechnicalFailure)
    assert result.stage == "document_loading"
    assert result.code == "EMPTY_DOCUMENT"


def test_txt_whitespace_only_file_is_technical_failure(tmp_path: Path, loader: DocumentLoader) -> None:
    p = tmp_path / "whitespace.txt"
    p.write_text("   \n\n   \n", encoding="utf-8")
    source = DocumentSource(paper_id="P001", path=p, content=None, format="TXT")
    result = loader.load(source)
    assert isinstance(result, TechnicalFailure)
    assert result.code == "EMPTY_DOCUMENT"


def test_txt_missing_file_is_technical_failure(tmp_path: Path, loader: DocumentLoader) -> None:
    p = tmp_path / "nonexistent.txt"
    source = DocumentSource(paper_id="P001", path=p, content=None, format="TXT")
    result = loader.load(source)
    assert isinstance(result, TechnicalFailure)
    assert result.code == "UNREADABLE_INPUT"


def test_txt_non_utf8_bytes_is_technical_failure(tmp_path: Path, loader: DocumentLoader) -> None:
    """A file containing non-UTF-8 bytes must be a DECODING_ERROR, not a scientific abstention."""
    p = tmp_path / "binary.txt"
    p.write_bytes(b"\xff\xfe\x00\x01invalid sequence")
    source = DocumentSource(paper_id="P001", path=p, content=None, format="TXT")
    result = loader.load(source)
    assert isinstance(result, TechnicalFailure)
    assert result.code == "DECODING_ERROR"


def test_txt_technical_failure_code_is_not_scientific_status(tmp_path: Path, loader: DocumentLoader) -> None:
    """Constitution principle 6: technical failure code must never be a ScientificStatus value."""
    p = tmp_path / "empty.txt"
    p.write_text("", encoding="utf-8")
    source = DocumentSource(paper_id="P001", path=p, content=None, format="TXT")
    result = loader.load(source)
    assert isinstance(result, TechnicalFailure)
    scientific_codes = {s.value for s in ScientificStatus}
    assert result.code not in scientific_codes


# ---------------------------------------------------------------------------
# DocumentSource XOR enforcement — path and content are mutually exclusive
# ---------------------------------------------------------------------------


def test_txt_both_path_and_content_is_invalid_source(tmp_path: Path, loader: DocumentLoader) -> None:
    """Providing both path and content is ambiguous → INVALID_SOURCE TechnicalFailure."""
    p = tmp_path / "paper.txt"
    # File need not exist — the check must fire before any I/O.
    source = DocumentSource(
        paper_id="P001", path=p, content="some content", format="TXT"
    )
    result = loader.load(source)
    assert isinstance(result, TechnicalFailure)
    assert result.code == "INVALID_SOURCE"
    assert result.stage == "document_loading"


def test_txt_neither_path_nor_content_is_invalid_source(loader: DocumentLoader) -> None:
    """Providing neither path nor content → INVALID_SOURCE TechnicalFailure."""
    source = DocumentSource(paper_id="P001", path=None, content=None, format="TXT")
    result = loader.load(source)
    assert isinstance(result, TechnicalFailure)
    assert result.code == "INVALID_SOURCE"
