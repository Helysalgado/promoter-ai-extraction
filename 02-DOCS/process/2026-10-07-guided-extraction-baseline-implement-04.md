---
type: process-report
title: Guided extraction baseline — IMPLEMENT 04
date: 2026-10-07
feature: guided-extraction-baseline
phase: implement
scope: T027-T035
---

# IMPLEMENT 04 — guided-extraction-baseline

## Objective

Checkpoint T019–T026, then implement T027–T035: set comparison, metrics, persist-before-gold evaluation, and synthetic TXT/TEI end-to-end wiring.

## Foundation checkpoint (T019–T026)

- Commit: `1bb5a8129de2656c7e40c92b8422b7423116266a`
- Message: `feat: add persisted evaluation boundary`
- Remote: `origin/feat/guided-extraction-baseline`
- Trailers: none
- Merge: none
- Pre-checkpoint gate: `uv sync --frozen` and `./scripts/verify.sh` passed with 424 tests
- `.gitignore` includes both `/data/` and `/02-DOCS/data/`

## Operational risk

The original checkout still needs to sync this `.gitignore` before it is used again. Until then, `git add .` there can include `02-DOCS/data/`. This worktree did not modify that checkout.

## Completed tasks

### T027–T028 — set comparison

- Normalized unordered sets, keyed by paper × promoter × property.
- Outcomes: `EXACT_MATCH`, `PARTIAL_MATCH`, `EXTRA_VALUE`, `WRONG_VALUE`, `MISS`.
- Value-level TP/FP/FN.
- Abstention on a positive target is `MISS`.
- Rejected candidates do not count as predictions.
- Technical failures yield no predicted set.

### T029–T030 — metrics and splits

- Per-property precision, recall, F1, exact-row accuracy.
- `texto_explicito` and `imagen_only` recall strata.
- Parse failures and technical failures counted separately from value metrics.
- Coverage = evaluated rows / (evaluated rows + technical failures).
- Paper-grouped split validator rejects a paper on both sides.
- Every report includes the positive-only limitation text (AC-26).

### T031 — resolved at checkpoint

Human decision recorded in `02-DOCS/wiki/sdd/decisions.md`:

- Headline = end-to-end view: technical failure + positive gold → FN.
- Secondary = scientific metrics conditioned on technically evaluable cases.
- Always report coverage, technical-failure count, technical-failure rate, and scientific abstentions separately.
- Never convert technical failure ↔ scientific abstention.
- Positive-only subset limitation remains explicit.

Dual-view metric wiring is deferred to T042. T027–T035 keep the existing separate failure/coverage counts.

### T032–T033 — EvaluationService

- `evaluate(PersistedPredictionRef, gold_path)` only.
- In-memory `ExtractionRun` and failed persistence never open gold.
- Gold loader call count stays zero on those paths.

### T034–T035 — synthetic end-to-end

- `GuidedBaselineApplication` loads TXT or TEI, extracts with a scripted backend, persists, then evaluates a synthetic workbook under `tmp_path`.
- Both formats score four exact property rows.

## Tests

- Increment tests: 56 passed (comparison, metrics, leakage, integration).
- Full gate: `./scripts/verify.sh`
- Result: 452 passed, 0 failed
- Fixtures: synthetic only.

## Files

Created:

- `src/promoter_ai_extraction/evaluation/comparison.py`
- `src/promoter_ai_extraction/evaluation/metrics.py`
- `src/promoter_ai_extraction/evaluation/service.py`
- `src/promoter_ai_extraction/application.py`
- `tests/unit/evaluation/test_comparison.py`
- `tests/unit/evaluation/test_metrics.py`
- `tests/contract/test_leakage_ordering.py`
- `tests/integration/__init__.py`
- `tests/integration/test_guided_baseline.py`

Modified:

- `02-DOCS/wiki/sdd/progress/guided-extraction-baseline.md`

## Decisions and deviations

- EXTRA_VALUE wins over PARTIAL_MATCH when extras and misses coexist.
- T027/T029/T032/T034 first RED was a missing-module collection failure.
- T031 was not invented.
- No runtime dependency was added.
- Six authoritative root documents remain unchanged.

## Scope and security

- T036 and later were not started.
- Knowledge-sync remains disabled.
- `/data/` and `/02-DOCS/data/` remain ignored, untracked, unstaged.
- T027–T035 remain uncommitted until the next approved checkpoint.
