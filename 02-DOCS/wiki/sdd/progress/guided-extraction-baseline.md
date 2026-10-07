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
- skill resolution:
  - used: `implement`, `python`, `testing-py`
  - missing: none
  - fallback: none
  - compact rules: tests precede behavior; public boundaries are typed; fixtures are synthetic; private gold never enters tests; progress is append-only.
