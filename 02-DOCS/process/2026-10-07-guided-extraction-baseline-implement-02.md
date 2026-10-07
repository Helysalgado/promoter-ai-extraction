---
type: process-report
title: Guided extraction baseline — IMPLEMENT 02
date: 2026-10-07
feature: guided-extraction-baseline
phase: implement
scope: T011-T018
---

# IMPLEMENT 02 — guided-extraction-baseline

## Objective

Complete only T011–T018: conservative property normalization, scientific-output validation, extractor/backend ports, a deterministic scripted backend for tests, and sequential four-property orchestration.

## Foundation checkpoint

- Commit: `596a7f318a9d7256c45938d462bf8cb53b51f960`
- Message: `feat: establish safe extraction foundation`
- Remote branch: `origin/feat/guided-extraction-baseline`
- Scope: approved T001–T010 files only.
- Verification before commit: `uv sync --frozen` and `./scripts/verify.sh` passed with 205 tests.
- Commit message contains no generated trailers.

## Completed tasks

- T011–T012: pure normalizers for TSS, Caja -10, Caja -35, and factor sigma.
  - `value_raw` remains unchanged.
  - TSS sign derivation requires an explicit translation-start anchor in the raw form or grounded evidence.
  - Boxes receive only typographic case/separator normalization.
  - Sigma receives only typographic normalization; Rpo/sigma biological equivalences remain excluded.
- T013–T014: `OutputValidator`.
  - Enforces request/result identity, status/value cardinality, abstention reasons, required evidence, and document-segment grounding.
  - Validates evidence fragment, source type, and location against the referenced segment.
  - Keeps `INVALID_CANDIDATE` diagnostic and accepted values separate.
  - Returns `TechnicalFailure` for contract violations.
- T015–T016: `ModelBackend` and `PropertyExtractor` ports plus safe immutable payloads.
  - Backend receives only `SafeExtractionInput`.
  - Backend failures, adapter exceptions, malformed statuses, and malformed evidence cardinality remain technical failures.
  - Test-only `ScriptedBackend` and `CaptureBackend` are deterministic.
- T017–T018: `GuidedExtractionService` and `ExtractionRun`.
  - Executes TSS, Caja -10, Caja -35, and sigma independently and sequentially.
  - Groups all four attempts by paper and promoter.
  - A technical failure in one property does not suppress the other attempts.

## Tests and evidence

- Focused T011–T018 suite: 122 tests passed.
- Full gate: `./scripts/verify.sh`.
- Final result: 327 passed, 0 failed.
- Tests cover normalization, raw preservation, qualifiers, multiple values, abstention, invalid candidates, technical failures, evidence grounding, malformed backend payloads, safe projection, property independence, and grouped output.
- All fixtures are synthetic.

## Files

Created:

- `src/promoter_ai_extraction/normalization.py`
- `src/promoter_ai_extraction/validation.py`
- `src/promoter_ai_extraction/extraction.py`
- `tests/contract/__init__.py`
- `tests/contract/test_extractor_port.py`
- `tests/fakes.py`
- `tests/unit/test_extraction_service.py`
- `tests/unit/test_normalization.py`
- `tests/unit/test_validation.py`

Modified:

- `src/promoter_ai_extraction/models.py`
- `tests/conftest.py`
- `02-DOCS/wiki/sdd/progress/guided-extraction-baseline.md`

## Decisions and deviations

- No new scientific, leakage, evaluation, scope, or material architectural decision was required.
- T017 did not have an independent RED run because `GuidedExtractionService` was initially implemented in the same module pass as T016. Its required behavior is covered by dedicated orchestration tests.
- Review strengthened evidence grounding and backend-payload cardinality checks without changing approved architecture or scientific rules.
- No runtime dependency was added.

## Scope and security

- T019 and later tasks were not started.
- No persistence, evaluator, gold parser, metrics, real model backend, RAG, agents, FastAPI, UI, or deployment code was added.
- The six authoritative root documents remain unchanged.
- Knowledge-sync remains disabled.
- `02-DOCS/data/SUBSET_GOLD.xlsx` remains ignored, untracked, unstaged, unread by tests, and outside Git.
- T011–T018 remain uncommitted for review.
