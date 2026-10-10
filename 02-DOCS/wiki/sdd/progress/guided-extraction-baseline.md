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

## T039 — 2026-10-08
- status: complete
- red: `tests/unit/test_development_manifest.py` failed at collection — `promoter_ai_extraction.manifest` missing
- green: T039 tests + `test_boundary` + gold isolation 127 passed; `./scripts/verify.sh` — 481 passed
- files: `src/promoter_ai_extraction/manifest.py`, `src/promoter_ai_extraction/boundary.py`, `tests/unit/test_development_manifest.py`, `tests/fixtures/synthetic_safe_manifest.json`, `tests/contract/test_gold_boundary.py`, `scripts/verify.sh`
- decision: development-manifest rows are paper × promoter (document reference + identities). No `property` column — the runner applies the fixed four-property set (spec §Inputs). No gold/evaluator columns. Real file path `02-DOCS/data/safe-development-manifest.json` stays git-ignored; tests use a synthetic fixture. Case selection for the real local run is deferred to T042 (human-authored untracked file).
- blocker: none
- note: T039 does not copy or derive cases from SUBSET_GOLD.xlsx. Uncommitted.

## T040 — 2026-10-08
- status: complete (RED; GREEN is T041)
- red: `uv run pytest tests/integration/test_baseline_runner.py` — collection `ModuleNotFoundError: No module named 'promoter_ai_extraction.baseline'`
- green: deferred to T041 (`src/promoter_ai_extraction/baseline.py`)
- triangulation: persist-before-gold via `GoldLoader.load` monkeypatch; leaky GT column rejected without gold; TIMEOUT vs `INSUFFICIENT_EVIDENCE`; `predictions/` git-ignore; no-overwrite second run; extractor never sees gold/evaluator fields
- files: `tests/integration/test_baseline_runner.py`
- decision: none. Runner API follows T041 Interfaces (`BaselineRunner.run(manifest, documents, gold, predictions, report)`). Stable `run_id` per paper × promoter is implied by the no-overwrite assertion; not a new scientific contract.
- blocker: none
- note: synthetic papers/gold/manifest only under `tmp_path`. No `SUBSET_GOLD.xlsx`, no real documents, no live OpenAI. `./scripts/verify.sh` exits 2 until T041. T039 remains uncommitted. T041 not started.

## T041 — 2026-10-08
- status: complete
- red: T040 collection failed for missing `promoter_ai_extraction.baseline`
- green: `uv run pytest tests/integration/test_baseline_runner.py -vv` — 7 passed (assertions executed, not import-only); `./scripts/verify.sh` — 488 passed
- files: `src/promoter_ai_extraction/baseline.py`
- decision: none. `BaselineRunner` reuses `DevelopmentManifestLoader` and `GuidedBaselineApplication`. Stable `run_id` is `{paper_id}__{promoter_name}` so `PredictionStore` no-overwrite holds. Report JSON writes counts + `limitation_note` after a successful evaluate. CLI `python -m` remains T042.
- blocker: none
- note: no contract edits; no live OpenAI; no real papers or `SUBSET_GOLD.xlsx`. T039–T041 remain uncommitted. T042 not started.

## T039–T041 review follow-up — 2026-10-08
- status: complete
- red: duplicate paper × promoter loaded; absolute/`../`/symlink-escape paths reached extraction
- green: `uv run pytest tests/unit/test_development_manifest.py tests/integration/test_baseline_runner.py tests/contract/test_gold_boundary.py` — 30 passed; `./scripts/verify.sh` — 495 passed
- files: `src/promoter_ai_extraction/manifest.py`, `src/promoter_ai_extraction/baseline.py`, `tests/unit/test_development_manifest.py`, `tests/integration/test_baseline_runner.py`
- decision: identity for duplicates is exact `(paper_id, promoter_name)`. Path confinement uses `Path.resolve()` (follows symlinks) and `is_relative_to`; absolute paths and escapes return `TechnicalFailure(code="PATH_OUTSIDE_ROOT")` before `DocumentSource` is opened. Not an OS sandbox.
- blocker: none
- note: uncommitted. T042 not started.

## T042 — 2026-10-09 (code + synthetic tests; live run deferred)
- status: partial — CLI, fingerprints, dual-view JSON report, and synthetic tests are green. The live done-check (real local papers, human-authored manifest, OpenAI) is not started.
- red: `tests/unit/evaluation/test_dual_view.py` and `tests/integration/test_baseline_cli.py` failed at collection (`headline_property_counts` / `main` missing).
- green: `uv run pytest tests/unit/evaluation/test_dual_view.py tests/integration/test_baseline_cli.py tests/contract/test_real_backend_adapter.py tests/integration/test_baseline_runner.py` — 42 passed; `./scripts/verify.sh` — 506 passed. No live OpenAI.
- files: `src/promoter_ai_extraction/baseline.py`, `src/promoter_ai_extraction/application.py`, `src/promoter_ai_extraction/backends/openai_backend.py`, `src/promoter_ai_extraction/evaluation/metrics.py`, `src/promoter_ai_extraction/evaluation/report.py`, `src/promoter_ai_extraction/evaluation/service.py`, `tests/unit/evaluation/test_dual_view.py`, `tests/integration/test_baseline_cli.py`, `tests/contract/test_real_backend_adapter.py`
- decision: `python -m promoter_ai_extraction.baseline` with `--manifest/--documents/--gold/--predictions/--report`. Reuses `BaselineRunner` and `GuidedBaselineApplication`. Persistence `system_fingerprint` stores `common` generation metadata plus per-property `model_snapshot`/`system_fingerprint`; `document_hash` comes from `LoadedDocument` at save time, never from the adapter. Report headline is `end_to_end` (TF on positive gold adds FN); `scientific` is diagnostic and does not count TF as abstention. CLI maps `BoundaryViolation` and non-`EvaluationReport` outcomes to exit 1; argparse missing flags stay non-zero. A TF inside a persisted four-property run still yields exit 0 with both views in JSON.
- blocker: live T042 done-check needs a human-authored ignored case list, a cost cap, and `OPENAI_API_KEY`. Not configured in this increment.
- note: no `SUBSET_GOLD.xlsx`, no real TEI/TXT, no PMID selection, no credentials, no T043+. Uncommitted.

## T042 review follow-up — 2026-10-09
- status: complete (code + synthetic tests). Live done-check still deferred.
- red: dual-view/CLI tests failed for missing `technical_failure_gold_values`, missing `technical_failure_rate`, multi-value FN=2, and missing-key CLI still exiting 0.
- green: focused dual-view + CLI + persistence + metrics 57 passed; `./scripts/verify.sh` — 510 passed. No live OpenAI.
- files: `02-DOCS/wiki/sdd/decisions.md`, `src/promoter_ai_extraction/evaluation/metrics.py`, `src/promoter_ai_extraction/evaluation/service.py`, `src/promoter_ai_extraction/evaluation/report.py`, `src/promoter_ai_extraction/baseline.py`, `tests/unit/evaluation/test_dual_view.py`, `tests/integration/test_baseline_cli.py`
- decision: T031 clarified — TF on multi-value gold adds FN per gold value; `technical_failures` stays one attempt. CLI preflights `OPENAI_API_KEY` before constructing `OpenAIModelBackend`. Report emits `technical_failure_rate = TF / (evaluated_rows + TF)`.
- blocker: live T042 still needs a human case list, cost cap, and credentials. Not run here.
- note: six root contracts unchanged. Uncommitted. No T043.

## T042 follow-up — 2026-10-09 (TSS typographic minus + numeric ID_paper)
- status: complete for these two defects. Live T042 still not run. Not checkpointed.
- red: `Ϫ12` and `−12` stayed unfolder; integer and integer-float `ID_paper` returned `CORRUPT_WORKBOOK`. ASCII `-12`, unsigned `12`, prose containing U+03EA, fractional ids, and boolean ids already behaved as required.
- green: `uv run pytest tests/unit/test_normalization.py tests/unit/evaluation/test_gold_loader.py tests/unit/evaluation/test_gold_parser.py` — 95 passed.
- files: `src/promoter_ai_extraction/normalization.py`, `src/promoter_ai_extraction/evaluation/gold_loader.py`, `tests/unit/test_normalization.py`, `tests/unit/evaluation/test_gold_loader.py`, `02-DOCS/wiki/sdd/decisions.md`
- decision: fold U+03EA and U+2212 only on a whole integer token. Convert unambiguous numeric `ID_paper` to text. Do not touch curator target cells or source documents.
- blocker: none for this increment. Live OpenAI case still unauthorized.
- note: no prompt change, no T043, no commit.

## T042 cost control — 2026-10-09
- status: complete for the cap and retry switch. Live call still not run. Not checkpointed.
- red: constructor rejected `max_output_tokens`; metadata had no `max_retries`; CLI help lacked `--max-output-tokens`; `--max-output-tokens 4096` was an unrecognized argument.
- green: adapter, CLI, and reproducibility tests after the implementation. `./scripts/verify.sh` recorded in the session report.
- files: `src/promoter_ai_extraction/backends/openai_backend.py`, `src/promoter_ai_extraction/baseline.py`, `tests/contract/test_real_backend_adapter.py`, `tests/integration/test_baseline_cli.py`, `02-DOCS/wiki/sdd/decisions.md`
- decision: default output cap stays 128000. CLI can set a positive integer. Live client uses `max_retries=0`. No new gitignore rule. The real manifest stays untracked.
- blocker: the live run is still not authorized.
- note: no OpenAI call, no gold edit, no commit.

## Anthropic provider — 2026-10-09
- status: code and synthetic tests complete. Not checkpointed. No live call.
- red: `tests/contract/test_anthropic_backend.py` failed collection because `AnthropicModelBackend` did not exist.
- green: `./scripts/verify.sh` — 551 passed.
- files: `src/promoter_ai_extraction/backends/anthropic_backend.py`, `src/promoter_ai_extraction/backends/__init__.py`, `src/promoter_ai_extraction/baseline.py`, `tests/contract/test_anthropic_backend.py`, `tests/integration/test_baseline_cli.py`, `pyproject.toml`, `uv.lock`, `02-DOCS/wiki/sdd/decisions.md`
- decision: second adapter behind `ModelBackend`. Messages `output_config.format` json_schema. Model `claude-sonnet-5-5`. Default cap 4096 only for Anthropic. `max_retries=0`. No fallback. OpenAI stays the CLI default.
- blocker: a real Anthropic call is not authorized.
- note: `runs/t042-real-01` was not modified. No T043. No commit.

## T042 — 2026-10-09 (controlled real runs; documentary close)

- status: complete for the controlled-execution done-check. This records that the baseline ran on one real local case and wrote a report. It does not record scientific performance on the workset.
- evidence: gitignored `runs/t042-real-01` and `runs/t042-real-02`. This close did not re-execute either run and did not rewrite the prediction or the report. No gold value, document excerpt, or absolute private path is copied here.
- functioning — OpenAI `t042-real-01`: provider `openai`, model `gpt-6.1-sol`, `max_output_tokens` 4096, `max_retries` 0. Four property slots are `technical_failure` / `PROVIDER_ERROR`. Each persisted message identifies `RateLimitError` and does not store an HTTP status. There is no scientific extraction. Report: `evaluated_rows` 0, `technical_failures` 3, `technical_failure_rate` 1.0, `scientific_abstentions` 0, `coverage` 0.0, end-to-end TP 0, FP 0, FN 3. The report counts three technical failures because factor sigma has `n_targets` 0. Parser `current-workset-v1`. Prompt `safe-extraction-v1`.
- functioning — Anthropic `t042-real-02`: provider `anthropic`, model `claude-sonnet-5-5`, API `messages`, `max_output_tokens` 4096, `max_retries` 0. One case: paper `10400579`, promoter `yicRp`, `run_id` `10400579__yicRp`. Four scientific outcomes and no technical failure: TSS `EXTRACTED`, Caja -10 `AMBIGUOUS`, Caja -35 `NOT_FOUND`, factor sigma `NOT_FOUND`. Report: `evaluated_rows` 3, `technical_failures` 0, `technical_failure_rate` 0.0, `scientific_abstentions` 2, `parse_failures` 0, `coverage` 1.0. Headline `end_to_end`. Parser `current-workset-v1`. Schema `raw-property-payload-v1`. Per-property counts are present. The scientific view includes `recall_texto_explicito` and `recall_imagen_only`. `limitation_note` is present.
- scientific performance — not claimed. Historical totals on `t042-real-02` are TP 0, FP 1, FN 3, `n_targets` 3, in both views. TSS is the FP: `value_normalized` stayed a non-integer documentary expression, equal to `value_raw`, with a null derivation note. Caja -10 and Caja -35 are the two scientific abstentions and the other two FN. Factor sigma has `n_targets` 0. These counts describe one development case. They are not a workset score.
- later normalizer: `8ceb02e` teaches the TSS normalizer to read one explicit anchored distance. That commit did not change `t042-real-02`. The historical mismatch stands. Syntactic normalization of an anchored distance does not by itself prove that the distance is the TSS rather than another regulatory feature.
- done-check: `t042-real-02` is the controlled execution. Its report has per-property metrics, modality strata, coverage, failures, and parser/model versions. `runs/` is ignored. This close does not stage predictions, reports, the workbook, or the case manifest.
- acceptance trace for this case, not a new test: AC-19 and AC-20 hold because the prediction file exists and the report scores that persisted run without altering it. AC-21–AC-24 are visible in the report. AC-25 is not claimed: one case does not assign the workset to development and test. AC-26 holds because the limitation note is present and this close does not claim a false-assertion rate or abstention appropriateness for the 329-row subset.
- blocker: none for T042. T043 and T044 are not started.
- files: `02-DOCS/wiki/sdd/progress/guided-extraction-baseline.md`, `02-DOCS/wiki/sdd/decisions.md`
- note: no code, no tests, no root-contract edit, no API call, no rescore. Prior T042 entries above remain the record of what was true when they were written.

## T043 — 2026-10-09 (deterministic suite and scope audit)

- status: complete. The done-check passes. This audit does not start T044 and does not add FastAPI, RAG, agents, or deployment.
- green: `./scripts/verify.sh` exited 0. Pytest: 561 passed in 3.01s. The gate also confirmed `data/`, `02-DOCS/data/`, `02-DOCS/data/SUBSET_GOLD.xlsx`, and `02-DOCS/data/safe-development-manifest.json` are git-ignored, and `tests/fixtures/synthetic_gold.xlsx` plus `tests/fixtures/synthetic_safe_manifest.json` are not.
- scope: runtime dependencies in `pyproject.toml` are `openpyxl`, `defusedxml`, `openai`, and `anthropic`. The dev group is `pytest`. `uv.lock` adds only their transitive packages (`pydantic`, `httpx2`, `httpcore2`, and the rest of those SDK stacks). No FastAPI, LangChain, LiteLLM, vector client, database driver, frontend, or deployment manifest. `src/` imports those four libraries plus the standard library. `openai` and `anthropic` are imported inside the live-client constructors, not at module import. No Dockerfile or service manifest.
- privacy: `git ls-files` has no `.env`, no `SUBSET_GOLD.xlsx`, no `runs/`, and no real TEI/TXT. `.env`, `runs/t042-real-01`, and `runs/t042-real-02` are ignored. The only tracked dotenv path is `01-TOOLS/_TEMPLATE/.env.example`. Run artifact mtimes are unchanged: `1791592748` and `1791603651`.
- leakage: `GoldLoader` is imported by the evaluation service, not by extraction or the backends. `boundary.py` still rejects forbidden field names before the allowlist, including nested keys. The six root contracts have no diff against `8ceb02e`. Tests use synthetic fixtures. The string `SUBSET_GOLD` in the Anthropic contract test is a denylist sentinel, not the workbook. The Anthropic client in that test is monkeypatched.
- AC-01–AC-33: the plan assigns these to the deterministic suite and this dependency inspection. The suite passed and the inspection found no out-of-scope dependency. AC-27 holds for this slice.
- blocker: none.
- files: `02-DOCS/wiki/sdd/progress/guided-extraction-baseline.md`
- note: no code, dependency, contract, or prediction edit. No provider call. T044 is not started.

## T044 — 2026-10-09 (evidence map and baseline documentary close)

- status: complete. `guided-extraction-baseline` T001–T044 meet their recorded done-checks. This section is the map. It does not replace the entries above and does not copy a private value, credential, absolute path, prediction, or gold cell.
- done-check: each task below points at the command or result already written in its section. T042's controlled local evidence stays in `T042 — 2026-10-09 (controlled real runs; documentary close)`.
- suite reading: T043 records `./scripts/verify.sh` with 561 passed. That is one synthetic, contract, and integration run. It is not 561 papers and not 561 independent scientific cases.

### Evidence classes

- Deterministic: T001–T041, the synthetic portions of T042, and T043. Inputs are `tests/fixtures/` or `tmp_path`. No live provider call is part of that evidence.
- Real functioning: gitignored `runs/t042-real-02`. One case. Claude `claude-sonnet-5-5`. A report was written. Counts stay in the T042 close section and are not a workset score.
- Technical failure: gitignored `runs/t042-real-01`. Four property slots are `PROVIDER_ERROR` / `RateLimitError`. No scientific extraction. The report's `technical_failures` count is 3 because factor sigma has `n_targets` 0.
- Scientific limitation: the stored Anthropic totals are not corpus performance. The TSS normalized value in that artifact remained a documentary expression. `8ceb02e` did not rewrite it. An anchored distance the normalizer can parse is not, by that parse alone, proof that the distance is the TSS.

### Task map

| ID | Final status | Checkable result |
|---|---|---|
| T001 | complete | Real workbook path ignored; `tests/fixtures/synthetic_gold.xlsx` not ignored. |
| T002 | complete | `./scripts/verify.sh` exits 0 after package setup. |
| T003 | complete | Domain-model tests pass after T004. |
| T004 | complete | `tests/unit/test_models.py`: four properties, five scientific statuses, technical-failure separation. |
| T005 | complete | TXT suite passes after T006. |
| T006 | complete | `tests/unit/test_txt_loader.py`. |
| T007 | complete | TEI suite passes after T008. |
| T008 | complete | `tests/unit/test_tei_loader.py`, `defusedxml`. |
| T009 | complete | Boundary RED cases pass after T010. |
| T010 | complete | `tests/unit/test_boundary.py`: allowlist, denylist, no gold path on the request. |
| T011 | complete | 52 normalization tests pass after T012. |
| T012 | complete | `tests/unit/test_normalization.py`. |
| T013 | complete | 19 validator tests pass after T014. |
| T014 | complete | `tests/unit/test_validation.py`. |
| T015 | complete | 17 extractor-port contract tests pass after T016. |
| T016 | complete | `tests/contract/test_extractor_port.py`. `SafeExtractionInput` has no gold fields. |
| T017 | complete | `tests/unit/test_extraction_service.py`, 16 tests. No observed RED: the service already existed from T016. |
| T018 | complete | Same service. Four slots. One slot's failure does not change the others. |
| T019 | complete | Schema version 1 round-trip. |
| T020 | complete | `tests/unit/test_prediction_schema.py`. |
| T021 | complete | Atomic write, no overwrite, hash check. |
| T022 | complete | `tests/unit/test_prediction_store.py`. |
| T023 | complete | Gold loader waits for a verified persisted prediction. |
| T024 | complete | `tests/unit/evaluation/test_gold_loader.py`. |
| T025 | complete | Parser cases, including Caja -10 ` + ` and fail-closed unknown syntax. |
| T026 | complete | `tests/unit/evaluation/test_gold_parser.py`. |
| T027 | complete | 14 comparison tests pass after T028. |
| T028 | complete | `tests/unit/evaluation/test_comparison.py`. |
| T029 | complete | 8 metrics and split tests pass after T030. |
| T030 | complete | `tests/unit/evaluation/test_metrics.py`. Synthetic paper-grouped split. Positive-only limitation text. |
| T031 | complete | First entry was blocked. Authority is `T031 — 2026-10-07 (resolved)` plus the 2026-10-09 multi-value clarification in `decisions.md`. |
| T032 | complete | In-memory runs record zero gold-loader calls. |
| T033 | complete | `tests/contract/test_leakage_ordering.py` and `tests/contract/test_gold_boundary.py`. |
| T034 | complete | Synthetic TXT and TEI flows pass after T035. |
| T035 | complete | `tests/integration/test_guided_baseline.py`. |
| T036 | complete | Decision: OpenAI Responses API, `gpt-6.1-sol`. |
| T037 | complete | `tests/contract/test_real_backend_adapter.py` with a fake client. No network. |
| T038 | complete | OpenAI adapter. Review follow-up: 46 passed in the focused contract files; `./scripts/verify.sh` 471 passed. |
| T039 | complete | `tests/unit/test_development_manifest.py`. Real manifest path stays ignored. |
| T040 | complete as RED | Green is T041, by the task split. |
| T041 | complete | `tests/integration/test_baseline_runner.py`, 7 passed; later review follow-up 30 passed. |
| T042 | complete for the controlled run | Synthetic CLI evidence is in the earlier T042 sections (`tests/integration/test_baseline_cli.py`, `tests/unit/evaluation/test_dual_view.py`). Live evidence is only the T042 close section. |
| T043 | complete | `./scripts/verify.sh`, 561 passed. No FastAPI, RAG, agent, frontend, deployment, vector, or database dependency. |

### Acceptance map

Grouped coverage is the plan table "Acceptance-criterion coverage". These files exist and match those groups. This map does not assign one test function to each AC.

| Criteria | Tasks | Existing tests |
|---|---|---|
| AC-01–AC-03 | T005–T008 | `tests/unit/test_txt_loader.py`, `tests/unit/test_tei_loader.py` |
| AC-04, AC-09 | T016–T018 | `tests/unit/test_extraction_service.py`, `tests/contract/test_extractor_port.py` |
| AC-05, AC-10 | T016 | `tests/contract/test_extractor_port.py` |
| AC-06–AC-08 | T011–T012 | `tests/unit/test_normalization.py` |
| AC-11–AC-16 | T006–T018 | Loader, extraction, and port tests above |
| AC-17–AC-18 | T013–T014 | `tests/unit/test_validation.py` |
| AC-19–AC-20 | T023–T033 | `tests/contract/test_leakage_ordering.py`, `tests/contract/test_gold_boundary.py` |
| AC-21–AC-26 | T027–T031, T042 | `tests/unit/evaluation/test_comparison.py`, `tests/unit/evaluation/test_metrics.py`, `tests/unit/evaluation/test_dual_view.py` |
| AC-27 | T002, T043 | `pyproject.toml`, `uv.lock`, T043 scope notes |
| AC-28–AC-30 | T009–T014, T037–T038 | `tests/unit/test_boundary.py`, `tests/unit/test_models.py`, both backend contract tests |
| AC-31–AC-33 | T025–T026 | `tests/unit/evaluation/test_gold_parser.py` |

AC-25 is covered by the synthetic split validator in `tests/unit/evaluation/test_metrics.py`. The one real case does not assign the workset to development and test. AC-26 is the limitation note. Neither AC is a corpus-performance claim.

### Traceability gaps

- There is no file that pairs each of AC-01–AC-33 with one test function. The plan groups them.
- T017 did not show a failing test first.
- The cost-control progress entry does not record a pytest count. Later checkable counts are 551 after the Anthropic adapter and 561 at T043.
- Entries written before the live runs still say the live done-check was not started. The T042 close section is the authority for that done-check.
- Constitution Definition of Done also asks for a branch and a pull request. That merge is not T044. This close does not open one.

### Outside this baseline

FastAPI, RAG, agents, and a demonstration stay in the plan section "Post-baseline course milestones". They are not tasks T001–T044 and this map does not start them.

- blocker: none.
- files: `02-DOCS/wiki/sdd/progress/guided-extraction-baseline.md`, `02-DOCS/wiki/sdd/decisions.md`
- note: no code, test, dependency, root-contract, or prediction edit. No provider call. `t042-real-02` metrics were not restated as a new measurement.

