"""Document loading for the guided extraction baseline (T006 TXT / T008 TEI/XML).

Public types
------------
DocumentSource    – path XOR in-memory content + declared format + paper id
DocumentSegment   – one ordered, stable, source-located text segment
LoadedDocument    – all segments + paper id + document hash
DocumentLoader    – loads TXT or TEI/XML into a LoadedDocument

Design constraints (plan §0 / §3):
- No gold, evaluator, or curator fields anywhere in this module.
- DocumentSource holds only allowlisted extraction inputs.
- All value objects are frozen (immutable after construction).
- Failures are returned as TechnicalFailure; no exception is silently swallowed.
- No silent truncation: if content cannot be fully read and segmented, it is
  a TechnicalFailure, not a partial LoadedDocument.
- Location is populated only from information available in the representation;
  unavailable precision is left as None (spec §Evidence and location).
- path and content are mutually exclusive (XOR): both set or both absent
  yields INVALID_SOURCE before any I/O.

source_type vocabulary (canonical, from extraction/evaluation contracts):
  "body_text"       – paragraph or note body text
  "figure_caption"  – <figDesc> caption text
  "table"           – table cell aggregate
  "other"           – headings and other non-body elements

TXT loading (T006):
  - Read raw bytes; SHA-256 the raw bytes for the document hash.
  - Decode UTF-8; non-decodable bytes → DECODING_ERROR.
  - Split into paragraph segments (consecutive non-empty lines); each segment
    records its 1-based line range as location.
  - Empty or whitespace-only input → EMPTY_DOCUMENT.
  - OS read failure → UNREADABLE_INPUT.

TEI/XML loading (T008):
  - defusedxml fail-closed parsing:
      DTD / entity / external-ref → UNSAFE_XML (constitution principle 9).
      Malformed XML (ParseError) → MALFORMED_XML.
      Non-UTF-8 bytes → DECODING_ERROR.
      Empty string → EMPTY_DOCUMENT.
  - Segment-creating elements: <p>, <head>, <figDesc>, <table>, <note>.
  - Section context propagated from ancestor <div> elements:
      ``type`` attribute → section_type in location.
      ``xml:id`` attribute → section id in location.
  - Figure context propagated from <figure> to its <figDesc> children:
      ``xml:id`` of <figure> → figure id in figDesc location.
  - Page number from preceding <pb n="…"> elements.
  - Element own xml:id → id in location (for non-figDesc elements).
  - Location is None when none of the above are available (no invented precision).
  - Table segments concatenate all <cell> text with " | " separator.
  - No extractable text → NO_TEXTUAL_CONTENT.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import defusedxml
import defusedxml.ElementTree as _DefusedET
from xml.etree.ElementTree import ParseError as _XMLParseError

from promoter_ai_extraction.models import TechnicalFailure

# ---------------------------------------------------------------------------
# TEI / XML namespace constants
# ---------------------------------------------------------------------------

_TEI_NS = "http://www.tei-c.org/ns/1.0"
_XML_NS = "http://www.w3.org/XML/1998/namespace"  # for xml:id

# ---------------------------------------------------------------------------
# Public data carriers
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DocumentSource:
    """The input to :class:`DocumentLoader`.  Contains only allowlisted fields.

    Exactly one of ``path`` or ``content`` must be provided (XOR).
    Providing both or neither yields ``INVALID_SOURCE``.

    Attributes
    ----------
    paper_id:
        Stable identifier for the paper (e.g. PMID or internal ID).
    path:
        Filesystem path to the document file, or ``None`` if content is
        supplied directly.
    content:
        Pre-supplied document text (UTF-8 string), or ``None`` if a path is
        given.  For TXT: the full text.  For TEI/XML: the full XML string.
    format:
        The declared document format: ``"TXT"`` or ``"TEI/XML"``.
    """

    paper_id: str
    path: Path | None
    content: str | None
    format: Literal["TXT", "TEI/XML"]


@dataclass(frozen=True, slots=True)
class DocumentSegment:
    """One ordered, stable segment from a loaded document.

    Attributes
    ----------
    segment_id:
        Stable, unique identifier within the document.  Format:
        ``"txt:p:NNNN"`` for TXT paragraphs, ``"tei:<type>:NNNN"`` for
        TEI elements.
    text:
        Stripped text content of the segment.
    source_type:
        Canonical segment type: ``"body_text"``, ``"figure_caption"``,
        ``"table"``, or ``"other"``.
    location:
        All available document location information as a single string, or
        ``None`` when the representation provides no stable reference.
        The system does not invent unavailable precision.
    """

    segment_id: str
    text: str
    source_type: str
    location: str | None


@dataclass(frozen=True, slots=True)
class LoadedDocument:
    """A successfully loaded document, ready for extraction.

    Attributes
    ----------
    paper_id:
        Passed through from :class:`DocumentSource`.
    format:
        ``"TXT"`` or ``"TEI/XML"``.
    segments:
        Ordered, stable tuple of document segments.
    document_hash:
        SHA-256 hex digest of the raw document bytes.  Used for run identity
        and content verification.
    """

    paper_id: str
    format: str
    segments: tuple[DocumentSegment, ...]
    document_hash: str  # 64-char SHA-256 hex


# ---------------------------------------------------------------------------
# Document loader
# ---------------------------------------------------------------------------

_SUPPORTED_FORMATS: frozenset[str] = frozenset({"TXT", "TEI/XML"})


class DocumentLoader:
    """Loads a :class:`DocumentSource` into a :class:`LoadedDocument`.

    Returns a :class:`~promoter_ai_extraction.models.TechnicalFailure` for
    every error condition.  Never raises exceptions to the caller.
    """

    def load(self, source: DocumentSource) -> LoadedDocument | TechnicalFailure:
        """Load the document described by *source*.

        Returns
        -------
        LoadedDocument
            On success.
        TechnicalFailure
            When any step of loading or segmentation fails.
        """
        if source.format not in _SUPPORTED_FORMATS:
            return TechnicalFailure(
                stage="document_loading",
                code="UNSUPPORTED_FORMAT",
                message="Document format is not supported. Supported formats: TXT, TEI/XML.",
                cause="UnsupportedFormat",
            )

        raw_result = self._read_bytes(source)
        if isinstance(raw_result, TechnicalFailure):
            return raw_result
        raw_bytes = raw_result

        doc_hash = hashlib.sha256(raw_bytes).hexdigest()

        if source.format == "TXT":
            return self._load_txt(source, raw_bytes, doc_hash)

        return self._load_tei(source, raw_bytes, doc_hash)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _read_bytes(self, source: DocumentSource) -> bytes | TechnicalFailure:
        """Return raw bytes from the source, or a TechnicalFailure.

        Enforces the path XOR content invariant: both set or both absent
        yields INVALID_SOURCE without performing any I/O.
        """
        both_set = source.content is not None and source.path is not None
        both_absent = source.content is None and source.path is None

        if both_set:
            return TechnicalFailure(
                stage="document_loading",
                code="INVALID_SOURCE",
                message=(
                    "DocumentSource must provide path or content, not both. "
                    "Supply exactly one."
                ),
                cause="InvalidSource",
            )

        if both_absent:
            return TechnicalFailure(
                stage="document_loading",
                code="INVALID_SOURCE",
                message="DocumentSource must provide either path or content, not neither.",
                cause="InvalidSource",
            )

        if source.content is not None:
            return source.content.encode("utf-8")

        # source.path is not None (guarded above)
        try:
            return source.path.read_bytes()  # type: ignore[union-attr]
        except OSError as exc:
            return TechnicalFailure(
                stage="document_loading",
                code="UNREADABLE_INPUT",
                message=f"Cannot read document file: {type(exc).__name__}.",
                cause=type(exc).__name__,
            )

    # ------------------------------------------------------------------
    # TXT loader (T006)
    # ------------------------------------------------------------------

    def _load_txt(
        self,
        source: DocumentSource,
        raw_bytes: bytes,
        doc_hash: str,
    ) -> LoadedDocument | TechnicalFailure:
        try:
            text = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return TechnicalFailure(
                stage="document_loading",
                code="DECODING_ERROR",
                message="The TXT document contains bytes that are not valid UTF-8.",
                cause="UnicodeDecodeError",
            )

        if not text.strip():
            return TechnicalFailure(
                stage="document_loading",
                code="EMPTY_DOCUMENT",
                message="The supplied TXT document has no content.",
                cause="EmptyDocument",
            )

        segments = _parse_txt_segments(text)
        if not segments:
            return TechnicalFailure(
                stage="document_loading",
                code="EMPTY_DOCUMENT",
                message="The supplied TXT document has no parseable paragraphs.",
                cause="EmptyDocument",
            )

        return LoadedDocument(
            paper_id=source.paper_id,
            format="TXT",
            segments=tuple(segments),
            document_hash=doc_hash,
        )

    # ------------------------------------------------------------------
    # TEI/XML loader (T008)
    # ------------------------------------------------------------------

    def _load_tei(
        self,
        source: DocumentSource,
        raw_bytes: bytes,
        doc_hash: str,
    ) -> LoadedDocument | TechnicalFailure:
        """Parse TEI/XML using defusedxml (fail-closed for unsafe constructs)."""
        try:
            xml_str = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return TechnicalFailure(
                stage="document_loading",
                code="DECODING_ERROR",
                message="The TEI/XML document contains bytes that are not valid UTF-8.",
                cause="UnicodeDecodeError",
            )

        if not xml_str.strip():
            return TechnicalFailure(
                stage="document_loading",
                code="EMPTY_DOCUMENT",
                message="The supplied TEI/XML document is empty.",
                cause="EmptyDocument",
            )

        try:
            root = _DefusedET.fromstring(xml_str)
        except defusedxml.DefusedXmlException as exc:
            return TechnicalFailure(
                stage="document_loading",
                code="UNSAFE_XML",
                message=(
                    f"TEI/XML document contains a forbidden XML construct "
                    f"({type(exc).__name__}). DOCTYPE, DTD, and external entities "
                    f"are not permitted."
                ),
                cause=type(exc).__name__,
            )
        except _XMLParseError:
            return TechnicalFailure(
                stage="document_loading",
                code="MALFORMED_XML",
                message="The TEI/XML document is not well-formed.",
                cause="XMLParseError",
            )

        segments = _parse_tei_segments(root)
        if not segments:
            return TechnicalFailure(
                stage="document_loading",
                code="NO_TEXTUAL_CONTENT",
                message=(
                    "The TEI/XML document contains no extractable textual content. "
                    "Expected at least one <p>, <head>, <figDesc>, <table>, or <note> "
                    "element with non-empty text."
                ),
                cause="NoTextualContent",
            )

        return LoadedDocument(
            paper_id=source.paper_id,
            format="TEI/XML",
            segments=tuple(segments),
            document_hash=doc_hash,
        )


# ---------------------------------------------------------------------------
# TXT paragraph segmentation (pure, deterministic)
# ---------------------------------------------------------------------------


def _parse_txt_segments(text: str) -> list[DocumentSegment]:
    """Split *text* into paragraph segments with stable IDs and line locations.

    A paragraph is a run of consecutive non-empty lines separated from the
    next paragraph by one or more blank lines.  Blank lines are lines whose
    stripped form is empty.

    Segment IDs follow the pattern ``txt:p:NNNN`` (zero-padded, zero-based).
    Location is ``lines:S-E`` where S and E are 1-based line numbers.
    source_type is ``"body_text"`` for all TXT paragraphs.
    """
    lines = text.split("\n")
    segments: list[DocumentSegment] = []
    seg_idx = 0

    para_lines: list[str] = []
    para_start_line: int = 0  # 1-based

    def _flush(end_line_1based: int) -> None:
        nonlocal seg_idx
        if not para_lines:
            return
        para_text = "\n".join(para_lines).strip()
        if para_text:
            segments.append(
                DocumentSegment(
                    segment_id=f"txt:p:{seg_idx:04d}",
                    text=para_text,
                    source_type="body_text",
                    location=f"lines:{para_start_line}-{end_line_1based}",
                )
            )
            seg_idx += 1
        para_lines.clear()

    for idx, line in enumerate(lines):
        line_no = idx + 1  # 1-based
        if line.strip():
            if not para_lines:
                para_start_line = line_no
            para_lines.append(line)
        else:
            _flush(line_no - 1)

    # Flush the last paragraph (no trailing blank line required).
    _flush(len(lines))

    return segments


# ---------------------------------------------------------------------------
# TEI/XML segment extraction (pure, deterministic)
# ---------------------------------------------------------------------------

# XML namespace of a standard xml:id attribute.
_XML_ID_ATTR = f"{{{_XML_NS}}}id"


def _xml_id_of(elem: Any) -> str | None:
    """Return the ``xml:id`` of *elem* if present, else ``None``."""
    return (
        elem.get(_XML_ID_ATTR)
        or elem.get("xml:id")
        or elem.get("id")
        or None
    )


def _localname(tag: str) -> str:
    """Strip the Clark-notation namespace from an ElementTree tag."""
    return tag.split("}")[-1] if "}" in tag else tag


def _iter_text(elem: Any) -> str:
    """Concatenate all text nodes within *elem* (including descendants)."""
    return "".join(elem.itertext()).strip()


def _build_location(
    *,
    page: str | None,
    section_type: str | None,
    section_id: str | None,
    figure_id: str | None = None,
    element_id: str | None,
) -> str | None:
    """Build a location string from available fields; returns None if nothing available.

    Field order in the string: page → section_type → section → figure → id.
    Only fields with non-None, non-empty values are included.
    """
    parts: list[str] = []
    if page:
        parts.append(f"page:{page}")
    if section_type:
        parts.append(f"section_type:{section_type}")
    if section_id:
        parts.append(f"section:{section_id}")
    if figure_id:
        parts.append(f"figure:{figure_id}")
    if element_id:
        parts.append(f"id:{element_id}")
    return " ".join(parts) if parts else None


def _find_body(root: Any) -> Any:
    """Return the <body> element of the TEI tree (with or without namespace)."""
    body = root.find(f".//{{{_TEI_NS}}}body")
    if body is not None:
        return body
    body = root.find(".//body")
    if body is not None:
        return body
    # Last resort: treat the whole tree as the body.
    return root


def _parse_tei_segments(root: Any) -> list[DocumentSegment]:
    """Walk a TEI/XML element tree and produce an ordered list of segments.

    Elements processed and their canonical source_type:
      <p>       → "body_text"
      <head>    → "other"
      <figDesc> → "figure_caption"  (location inherits containing <figure> xml:id)
      <table>   → "table"           (cells concatenated with " | ")
      <note>    → "body_text"

    Context propagation:
      <div> elements propagate section type and xml:id to descendants.
      <figure> elements propagate their xml:id to direct <figDesc> children.
      <pb n="…"> elements update the current page for subsequent segments.

    Segment IDs follow ``tei:<prefix>:NNNN`` (zero-padded sequential counter).
    """
    segments: list[DocumentSegment] = []
    counter: int = 0   # sequential segment counter
    page: str | None = None  # current page from the last <pb n="…">

    def next_id(prefix: str) -> str:
        nonlocal counter
        idx = counter
        counter += 1
        return f"tei:{prefix}:{idx:04d}"

    def walk(
        elem: Any,
        ctx_section_id: str | None,
        ctx_section_type: str | None,
        ctx_figure_id: str | None = None,
    ) -> None:
        nonlocal page
        lname = _localname(elem.tag)

        if lname == "pb":
            page = elem.get("n") or page
            return

        if lname == "div":
            new_sid = _xml_id_of(elem) or ctx_section_id
            new_stype = elem.get("type") or ctx_section_type
            for child in elem:
                walk(child, new_sid, new_stype)
            return

        if lname == "figure":
            # Propagate this figure's xml:id into its children (for figDesc).
            fig_id = _xml_id_of(elem)
            for child in elem:
                walk(child, ctx_section_id, ctx_section_type, ctx_figure_id=fig_id)
            return

        # Standard location for most elements (section + element own id).
        loc = _build_location(
            page=page,
            section_type=ctx_section_type,
            section_id=ctx_section_id,
            element_id=_xml_id_of(elem),
        )

        if lname == "p":
            text = _iter_text(elem)
            if text:
                segments.append(
                    DocumentSegment(
                        segment_id=next_id("p"),
                        text=text,
                        source_type="body_text",
                        location=loc,
                    )
                )
            return  # do not recurse into <p>'s children

        if lname == "head":
            text = _iter_text(elem)
            if text:
                segments.append(
                    DocumentSegment(
                        segment_id=next_id("head"),
                        text=text,
                        source_type="other",
                        location=loc,
                    )
                )
            return

        if lname == "figDesc":
            # Caption location includes the containing figure's xml:id.
            fig_loc = _build_location(
                page=page,
                section_type=ctx_section_type,
                section_id=ctx_section_id,
                figure_id=ctx_figure_id,
                element_id=_xml_id_of(elem),
            )
            text = _iter_text(elem)
            if text:
                segments.append(
                    DocumentSegment(
                        segment_id=next_id("fig"),
                        text=text,
                        source_type="figure_caption",
                        location=fig_loc,
                    )
                )
            return

        if lname == "table":
            cells = [
                _iter_text(c)
                for c in elem.iter()
                if _localname(c.tag) == "cell" and _iter_text(c)
            ]
            if cells:
                segments.append(
                    DocumentSegment(
                        segment_id=next_id("tbl"),
                        text=" | ".join(cells),
                        source_type="table",
                        location=loc,
                    )
                )
            return  # do not recurse into <table>'s children

        if lname == "note":
            text = _iter_text(elem)
            if text:
                segments.append(
                    DocumentSegment(
                        segment_id=next_id("note"),
                        text=text,
                        source_type="body_text",
                        location=loc,
                    )
                )
            return

        # Default: recurse into other container elements (figure_id resets).
        for child in elem:
            walk(child, ctx_section_id, ctx_section_type)

    body = _find_body(root)
    walk(body, None, None)
    return segments
