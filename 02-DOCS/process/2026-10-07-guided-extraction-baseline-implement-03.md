---
type: process-report
title: Guided extraction baseline — IMPLEMENT 03
date: 2026-10-07
feature: guided-extraction-baseline
phase: implement
scope: T019-T026
---

# IMPLEMENT 03 — guided-extraction-baseline

## Objective

Checkpoint T011–T018, then implement T019–T026: immutable local prediction persistence and evaluator-only gold loading/parsing.

## Foundation checkpoint (T011–T018)

- Commit: `06ff0c41fe7f5649b13e690188862db60a86526c`
- Message: `feat: add guided property extraction`
- Remote: `origin/feat/guided-extraction-baseline`
- Trailers: none
- Pre-checkpoint gate: `uv sync --frozen` and `./scripts/verify.sh` passed

This commit already existed on the isolated worktree and on origin at the start of the increment. It was re-verified, not rewritten.

## Completed tasks

### T019–T022 — persistence

- Schema version 1 deterministic JSON for `ExtractionRun`.
- Local write-once `PredictionStore` with atomic rename.
- `PersistedPredictionRef` plus `load_verified` → `VerifiedPersistedPrediction`.
- Overwrite attempts return `FILE_EXISTS` and leave the original file unchanged.
- Corrupt, missing, incomplete, and wrong-schema files remain technical `PersistenceFailure`.

### T023–T026 — evaluator-only gold

- `GoldLoader.load` requires `VerifiedPersistedPrediction`.
- In-memory `ExtractionRun` is rejected without opening gold.
- Synthetic XLSX under `tmp_path` only (sheet `Hoja1`, headers on row 4).
- `GoldParser` preserves `gold_value_raw`, tokenizes only current-workset encodings, then normalizes and deduplicates.
- Unknown syntax returns `PARSE_ERROR / NEEDS_REVIEW`.
- Extraction modules do not import the evaluation package.

## Persist → verified reference → gold access

Contract test `tests/contract/test_gold_boundary.py::test_persist_verified_reference_then_gold_access` records the order:

1. extraction run in memory
2. `PredictionStore.save` + `load_verified`
3. `GoldLoader.load` on a synthetic workbook

An in-memory run against a missing path fails with `MISSING_VERIFIED_PERSISTENCE`, not `FILE_NOT_FOUND`.

## Tests

- Full gate: `./scripts/verify.sh`
- Result: 424 passed, 0 failed
- Fixtures: synthetic only

## Files

Created:

- `src/promoter_ai_extraction/persistence.py`
- `src/promoter_ai_extraction/evaluation/__init__.py`
- `src/promoter_ai_extraction/evaluation/gold_loader.py`
- `src/promoter_ai_extraction/evaluation/gold_parser.py`
- `tests/synthetic_gold.py`
- `tests/unit/test_prediction_schema.py`
- `tests/unit/test_prediction_store.py`
- `tests/unit/evaluation/__init__.py`
- `tests/unit/evaluation/conftest.py`
- `tests/unit/evaluation/test_gold_loader.py`
- `tests/unit/evaluation/test_gold_parser.py`
- `tests/contract/test_gold_boundary.py`

Modified:

- `02-DOCS/wiki/sdd/progress/guided-extraction-baseline.md`
- `.gitignore` (data-ignore tightening; fold into this checkpoint)
- `scripts/verify.sh` (ignore probes for `/data/` and `/02-DOCS/data/`)

## Decisions and deviations

- No new scientific, leakage, evaluation, scope, or material architectural decision.
- T019–T022 were already present in the worktree as untracked files at the start of this increment; they were kept, verified, and not rewritten.
- T023–T026 first RED was a missing-module collection failure, then behavioral assertions.
- No runtime dependency was added (`openpyxl` already present).
- Gold parser does not apply documentary TSS distance derivation to gold cells.

## Scope and security

- T027 and later were not started.
- Six authoritative root documents remain unchanged.
- Knowledge-sync remains disabled.
- T019–T026 plus this gitignore tightening remain uncommitted. No commit was created for the data-ignore change.

## Data-ignore tightening (pre-checkpoint)

Requested policy: treat `data/` as local/non-versionable. Do not use global `*.txt` / `*.xml` / `*.xlsx`.

On disk, repo-root `data/` is absent. The real subset lives at `02-DOCS/data/gold-pmid-tei-txt/` (152 TEI/TXT files), with `SUBSET_GOLD.xlsx`, `copy_gold_files.sh`, and `gold_pmid_list.txt` beside it.

`.gitignore` now has two root-only directory rules:

- `/data/` — requested path, including a future `data/gold-pmid-tei-txt/` or `data/SUBSET_GOLD.xlsx`
- `/02-DOCS/data/` — current on-disk location of the same class of files

The exact rule `02-DOCS/data/SUBSET_GOLD.xlsx` is kept as a named belt-and-suspenders line.

Verification:

- Tracked under `data/` or `02-DOCS/data/`: none. No `git rm`.
- Staged under those trees: none.
- `git check-ignore -v data/gold-pmid-tei-txt/example.xml` → `.gitignore:22:/data/`
- `git check-ignore -v` on all 152 on-disk papers → `.gitignore:26:/02-DOCS/data/`
- `tests/fixtures/synthetic_gold.xlsx` is not ignored (`git check-ignore` exit 1)
- `./scripts/verify.sh`: 424 passed

## Operational risk — original checkout gitignore lag

The original checkout (not this worktree) still uses `data/raw/` + `data/private/`. Git lists `?? 02-DOCS/data/` there; only `SUBSET_GOLD.xlsx` is ignored.

That checkout must sync this `.gitignore` (`/data/` and `/02-DOCS/data/`) before it is used again. Until then, `git add .` there can still include papers, gold, and derived files under `02-DOCS/data/`.

This worktree does not modify that checkout. No merge is performed.
