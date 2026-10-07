"""TEI/XML document loader tests — T007 (RED) / T008 (GREEN) + contract corrections.

All fixtures are synthetic TEI/XML strings; no real papers or gold data accessed.

Covers:
  - Valid TEI/XML with paragraphs, headings, figure captions, tables → LoadedDocument
  - Canonical source_type vocabulary: body_text / figure_caption / table / other
  - Caption location includes containing <figure xml:id>
  - Stable, unique segment IDs and reproducible document hash
  - Location populated from available XML context (section type, xml:id)
  - Unavailable location → exactly None (no invented precision)
  - Malformed XML → TechnicalFailure(code=MALFORMED_XML)
  - DTD/internal-entity XML → TechnicalFailure(code=UNSAFE_XML)
  - External-entity (XXE) XML → TechnicalFailure(code=UNSAFE_XML) [fail-closed]
  - Empty body (no textual content) → TechnicalFailure(code=NO_TEXTUAL_CONTENT)
  - path XOR content: both set or both absent → TechnicalFailure(code=INVALID_SOURCE)
  - TechnicalFailure code is never a ScientificStatus value
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from promoter_ai_extraction.documents import DocumentLoader, DocumentSource, LoadedDocument
from promoter_ai_extraction.models import ScientificStatus, TechnicalFailure

# ---------------------------------------------------------------------------
# Synthetic TEI fixtures (deterministic, no real data)
# ---------------------------------------------------------------------------

_MINIMAL_TEI = """\
<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc><titleStmt><title>Synthetic Test Paper</title></titleStmt></fileDesc>
  </teiHeader>
  <text>
    <body>
      <div type="abstract" xml:id="abs">
        <p>This is the abstract content of the synthetic paper.</p>
      </div>
      <div type="intro" xml:id="intro">
        <head>Introduction</head>
        <p xml:id="p1">The promoter pA is regulated under stress conditions.</p>
      </div>
      <div type="results" xml:id="results">
        <head>Results</head>
        <p xml:id="p2">The TSS was mapped to position +1 relative to the A of the ATG.</p>
      </div>
    </body>
  </text>
</TEI>"""

_TEI_WITH_FIGURE = """\
<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <div type="results" xml:id="results">
        <p>Results paragraph with figure reference.</p>
        <figure xml:id="fig1">
          <figDesc>Figure 1: TSS mapping of promoter pA showing position +1.</figDesc>
        </figure>
      </div>
    </body>
  </text>
</TEI>"""

_TEI_WITH_TABLE = """\
<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <div type="results" xml:id="results">
        <p>Table 1 shows TSS positions for three promoters.</p>
        <table xml:id="tbl1">
          <row><cell>Promoter</cell><cell>TSS</cell><cell>Sigma</cell></row>
          <row><cell>pA</cell><cell>+1</cell><cell>sigma70</cell></row>
          <row><cell>pB</cell><cell>-1</cell><cell>sigma70</cell></row>
        </table>
      </div>
    </body>
  </text>
</TEI>"""

# A paragraph directly inside body with no div wrapper and no xml:id anywhere →
# location must be exactly None (no invented precision).
_TEI_NO_LOCATION_CONTEXT = """\
<?xml version="1.0" encoding="UTF-8"?>
<TEI>
  <text>
    <body>
      <p>A paragraph without any section div wrapper or element identifier.</p>
    </body>
  </text>
</TEI>"""

_MALFORMED_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <body>
      <p>This paragraph tag is never closed
    </body>
  </text>"""
# Note: missing </TEI> and <p> is unclosed — genuinely malformed.

# Internal entity declaration (DOCTYPE with inline entity body).
_UNSAFE_INTERNAL_ENTITY_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [<!ENTITY xxe "injected content">]>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text><body><p>Some text here.</p></body></text>
</TEI>"""

# External entity declaration (XXE attack vector: SYSTEM URI).
# defusedxml must reject this without accessing the filesystem or network.
_UNSAFE_EXTERNAL_ENTITY_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text><body><p>Content &xxe;</p></body></text>
</TEI>"""

_TEI_EMPTY_BODY = """\
<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader></teiHeader>
  <text>
    <body>
    </body>
  </text>
</TEI>"""


# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def loader() -> DocumentLoader:
    return DocumentLoader()


def _src(content: str, paper_id: str = "P001") -> DocumentSource:
    return DocumentSource(paper_id=paper_id, path=None, content=content, format="TEI/XML")


# ---------------------------------------------------------------------------
# Happy path — valid TEI/XML
# ---------------------------------------------------------------------------


def test_tei_valid_returns_loaded_document(loader: DocumentLoader) -> None:
    result = loader.load(_src(_MINIMAL_TEI))
    assert isinstance(result, LoadedDocument)
    assert result.format == "TEI/XML"
    assert result.paper_id == "P001"


def test_tei_paragraphs_appear_in_segments(loader: DocumentLoader) -> None:
    result = loader.load(_src(_MINIMAL_TEI))
    assert isinstance(result, LoadedDocument)
    all_text = " ".join(s.text for s in result.segments)
    assert "abstract content" in all_text
    assert "promoter pA" in all_text
    assert "position +1" in all_text


def test_tei_paragraph_source_type_is_body_text(loader: DocumentLoader) -> None:
    """Canonical vocabulary: <p> elements must use source_type='body_text'."""
    result = loader.load(_src(_MINIMAL_TEI))
    assert isinstance(result, LoadedDocument)
    body_segs = [s for s in result.segments if s.source_type == "body_text"]
    assert len(body_segs) >= 1


def test_tei_caption_source_type_is_figure_caption(loader: DocumentLoader) -> None:
    """Canonical vocabulary: <figDesc> elements must use source_type='figure_caption'."""
    result = loader.load(_src(_TEI_WITH_FIGURE))
    assert isinstance(result, LoadedDocument)
    captions = [s for s in result.segments if s.source_type == "figure_caption"]
    assert len(captions) >= 1
    assert any("TSS mapping" in c.text for c in captions)


def test_tei_table_source_type_is_table(loader: DocumentLoader) -> None:
    result = loader.load(_src(_TEI_WITH_TABLE))
    assert isinstance(result, LoadedDocument)
    tables = [s for s in result.segments if s.source_type == "table"]
    assert len(tables) >= 1
    assert any("pA" in t.text for t in tables)


def test_tei_table_segment_contains_cell_text(loader: DocumentLoader) -> None:
    """Table cells must be captured; header and data rows included."""
    result = loader.load(_src(_TEI_WITH_TABLE))
    assert isinstance(result, LoadedDocument)
    tables = [s for s in result.segments if s.source_type == "table"]
    combined = " ".join(t.text for t in tables)
    assert "Promoter" in combined
    assert "sigma70" in combined


def test_tei_figure_id_in_caption_location(loader: DocumentLoader) -> None:
    """The containing <figure xml:id> must appear in the caption segment's location."""
    result = loader.load(_src(_TEI_WITH_FIGURE))
    assert isinstance(result, LoadedDocument)
    captions = [s for s in result.segments if s.source_type == "figure_caption"]
    assert len(captions) >= 1
    for cap in captions:
        assert cap.location is not None, "Caption location must not be None when figure has xml:id"
        assert "fig1" in cap.location, (
            f"Expected figure id 'fig1' in caption location, got: {cap.location!r}"
        )


def test_tei_segment_ids_are_stable(loader: DocumentLoader) -> None:
    """Same content loaded twice → identical segment IDs (deterministic)."""
    source = _src(_MINIMAL_TEI)
    r1 = loader.load(source)
    r2 = loader.load(source)
    assert isinstance(r1, LoadedDocument) and isinstance(r2, LoadedDocument)
    assert [s.segment_id for s in r1.segments] == [s.segment_id for s in r2.segments]


def test_tei_segment_ids_are_unique(loader: DocumentLoader) -> None:
    result = loader.load(_src(_MINIMAL_TEI))
    assert isinstance(result, LoadedDocument)
    ids = [s.segment_id for s in result.segments]
    assert len(ids) == len(set(ids)), "All segment IDs must be unique within the document"


def test_tei_document_hash_is_sha256_hex(loader: DocumentLoader) -> None:
    result = loader.load(_src(_MINIMAL_TEI))
    assert isinstance(result, LoadedDocument)
    assert len(result.document_hash) == 64
    int(result.document_hash, 16)  # raises ValueError if not hex


def test_tei_document_hash_reproducible(loader: DocumentLoader) -> None:
    source = _src(_MINIMAL_TEI)
    r1 = loader.load(source)
    r2 = loader.load(source)
    assert isinstance(r1, LoadedDocument) and isinstance(r2, LoadedDocument)
    assert r1.document_hash == r2.document_hash


def test_tei_location_populated_from_section_context(loader: DocumentLoader) -> None:
    """Segments inside a typed, identified div must report that context in location."""
    result = loader.load(_src(_MINIMAL_TEI))
    assert isinstance(result, LoadedDocument)
    located = [s for s in result.segments if s.location is not None]
    assert len(located) > 0


def test_tei_location_contains_section_type_or_id(loader: DocumentLoader) -> None:
    """Location string for segments inside typed divs must reference the section."""
    result = loader.load(_src(_MINIMAL_TEI))
    assert isinstance(result, LoadedDocument)
    located = [s for s in result.segments if s.location is not None]
    any_section_ref = any(
        "intro" in (s.location or "")
        or "results" in (s.location or "")
        or "abs" in (s.location or "")
        for s in located
    )
    assert any_section_ref, "Expected section context in at least one segment's location"


def test_tei_no_invented_precision_when_no_context(loader: DocumentLoader) -> None:
    """Spec §Evidence and location: unavailable precision must be exactly None.

    _TEI_NO_LOCATION_CONTEXT has no namespace, no div wrapper, and no xml:id
    on any element — the paragraph's location must be None, not an empty string
    or any invented placeholder.
    """
    result = loader.load(_src(_TEI_NO_LOCATION_CONTEXT))
    assert isinstance(result, LoadedDocument)
    assert len(result.segments) >= 1
    for seg in result.segments:
        assert seg.location is None, (
            f"Expected location=None for context-free segment, got {seg.location!r}"
        )


def test_tei_loaded_document_is_immutable(loader: DocumentLoader) -> None:
    result = loader.load(_src(_MINIMAL_TEI))
    assert isinstance(result, LoadedDocument)
    with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
        result.paper_id = "other"  # type: ignore[misc]


def test_tei_segments_are_immutable(loader: DocumentLoader) -> None:
    result = loader.load(_src(_MINIMAL_TEI))
    assert isinstance(result, LoadedDocument)
    for seg in result.segments:
        with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
            seg.text = "modified"  # type: ignore[misc]


def test_tei_paper_id_preserved(loader: DocumentLoader) -> None:
    result = loader.load(_src(_MINIMAL_TEI, paper_id="PMID88888"))
    assert isinstance(result, LoadedDocument)
    assert result.paper_id == "PMID88888"


# ---------------------------------------------------------------------------
# Failure modes — TEI/XML
# ---------------------------------------------------------------------------


def test_tei_malformed_xml_is_technical_failure(loader: DocumentLoader) -> None:
    """Spec AC-16: malformed input → TechnicalFailure, not scientific abstention."""
    result = loader.load(_src(_MALFORMED_XML))
    assert isinstance(result, TechnicalFailure)
    assert result.stage == "document_loading"
    assert result.code == "MALFORMED_XML"


def test_tei_unsafe_internal_entity_is_technical_failure(loader: DocumentLoader) -> None:
    """defusedxml must reject DOCTYPE with inline entity → fail-closed as UNSAFE_XML."""
    result = loader.load(_src(_UNSAFE_INTERNAL_ENTITY_XML))
    assert isinstance(result, TechnicalFailure)
    assert result.stage == "document_loading"
    assert result.code == "UNSAFE_XML"


def test_tei_unsafe_external_entity_xxe_is_technical_failure(loader: DocumentLoader) -> None:
    """defusedxml must reject external-entity (XXE) declaration without accessing the URI.

    The SYSTEM URI must never be fetched; the failure must be raised at parse time.
    """
    result = loader.load(_src(_UNSAFE_EXTERNAL_ENTITY_XML))
    assert isinstance(result, TechnicalFailure)
    assert result.stage == "document_loading"
    assert result.code == "UNSAFE_XML"


def test_tei_empty_body_no_text_is_technical_failure(loader: DocumentLoader) -> None:
    """A well-formed TEI with no extractable text → NO_TEXTUAL_CONTENT failure."""
    result = loader.load(_src(_TEI_EMPTY_BODY))
    assert isinstance(result, TechnicalFailure)
    assert result.code == "NO_TEXTUAL_CONTENT"


def test_tei_malformed_failure_code_is_not_scientific_status(loader: DocumentLoader) -> None:
    """Constitution principle 6: failure code ≠ ScientificStatus."""
    result = loader.load(_src(_MALFORMED_XML))
    assert isinstance(result, TechnicalFailure)
    scientific_codes = {s.value for s in ScientificStatus}
    assert result.code not in scientific_codes


def test_tei_unsafe_failure_code_is_not_scientific_status(loader: DocumentLoader) -> None:
    result = loader.load(_src(_UNSAFE_INTERNAL_ENTITY_XML))
    assert isinstance(result, TechnicalFailure)
    scientific_codes = {s.value for s in ScientificStatus}
    assert result.code not in scientific_codes


# ---------------------------------------------------------------------------
# DocumentSource XOR enforcement — path and content are mutually exclusive
# ---------------------------------------------------------------------------


def test_tei_both_path_and_content_is_invalid_source(
    tmp_path: Path, loader: DocumentLoader
) -> None:
    """Providing both path and content is ambiguous → INVALID_SOURCE TechnicalFailure."""
    p = tmp_path / "paper.xml"
    # File need not exist — the XOR check must fire before any I/O.
    source = DocumentSource(
        paper_id="P001", path=p, content=_MINIMAL_TEI, format="TEI/XML"
    )
    result = loader.load(source)
    assert isinstance(result, TechnicalFailure)
    assert result.code == "INVALID_SOURCE"
    assert result.stage == "document_loading"


def test_tei_neither_path_nor_content_is_invalid_source(loader: DocumentLoader) -> None:
    """Providing neither path nor content → INVALID_SOURCE TechnicalFailure."""
    source = DocumentSource(paper_id="P001", path=None, content=None, format="TEI/XML")
    result = loader.load(source)
    assert isinstance(result, TechnicalFailure)
    assert result.code == "INVALID_SOURCE"


# ---------------------------------------------------------------------------
# Finding #6: error messages must not echo user-controlled values.
# Sentinel tests — RED until messages are made generic.
# ---------------------------------------------------------------------------


def test_unsupported_format_message_does_not_echo_format_value(
    loader: DocumentLoader,
) -> None:
    """UNSUPPORTED_FORMAT message must not echo the caller-supplied format string.
    The format value is user-controlled and may contain arbitrary data."""
    sentinel = "FORMAT_SENTINEL_XYZ_PRIVATE"
    source = DocumentSource(
        paper_id="P001",
        path=None,
        content="some text",
        format=sentinel,  # type: ignore[arg-type]
    )
    result = loader.load(source)
    assert isinstance(result, TechnicalFailure)
    assert result.code == "UNSUPPORTED_FORMAT"
    # Current buggy code: f"Document format '{source.format}' is not supported."
    # Fixed code: a static string with no caller value echoed
    assert sentinel not in result.message


def test_malformed_xml_message_does_not_echo_parse_error_text(
    loader: DocumentLoader,
) -> None:
    """MALFORMED_XML message must not include ParseError diagnostic text.
    The ParseError str() can contain line/column info derived from caller input."""
    source = DocumentSource(
        paper_id="P001",
        path=None,
        content="<unclosed_element",
        format="TEI/XML",
    )
    result = loader.load(source)
    assert isinstance(result, TechnicalFailure)
    assert result.code == "MALFORMED_XML"
    # Current buggy code: f"TEI/XML document is not well-formed: {exc}"
    # str(ParseError) → "unclosed token: line 1, column 0" — contains "line"/"column"
    # Fixed code: a static string with no ParseError details
    assert "line" not in result.message
    assert "column" not in result.message
