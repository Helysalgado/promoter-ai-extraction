# guided-extraction-baseline — IMPLEMENT increment 01

- Date: 2026-10-07
- Branch: `feat/guided-extraction-baseline`
- Phase: `SDD → implement`
- Scope: tasks `T001–T010` only
- Result: complete
- Commits created: none
- Pushes performed: none

## Objective

Implement the first approved functional increment:

- private/gold-data protection;
- minimal reproducible Python and pytest foundation;
- immutable base domain contracts;
- TXT loading;
- safe TEI/XML loading;
- reproducible document segments and locations;
- closed extractor allowlist;
- defensive denylist against direct and indirect leakage.

No work from `T011` or later was started.

## Completed tasks

- `T001`: narrow ignore protection for the real workbook and local generated outputs.
- `T002`: Python `src/` package, uv lock, pytest configuration, synthetic-fixture convention, and deterministic verification script.
- `T003`: base-domain contract tests.
- `T004`: immutable property, status, evidence, value, candidate, result, attempt, and technical-failure contracts.
- `T005`: TXT-loader tests.
- `T006`: TXT loader with stable paragraphs, line locations, UTF-8 handling, and SHA-256.
- `T007`: TEI/XML-loader tests.
- `T008`: fail-closed TEI/XML loader using `defusedxml`.
- `T009`: allowlist/denylist and leakage-boundary tests.
- `T010`: immutable extraction request and safe case-manifest boundary.

Implementation evidence is recorded in:

`02-DOCS/wiki/sdd/progress/guided-extraction-baseline.md`

## Implemented behavior

### Private data

- `02-DOCS/data/SUBSET_GOLD.xlsx` has an exact ignore rule.
- The workbook is not tracked and is not staged.
- `tests/fixtures/synthetic_gold.xlsx` remains versionable.
- Automated tests never open or use the real workbook.
- Local `predictions/`, `outputs/`, and `runs/` directories are ignored.

### Python/test foundation

- Python floor remains `>=3.11`.
- Package uses a `src/promoter_ai_extraction/` layout.
- Environment is locked with `uv.lock`.
- `scripts/verify.sh` checks both real-gold protection and synthetic-fixture versionability, then runs pytest.
- Installed `testing-py` after explicit human approval; this updated `.rsc.json`.

### Domain contracts

- Four `Property` values.
- Five terminal `ScientificStatus` values.
- `INVALID_CANDIDATE` remains a candidate rejection reason, not a terminal status.
- Frozen slotted dataclasses for evidence, accepted values, rejected candidates, property results, and technical failures.
- A technical-failure code cannot equal a scientific status.
- Output-contract cardinality checks remain intentionally deferred to `T013–T014`.

### TXT loader

- Accepts one path or one in-memory content string, never both.
- Reads UTF-8 without silent truncation.
- Produces ordered paragraph segments.
- Produces deterministic segment IDs.
- Preserves one-based line ranges.
- Computes SHA-256 over source bytes.
- Empty, unreadable, invalid-source, and decoding cases are technical failures.

### TEI/XML loader

- Uses `defusedxml`.
- Rejects malformed XML, DTD/internal entities, and external-entity/XXE input.
- Extracts paragraphs, headings, figure captions, tables, and notes.
- Preserves available section, page, figure, and XML identifiers.
- Uses canonical source types.
- Does not invent unavailable location precision.
- Error messages do not echo supplied malformed content.

### Extractor boundary

- `ExtractionRequest` contains exactly:
  - loaded document;
  - paper identifier;
  - optional promoter identifier;
  - promoter name;
  - optional paper-specific gene synonym;
  - requested property.
- No arbitrary metadata bag or gold path exists.
- Paper identity must match the loaded document.
- A closed allowlist rejects every unknown top-level field.
- The defensive denylist rejects canonical gold, curator, split, target, score, metric, and evaluator fields.
- Key normalization covers case, accents, spaces, hyphens, and repeated separators.
- Recursive inspection covers mappings and mapping values embedded in list, tuple, set, or frozenset containers.
- Document text is never scanned for forbidden words.
- Safe manifest projection accepts only document reference/format and allowlisted identity fields.
- Boundary errors use stable codes and do not echo private values.

## Dependencies added

Direct resolved dependencies:

```text
promoter-ai-extraction v0.1.0
├── defusedxml v0.7.1
├── openpyxl v3.1.5
└── pytest v9.1.1 (group: dev)
```

- `pytest`: approved deterministic test runner.
- `defusedxml`: approved fail-closed TEI/XML parser.
- `openpyxl`: included because the approved `T002` done-check explicitly requires the dependency environment to import it; no evaluator or workbook-loading code was implemented in this increment.
- `hatchling`: build backend required for the `src/` package installation.

`pytest-cov` was introduced transiently by the implementation worker but was not justified by the approved dependency list. It was removed from `pyproject.toml`, `uv.lock`, and the synchronized environment before final verification.

## Tests executed

Primary final command:

```text
uv sync --frozen && ./scripts/verify.sh
```

Result:

```text
[ok] Real gold workbook is git-ignored.
[ok] Synthetic fixture path is versionable (not git-ignored).
205 passed in 0.13s
=== verify gate passed ===
```

Focused suites were also executed during RED/GREEN:

- `tests/unit/test_package.py`
- `tests/unit/test_models.py`
- `tests/unit/test_txt_loader.py`
- `tests/unit/test_tei_loader.py`
- `tests/unit/test_boundary.py`

Coverage includes:

- valid and invalid TXT;
- valid, malformed, unsafe, and empty TEI/XML;
- internal and external entity attacks;
- deterministic document hashes, segment IDs, and locations;
- captions, tables, sections, pages, and figure IDs;
- closed allowlist;
- all canonical denied-field categories;
- unknown, renamed, case/diacritic/separator variants;
- nested and sequence-embedded forbidden fields;
- safe boundary messages;
- immutable request and manifest carriers.

## Review

Fresh Python and leakage reviews found no Critical issue.

Accepted review findings were corrected:

- mechanical technical/scientific failure-code separation;
- misleading evidence-cardinality test;
- canonical source-type documentation;
- sequence-container recursive denylist scan;
- repeated-separator key normalization;
- non-echoing document errors;
- typed manifest format narrowing;
- synthetic-fixture negative ignore gate;
- dead typing code and mutable-counter cleanup.

One recommendation was intentionally rejected: broadly ignoring every XLSX/XML/TXT under `02-DOCS/data/`. That would conflict with the approved requirement to keep public synthetic fixtures versionable. The current real workbook is protected by an exact rule; any future private/gold file requires an explicit reviewed rule or private directory.

## Decisions and deviations

No new scientific, leakage, evaluation, scope, or material architecture decision was required.

Process deviations:

- Initial RED runs for `T003`, `T005`, and `T009` failed at module import because their modules did not yet exist. This is weaker TDD evidence than a behavioral assertion failure. Later review-driven tests did produce behavioral RED evidence for the implemented contracts.
- `pytest-cov` was briefly introduced and then removed before the final state.
- The generic Python skill recommends newer Python, but the approved project floor remains Python 3.11 and was preserved.

## Files created or modified

Modified:

- `.gitignore`
- `.rsc.json`
- `02-DOCS/wiki/index.md`
- `pyproject.toml`

Created:

- `02-DOCS/process/2026-10-07-guided-extraction-baseline-implement-01.md`
- `02-DOCS/wiki/sdd/progress/guided-extraction-baseline.md`
- `scripts/verify.sh`
- `src/promoter_ai_extraction/__init__.py`
- `src/promoter_ai_extraction/models.py`
- `src/promoter_ai_extraction/documents.py`
- `src/promoter_ai_extraction/boundary.py`
- `tests/conftest.py`
- `tests/unit/test_package.py`
- `tests/unit/test_models.py`
- `tests/unit/test_txt_loader.py`
- `tests/unit/test_tei_loader.py`
- `tests/unit/test_boundary.py`
- `uv.lock`

No six-root requirement document was modified.

## Git status

```text
## feat/guided-extraction-baseline...origin/feat/guided-extraction-baseline
 M .gitignore
 M .rsc.json
 M 02-DOCS/wiki/index.md
 M pyproject.toml
?? 02-DOCS/process/2026-10-07-guided-extraction-baseline-implement-01.md
?? 02-DOCS/wiki/sdd/progress/guided-extraction-baseline.md
?? scripts/verify.sh
?? src/promoter_ai_extraction/__init__.py
?? src/promoter_ai_extraction/boundary.py
?? src/promoter_ai_extraction/documents.py
?? src/promoter_ai_extraction/models.py
?? tests/conftest.py
?? tests/unit/test_boundary.py
?? tests/unit/test_models.py
?? tests/unit/test_package.py
?? tests/unit/test_tei_loader.py
?? tests/unit/test_txt_loader.py
?? uv.lock
```

The ignored real workbook does not appear in normal status output. Independent checks confirmed:

```text
ROOT_DOCS_UNCHANGED=true
INDEX_EMPTY=true
GOLD_IGNORED_UNTRACKED_UNSTAGED=true
SYNTHETIC_FIXTURE_VERSIONABLE=true
COMMITS_NOT_PUSHED=0
```

## Git diff --stat

```text
 .gitignore            | 13 +++++++++++++
 .rsc.json             |  6 ++++++
 02-DOCS/wiki/index.md |  1 +
 pyproject.toml        | 27 +++++++++++++++++++++++++--
 4 files changed, 45 insertions(+), 2 deletions(-)
```

Standard `git diff --stat` does not include the untracked implementation, tests, lockfile, progress artifact, or this report.

## Stop condition

The increment stops after `T010`. `T011` has not started. No commit, push, PR, merge, VERIFY, or SHIP action was performed.

```json result-envelope
{
  "status": "complete",
  "executive_summary": "Implemented T001–T010 with 205 passing synthetic tests and reviewed leakage boundaries.",
  "artifact": "02-DOCS/wiki/sdd/progress/guided-extraction-baseline.md",
  "next_recommended": "implement",
  "risk": "medium",
  "skill_resolution": {
    "used": ["implement", "python", "testing-py"],
    "missing": [],
    "fallback": [],
    "compact_rules": [
      "Use uv and the approved Python 3.11 floor.",
      "Keep private gold outside Git and tests.",
      "Fail closed at document and request boundaries.",
      "Append progress after every task."
    ]
  },
  "evidence": [
    "205 pytest tests passed",
    "scripts/verify.sh passed",
    "SUBSET_GOLD.xlsx ignored, untracked, and unstaged",
    "six root documents unchanged",
    "no commit or push"
  ]
}
```
