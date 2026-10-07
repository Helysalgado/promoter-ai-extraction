"""Deterministic fake backend implementations for testing (T016).

These fakes are test-only utilities.  They live in ``tests/`` and must not
be imported by production code.

ScriptedBackend
    Returns a pre-configured response for each :class:`~promoter_ai_extraction.models.Property`.
    Deterministic: the same input always returns the same pre-configured object.

CaptureBackend
    Records every :class:`~promoter_ai_extraction.extraction.SafeExtractionInput`
    it receives.  Returns a single canned response for all calls.  Used in
    contract tests to inspect the exact payload the backend sees.
"""
from __future__ import annotations

from promoter_ai_extraction.extraction import (
    BackendFailure,
    RawPropertyPayload,
    SafeExtractionInput,
)
from promoter_ai_extraction.models import Property

__all__ = ["CaptureBackend", "ScriptedBackend"]


class ScriptedBackend:
    """Returns a pre-scripted response for each property.

    Parameters
    ----------
    responses:
        Mapping from :class:`~promoter_ai_extraction.models.Property` to
        either a :class:`~promoter_ai_extraction.extraction.RawPropertyPayload`
        or a :class:`~promoter_ai_extraction.extraction.BackendFailure`.

        If a property is absent from the mapping and the backend is called
        for that property, :class:`KeyError` is raised — test setup must be
        explicit.

    Design
    ------
    Deterministic: the response object stored in the mapping is returned
    directly (same object, no copy).  This makes ``response1 is response2``
    assertions valid for the same property key.

    Example::

        backend = ScriptedBackend({
            Property.TSS: RawPropertyPayload(status="NOT_FOUND", ...),
            Property.CAJA_10: BackendFailure(code="TIMEOUT", message="..."),
        })
    """

    def __init__(
        self,
        responses: dict[Property, RawPropertyPayload | BackendFailure],
    ) -> None:
        self._responses = responses

    def generate(
        self, safe_input: SafeExtractionInput
    ) -> RawPropertyPayload | BackendFailure:
        """Return the pre-scripted response for ``safe_input.property``."""
        return self._responses[safe_input.property]


class CaptureBackend:
    """Records every SafeExtractionInput received and returns a canned response.

    Parameters
    ----------
    response:
        The single response returned for every call, regardless of property.

    Attributes
    ----------
    received:
        Ordered list of every :class:`~promoter_ai_extraction.extraction.SafeExtractionInput`
        passed to :meth:`generate`.  Inspect this after extraction to verify
        the exact safe projection the extractor sent to the backend.

    Example::

        capture = CaptureBackend(response=some_payload)
        extractor = PropertyExtractor(backend=capture, validator=OutputValidator())
        extractor.extract(request)
        assert isinstance(capture.received[0], SafeExtractionInput)
        assert not hasattr(capture.received[0], "document_hash")
    """

    def __init__(self, response: RawPropertyPayload | BackendFailure) -> None:
        self._response = response
        self.received: list[SafeExtractionInput] = []

    def generate(
        self, safe_input: SafeExtractionInput
    ) -> RawPropertyPayload | BackendFailure:
        """Record *safe_input* and return the canned response."""
        self.received.append(safe_input)
        return self._response
