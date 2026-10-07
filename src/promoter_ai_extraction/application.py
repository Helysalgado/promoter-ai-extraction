"""Synthetic baseline wiring: load → extract → persist → evaluate (T035)."""
from __future__ import annotations

from pathlib import Path

from promoter_ai_extraction.boundary import ExtractionRequestFactory
from promoter_ai_extraction.documents import DocumentLoader, DocumentSource, LoadedDocument
from promoter_ai_extraction.evaluation.metrics import EvaluationReport
from promoter_ai_extraction.evaluation.service import EvaluationError, EvaluationService
from promoter_ai_extraction.extraction import GuidedExtractionService, ModelBackend, PropertyExtractor
from promoter_ai_extraction.models import TechnicalFailure
from promoter_ai_extraction.persistence import PersistenceFailure, PredictionStore
from promoter_ai_extraction.validation import OutputValidator

__all__ = ["GuidedBaselineApplication"]


class GuidedBaselineApplication:
    """Orchestrates one synthetic paper × promoter run without a UI or API."""

    def __init__(self, backend: ModelBackend) -> None:
        self._documents = DocumentLoader()
        extractor = PropertyExtractor(backend=backend, validator=OutputValidator())
        self._extraction = GuidedExtractionService(extractor, ExtractionRequestFactory())

    def run(
        self,
        *,
        source: DocumentSource,
        promoter_name: str,
        gold_path: Path,
        prediction_dir: Path,
        run_id: str,
        promoter_id: str | None = None,
        paper_gene_synonym: str | None = None,
    ) -> EvaluationReport | TechnicalFailure | PersistenceFailure | EvaluationError:
        loaded = self._documents.load(source)
        if not isinstance(loaded, LoadedDocument):
            return loaded
        run = self._extraction.run(
            loaded,
            promoter_name,
            promoter_id=promoter_id,
            paper_gene_synonym=paper_gene_synonym,
            run_id=run_id,
        )
        store = PredictionStore(prediction_dir)
        saved = store.save(run, document_hash=loaded.document_hash)
        if isinstance(saved, PersistenceFailure):
            return saved
        return EvaluationService(store).evaluate(saved, gold_path)
