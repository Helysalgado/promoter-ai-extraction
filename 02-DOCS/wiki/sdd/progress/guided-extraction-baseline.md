---
type: progress
title: Progress — Guided extraction baseline
description: Append-only implementation evidence for guided-extraction-baseline.
tags: [sdd, progress, implementation]
timestamp: 2026-10-07T06:41:00-06:00
topic: sdd
slug: guided-extraction-baseline
---

# Progress — Guided extraction baseline

## T001 — 2026-10-07
- status: complete
- red: `git check-ignore -q 02-DOCS/data/SUBSET_GOLD.xlsx` exited 1.
- green: the real workbook is ignored; `tests/fixtures/synthetic_gold.xlsx` is not ignored; the workbook is not tracked or staged.
- files: `.gitignore`, `scripts/verify.sh`
- decision: use an exact workbook path and local output-directory rules; do not hide versionable synthetic fixtures.
- blocker: none

## T002 — 2026-10-07
- status: complete
- red: `python -c "import pytest, openpyxl, defusedxml"` failed because pytest was unavailable.
- green: imports succeed; `uv run pytest --collect-only` exits 0; `./scripts/verify.sh` exits 0.
- files: `pyproject.toml`, `uv.lock`, `src/promoter_ai_extraction/__init__.py`, `tests/conftest.py`, `tests/unit/test_package.py`, `scripts/verify.sh`
- decision: use the approved Python 3.11 floor, `uv`, a `src/` package, pytest, openpyxl, and defusedxml. No unapproved lint, type-check, framework, or service dependency was added.
- blocker: none

## T003 — 2026-10-07
- status: complete
- red: `python -m pytest tests/unit/test_models.py` failed at collection because `promoter_ai_extraction.models` did not yet exist.
- green: the same test module passes after T004.
- files: `tests/unit/test_models.py`
- decision: none
- blocker: none
- note: the first RED was a missing-module import failure rather than a behavioral assertion failure. This is retained as an implementation-process deviation; the completed tests now exercise the domain contracts and failure invariants.

## T004 — 2026-10-07
- status: complete
- green: domain-model tests pass for four properties, five scientific statuses, `INVALID_CANDIDATE` as a candidate diagnostic, immutable evidence/value/result carriers, and technical-failure separation.
- files: `src/promoter_ai_extraction/models.py`
- decision: use Python 3.11 `StrEnum` and frozen slotted dataclasses; defer result/value cardinality validation to T013–T014 while mechanically rejecting scientific status strings as technical-failure codes.
- blocker: none

## T005 — 2026-10-07
- status: complete
- red: `python -m pytest tests/unit/test_txt_loader.py` failed at collection because `promoter_ai_extraction.documents` did not yet exist.
- green: the focused TXT suite passes after T006.
- files: `tests/unit/test_txt_loader.py`
- decision: none
- blocker: none
- note: the first RED was a missing-module import failure. Later review-driven tests produced behavioral RED evidence for source exclusivity, canonical source types, and safe errors.

## T006 — 2026-10-07
- status: complete
- green: valid UTF-8 TXT loads into stable ordered paragraph segments with reproducible line locations and SHA-256; empty, unreadable, invalid-source, and decoding cases remain technical failures.
- files: `src/promoter_ai_extraction/documents.py`
- decision: a `DocumentSource` must contain exactly one of path or content; no silent truncation or invented location precision.
- blocker: none

## T007 — 2026-10-07
- status: complete
- red: the TEI suite ran against the temporary unsupported-format behavior; 18 tests failed for missing TEI behavior and 2 separation tests passed.
- green: the focused TEI suite passes after T008.
- files: `tests/unit/test_tei_loader.py`
- decision: none
- blocker: none

## T008 — 2026-10-07
- status: complete
- green: `defusedxml` loads synthetic TEI paragraphs, headings, captions, tables, sections, pages, and figure identifiers; malformed XML, DTD/internal entities, XXE, empty content, and invalid source carriers fail technically.
- files: `src/promoter_ai_extraction/documents.py`
- decision: use canonical `source_type` values and preserve only location precision present in TEI/XML.
- blocker: none

## T009 — 2026-10-07
- status: complete
- red: `python -m pytest tests/unit/test_boundary.py` initially failed at collection because `promoter_ai_extraction.boundary` did not yet exist.
- green: subsequent behavioral RED cases covered wrong types, empty paths/optional identities, repeated separators, nested sequence containers, and leakage-safe errors; all pass after T010.
- files: `tests/unit/test_boundary.py`
- decision: none
- blocker: none
- note: the first RED was a missing-module import failure; later behavioral RED runs exercised the boundary directly.

## T010 — 2026-10-07
- status: complete
- green: the closed request and manifest allowlists accept only approved fields; canonical, renamed, nested, joined, and embedded forbidden fields fail before extraction; request and manifest carriers are immutable and contain no arbitrary metadata or gold path.
- files: `src/promoter_ai_extraction/boundary.py`
- decision: recursively inspect mapping keys inside mappings and sequence containers, while never scanning supplied document text values.
- blocker: none

## Increment 1 checkpoint — 2026-10-07
- scope: T001–T010 only
- suite: `./scripts/verify.sh`
- result: 205 passed
- review: no critical findings; accepted Important findings were corrected before checkpoint.
- deferred by scope: T011 and every later task.
- commits: none
- pushes: none

## Increment 2 review addendum — 2026-10-07
- checkpoint before this increment: commit `596a7f318a9d7256c45938d462bf8cb53b51f960` (`feat: establish safe extraction foundation`) pushed to `origin/feat/guided-extraction-baseline`.
- review corrections: TSS sign derivation now requires an explicit translation-start anchor in the raw form or grounded evidence; validator checks abstention reasons, required abstention evidence, fragment/source/location grounding, and rejected-candidate separation; malformed evidence cardinality and backend exceptions remain technical failures.
- final suite: `./scripts/verify.sh`
- final result: 327 passed (205 checkpoint tests + 122 increment tests).
- review: Python-focused review found no high or critical defects; the medium anchor-context integration gap and low typing issue were corrected.
- authoritative roots: unchanged.
- private gold: ignored, untracked, and unstaged.
- commits for T011–T018: none.
- pushes for T011–T018: none.
- skill resolution:
  - used: `implement`, `python`, `testing-py`
  - missing: none
  - fallback: none
  - compact rules: tests precede behavior; public boundaries are typed; fixtures are synthetic; private gold never enters tests; progress is append-only.

## T011 — 2026-10-07
- status: complete
- red: `python -m pytest tests/unit/test_normalization.py` failed at collection — `ModuleNotFoundError: No module named 'promoter_ai_extraction.normalization'`.
- green: 52 normalization tests pass after T012.
- files: `tests/unit/test_normalization.py`
- decision: none
- blocker: none

## T012 — 2026-10-07
- status: complete
- green: pure normalizers for TSS (signed integer pass-through, no auto-sign assignment, genomic coord and +1 designation preserved), Caja sequences (uppercase + typographic separator removal, no base correction), and sigma (Greek σ/Σ → ASCII 'sigma', case/space normalization, no Rpo equivalences). Raw input not mutated. derivation_note is None when no transformation occurred.
- files: `src/promoter_ai_extraction/normalization.py`
- decision: normalize_for_property dispatches by Property enum with a lazy import to avoid circular imports.
- blocker: none

## T013 — 2026-10-07
- status: complete
- red: `python -m pytest tests/unit/test_validation.py` failed at collection — `ModuleNotFoundError: No module named 'promoter_ai_extraction.validation'`.
- green: 19 validator tests pass after T014.
- files: `tests/unit/test_validation.py`
- decision: none
- blocker: none

## T014 — 2026-10-07
- status: complete
- green: OutputValidator enforces (1) identity match paper_id/promoter_name/property against request, (2) EXTRACTED requires non-empty values, (3) abstention statuses require empty values, (4) each accepted value has non-empty evidence, (5) all evidence segment_ids resolve to document.segments. Returns the original PropertyResult on success; returns TechnicalFailure(stage="validation", code="VALIDATION_FAILED") on any violation. Constitution principle 6 preserved: VALIDATION_FAILED is not a ScientificStatus value.
- files: `src/promoter_ai_extraction/validation.py`
- decision: validator returns PropertyResult | TechnicalFailure (not raise); catches all violations inline; never reads gold.
- blocker: none

## T015 — 2026-10-07
- status: complete
- red: `python -m pytest tests/contract/test_extractor_port.py` failed at collection — `ModuleNotFoundError: No module named 'promoter_ai_extraction.extraction'` and `No module named 'tests'`.
- green: 17 contract tests pass after T016 and the sys.path fix in conftest.
- files: `tests/contract/__init__.py`, `tests/contract/test_extractor_port.py`
- decision: `tests/` was not a package; added `sys.path.insert(0, tests_root)` in conftest.py so `fakes.py` is importable as `from fakes import ...` from any subdirectory without making tests a package.
- blocker: none

## T016 — 2026-10-07
- status: complete
- green: SafeExtractionInput (no document_hash, no LoadedDocument, no gold fields), SafeDocumentSegment, RawValuePayload, RawCandidatePayload, RawPropertyPayload, BackendFailure, ModelBackend (Protocol), PropertyExtractor (projects request → SafeExtractionInput, calls backend, normalizes values, builds PropertyResult, validates). GuidedExtractionService implemented in the same module (sequential four-property, ExtractionRun grouping). ScriptedBackend and CaptureBackend in tests/fakes.py.
- files: `src/promoter_ai_extraction/extraction.py`, `tests/fakes.py`, `src/promoter_ai_extraction/models.py` (ExtractionRun added), `tests/conftest.py` (sys.path)
- decision: implemented GuidedExtractionService in T016 alongside PropertyExtractor (plan's T018 content was logically inseparable from T016 given the shared file); T017/T018 tests confirm the service behaviour.
- blocker: none

## T017 — 2026-10-07
- status: complete
- red/green: T017 tests were written against already-implemented GuidedExtractionService (implemented during T016). Tests confirmed behaviours: four independent property extractions, per-property failure isolation, multiple values per property, ExtractionRun grouping, backend called exactly four times. All 16 tests pass immediately after file creation.
- note: strict RED was not observed because GuidedExtractionService already existed from T016. This is recorded as an implementation-process deviation. The tests exercise all required behaviours and serve as regression coverage.
- files: `tests/unit/test_extraction_service.py`
- decision: none
- blocker: none

## T018 — 2026-10-07
- status: complete
- green: GuidedExtractionService (already in extraction.py from T016) confirmed by T017 tests. Sequential four-property extraction: ExtractionRequestFactory builds one request per property, PropertyExtractor.extract() called independently, results placed in ExtractionRun named slots (tss, caja_10, caja_35, sigma). Per-property BackendFailure → TechnicalFailure in that slot only; other slots unaffected.
- files: `src/promoter_ai_extraction/extraction.py` (GuidedExtractionService already complete)
- decision: ExtractionRun uses named slots (tss/caja_10/caja_35/sigma) rather than a generic tuple, matching the plan's "four property attempts grouped" requirement with explicit slot names for clarity.
- blocker: none

## Increment 2 checkpoint — 2026-10-07
- scope: T011–T018
- suite: `./scripts/verify.sh`
- result: 309 passed (205 from increment 1 + 104 new)
- files changed: `src/promoter_ai_extraction/normalization.py` (new), `src/promoter_ai_extraction/validation.py` (new), `src/promoter_ai_extraction/extraction.py` (new), `src/promoter_ai_extraction/models.py` (ExtractionRun added), `tests/unit/test_normalization.py` (new), `tests/unit/test_validation.py` (new), `tests/unit/test_extraction_service.py` (new), `tests/contract/__init__.py` (new), `tests/contract/test_extractor_port.py` (new), `tests/fakes.py` (new), `tests/conftest.py` (sys.path addition)
- deviations:
  - T017 RED was not observed: GuidedExtractionService was implemented in the same pass as T016 since both live in extraction.py and the service structure was clear. Tests were written and confirmed all required behaviours.
  - sys.path fix in conftest.py was required to make tests/fakes.py importable; recorded here.
- commits: none
- pushes: none

## Increment 2 Git checkpoint — 2026-10-07
- commit: `06ff0c41fe7f5649b13e690188862db60a86526c`
- message: `feat: add guided property extraction`
- pushed: `origin/feat/guided-extraction-baseline`

## T019 — 2026-10-07
- status: complete
- red: schema/serialization tests failed until `promoter_ai_extraction.persistence` existed.
- green: schema version 1 round-trips ExtractionRun slots, metadata, and enum strings.
- files: `tests/unit/test_prediction_schema.py`
- decision: persistence metadata lives on the serialized record, not on ExtractionRun.
- blocker: none

## T020 — 2026-10-07
- status: complete
- green: deterministic JSON serialization/deserialization for schema version 1.
- files: `src/promoter_ai_extraction/persistence.py`
- decision: none
- blocker: none

## T021 — 2026-10-07
- status: complete
- red: store tests failed until PredictionStore write/load behavior existed.
- green: atomic write, no overwrite, hash verification, corruption, and run isolation.
- files: `tests/unit/test_prediction_store.py`
- decision: none
- blocker: none

## T022 — 2026-10-07
- status: complete
- green: `PredictionStore.save` returns `PersistedPredictionRef`; `load_verified` returns `VerifiedPersistedPrediction` or `PersistenceFailure`.
- files: `src/promoter_ai_extraction/persistence.py`
- decision: none
- blocker: none

## T023 — 2026-10-07
- status: complete
- red: gold loader and boundary tests failed until the evaluation package existed.
- green: verified-persistence gate, synthetic header/key loading, technical workbook failures, extractor import isolation.
- files: `tests/unit/evaluation/test_gold_loader.py`, `tests/contract/test_gold_boundary.py`, `tests/synthetic_gold.py`
- decision: none
- blocker: none

## T024 — 2026-10-07
- status: complete
- green: `GoldLoader.load` accepts only `VerifiedPersistedPrediction`, then reads a local XLSX read-only/data-only.
- files: `src/promoter_ai_extraction/evaluation/gold_loader.py`, `src/promoter_ai_extraction/evaluation/__init__.py`
- decision: none
- blocker: none

## T025 — 2026-10-07
- status: complete
- red: parser tests failed until `GoldParser` existed.
- green: single values, Caja -10 ` + `, Caja -35 newline, TSS sign, sigma typography, dedup provenance, PARSE_ERROR / NEEDS_REVIEW.
- files: `tests/unit/evaluation/test_gold_parser.py`
- decision: none
- blocker: none

## T026 — 2026-10-07
- status: complete
- green: current-workset parser preserves raw, tokenizes only observed encodings, normalizes per property, fail-closes unknown syntax.
- files: `src/promoter_ai_extraction/evaluation/gold_parser.py`
- decision: none
- blocker: none

## Increment 3 local checkpoint — 2026-10-07
- scope: T019–T026
- suite: `./scripts/verify.sh`
- result: 424 passed
- persist-before-gold: `tests/contract/test_gold_boundary.py::test_persist_verified_reference_then_gold_access`
- commits for T019–T026: none
- pushes for T019–T026: none
- deferred: T027 and later

## Data-ignore tightening — 2026-10-07
- status: complete (uncommitted; fold into the T019–T026 checkpoint)
- files: `.gitignore`, `scripts/verify.sh`
- decision: ignore repo-root `/data/` and `/02-DOCS/data/` as directories. Do not use `*.txt`, `*.xml`, or `*.xlsx`. Synthetic fixtures stay versionable under `tests/fixtures/` or `tmp_path`.
- evidence:
  - `git ls-files -- data/** 02-DOCS/data/**` is empty in this worktree and in the original checkout (nothing to `git rm`).
  - `git diff --cached` lists no path under `data/` or `02-DOCS/data/`.
  - `git check-ignore -v` maps `data/gold-pmid-tei-txt/*` to `.gitignore:22:/data/` and `02-DOCS/data/gold-pmid-tei-txt/*` to `.gitignore:26:/02-DOCS/data/`.
  - 152 on-disk TEI/TXT files under `02-DOCS/data/gold-pmid-tei-txt/` are ignored (76 xml + 76 txt). Repo-root `data/` is absent on disk.
  - `tests/fixtures/synthetic_gold.xlsx` is not ignored. `./scripts/verify.sh`: 424 passed.
- note: the original checkout still has the old `data/raw/` + `data/private/` rules, so `02-DOCS/data/` (except `SUBSET_GOLD.xlsx`) remains untracked-visible there until this checkpoint lands. No `git rm` was run.
- operational risk: the original checkout at the repo root must sync this `.gitignore` (both `/data/` and `/02-DOCS/data/`) before it is used again. Until then, `git add .` there can still include `02-DOCS/data/` papers, gold, and derived files. This worktree does not modify that checkout.
- blocker: none
- commits: none

## Increment 3 Git checkpoint — 2026-10-07
- commit: `1bb5a8129de2656c7e40c92b8422b7423116266a`
- message: `feat: add persisted evaluation boundary`
- pushed: `origin/feat/guided-extraction-baseline`
- trailers: none
- merge: none
- operational risk remains: the original checkout must pull/sync this `.gitignore` before `git add .` is used there.

## T027 — 2026-10-07
- status: complete
- red: `python -m pytest tests/unit/evaluation/test_comparison.py` failed at collection — `ModuleNotFoundError: No module named 'promoter_ai_extraction.evaluation.comparison'`.
- green: 14 comparison tests pass after T028.
- files: `tests/unit/evaluation/test_comparison.py`
- decision: none
- blocker: none

## T028 — 2026-10-07
- status: complete
- green: normalized-set comparison yields EXACT_MATCH, PARTIAL_MATCH, EXTRA_VALUE, WRONG_VALUE, and MISS with TP/FP/FN. Abstention on a positive target is MISS. Rejected candidates and technical failures contribute no predicted values.
- files: `src/promoter_ai_extraction/evaluation/comparison.py`
- decision: when a prediction both misses gold values and adds extras, the row outcome is EXTRA_VALUE, not PARTIAL_MATCH.
- blocker: none

## T029 — 2026-10-07
- status: complete
- red: `python -m pytest tests/unit/evaluation/test_metrics.py` failed at collection — missing `promoter_ai_extraction.evaluation.metrics`.
- green: 8 metrics/split tests pass after T030.
- files: `tests/unit/evaluation/test_metrics.py`
- decision: none
- blocker: none

## T030 — 2026-10-07
- status: complete
- green: per-property precision/recall/F1/exact-row accuracy; texto_explicito and imagen_only recall strata; separate parse-failure and technical-failure counts; coverage = evaluated / (evaluated + technical_failures); paper-grouped split validator rejects shared PMIDs; positive-only limitation text is required on every report.
- files: `src/promoter_ai_extraction/evaluation/metrics.py`
- decision: none
- blocker: none

## T031 — 2026-10-07
- status: blocked
- blocker: HUMAN_DECISION_REQUIRED — final headline treatment of technical failures in denominators. Existing separate failure/coverage metrics are implemented and unchanged. This does not block T032–T035. It blocks only the frozen T042 benchmark protocol.
- files: none
- decision: none — not invented.

## T032 — 2026-10-07
- status: complete
- red: `python -m pytest tests/contract/test_leakage_ordering.py` failed at collection — missing `EvaluationService`.
- green: 4 contract tests pass after T033. In-memory runs and failed persistence record zero gold-loader calls.
- files: `tests/contract/test_leakage_ordering.py`
- decision: none
- blocker: none

## T033 — 2026-10-07
- status: complete
- green: `EvaluationService.evaluate` accepts only `PersistedPredictionRef`, verifies persistence, then opens gold. Direct `ExtractionRun` and `PersistenceFailure` are rejected.
- files: `src/promoter_ai_extraction/evaluation/service.py`
- decision: none
- blocker: none

## T034 — 2026-10-07
- status: complete
- red: `python -m pytest tests/integration/test_guided_baseline.py` failed at collection — missing `promoter_ai_extraction.application`.
- green: parametrized TXT and TEI synthetic flows pass after T035.
- files: `tests/integration/__init__.py`, `tests/integration/test_guided_baseline.py`
- decision: none
- blocker: none

## T035 — 2026-10-07
- status: complete
- green: `GuidedBaselineApplication` wires document load → guided extraction → immutable persistence → evaluation. Scripted backend plus synthetic XLSX under `tmp_path`. TXT and TEI both score four exact property rows.
- files: `src/promoter_ai_extraction/application.py`
- decision: none
- blocker: none

## Increment 4 local checkpoint — 2026-10-07
- scope: T027–T030 and T032–T035; T031 remains HUMAN_DECISION_REQUIRED
- suite: `./scripts/verify.sh`
- result: 452 passed
- commits for this increment: none
- pushes for this increment: none
- deferred: T036 and later

## T031 — 2026-10-07 (resolved)
- status: complete
- red: not applicable (decision log, not code)
- green: `02-DOCS/wiki/sdd/decisions.md` records the approved headline protocol
- files: `02-DOCS/wiki/sdd/decisions.md`
- decision: end-to-end headline treats technical failure + positive gold as FN; conditioned scientific metrics remain secondary; coverage, technical-failure count/rate, and scientific abstentions stay separate; types never mix (constitution principle 6); positive-only subset limitation remains explicit
- blocker: none
- note: T027–T035 code still reports separate failure/coverage counts. Dual-view wiring belongs with the T042 report, not this checkpoint.

## T036 — 2026-10-08
- status: complete
- red: not applicable (decision log, not code)
- green: `02-DOCS/wiki/sdd/decisions.md` records provider OpenAI, Responses API, model `gpt-6.1-sol`, env-only `OPENAI_API_KEY`, strict JSON-schema structured output, no fallback, fail-closed context handling, and reproducibility metadata
- files: `02-DOCS/wiki/sdd/decisions.md`
- decision: `PropertyExtractor` → `ModelBackend` → `OpenAIModelBackend`; prompt from `SafeExtractionInput` only; provider/schema/parse failures are technical failures
- blocker: none
- note: T037–T038 were not started. The `openai` SDK is not added in this step.

## T037 — 2026-10-08
- status: complete
- red: `python -m pytest tests/contract/test_real_backend_adapter.py` failed at collection — `promoter_ai_extraction.backends` did not exist
- green: `uv run pytest tests/contract/test_real_backend_adapter.py tests/contract/test_extractor_port.py tests/contract/test_gold_boundary.py` — 39 passed; fake Responses client; no network
- files: `tests/contract/test_real_backend_adapter.py`
- decision: none
- blocker: none
- note: not committed; held for review with T038

## T038 — 2026-10-08
- status: complete
- green: `uv sync --frozen` audited 23 packages; `./scripts/verify.sh` — 464 passed
- files: `src/promoter_ai_extraction/backends/__init__.py`, `src/promoter_ai_extraction/backends/openai_backend.py`, `src/promoter_ai_extraction/extraction.py`, `tests/contract/test_gold_boundary.py`, `pyproject.toml`, `uv.lock`
- decision: official `openai==3.26.1`; Responses API `text.format` json_schema strict; published gpt-6.1-sol window 1,050,000 context / 128,000 max output (https://developers.openai.com/api/docs/models/gpt-6.1-sol); preflight uses Unicode length as a conservative token upper bound; `DOCUMENT_TOO_LARGE` without truncation; optional payload fields encoded as required+nullable; `PropertyExtractor` preserves non-scientific `BackendFailure.code`; document hash stays on persistence/`LoadedDocument`, not in the prompt
- blocker: none
- note: no live `OPENAI_API_KEY` call; T037–T038 remain uncommitted pending review

## T037–T038 review fixes — 2026-10-08
- status: complete
- red: 9 new adapter assertions failed (truncation, extra fields, non-string value_raw, incomplete JSON, response.error, structured context error, injected environ api_key, output-budget preflight)
- green: `uv run pytest tests/contract/test_real_backend_adapter.py tests/contract/test_extractor_port.py tests/contract/test_gold_boundary.py` — 46 passed; `./scripts/verify.sh` — 471 passed
- files: `src/promoter_ai_extraction/backends/openai_backend.py`, `tests/contract/test_real_backend_adapter.py`
- decision: character-length fail-closed budget = published context − max output − measured schema JSON; not a tokenizer. Responses `status`/`error`/`incomplete_details` inspected before scientific accept. `OpenAI(api_key=secret)` from `self._environ`. `truncation="disabled"` explicit.
- blocker: none
- note: `document_hash` remains None in adapter metadata for later persist wiring; no live API call; uncommitted

