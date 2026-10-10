# SDD plan — guided-extraction-baseline

## Metadata

- Date: 2026-10-07
- Branch: `feat/guided-extraction-baseline`
- Phase: `SDD → plan`
- Plan status: draft for human review
- TASKS unlocked: yes
- TASKS executed: no

## Objective

Design the minimum Python architecture for the complete first vertical slice:

```text
TEI/XML or TXT + identified paper + identified promoter
→ independent property extraction
→ evidence / location / normalization / qualifiers / abstention
→ validation
→ immutable prediction persistence
→ evaluator-only gold access
→ gold parsing
→ set comparison
→ metrics and reporting
```

## Sources

Authoritative root requirements:

- `project-overview.md`
- `project-requirements.md`
- `extraction-contract.md`
- `gold-set-contract.md`
- `evaluation-contract.md`
- `ux-requirements.md`

SDD sources:

- `02-DOCS/wiki/sdd/constitution.md`
- `02-DOCS/wiki/sdd/decisions.md`
- `02-DOCS/wiki/sdd/specs/guided-extraction-baseline.md`
- `02-DOCS/wiki/sdd/config.yaml`

Runtime evidence:

- `pyproject.toml`

The six authoritative root documents were not modified.

## Artifact generated

```text
02-DOCS/wiki/sdd/plans/guided-extraction-baseline.md
```

The plan uses the standard rsc-harness sections:

1. global constraints;
2. context and constraints;
3. architecture;
4. interfaces and contracts;
5. data model and flow;
6. testing strategy;
7. sequencing and dependencies;
8. dependencies, risks, and open decisions.

## Architecture proposed

One synchronous Python process with small modules and explicit immutable contracts.

The extraction and evaluation sides are separated by two enforced boundaries:

1. extraction accepts only a typed allowlisted request and has no gold-loader dependency;
2. evaluation accepts only a verified persisted prediction reference and opens gold only after persistence succeeds.

No service, database, web framework, asynchronous orchestration, RAG, agent framework, vector store, or deployment layer is included.

## Main components

1. `DocumentLoader`
2. `ExtractionRequestFactory`
3. `GuidedExtractionService`
4. `PropertyExtractor` port
5. provider-specific `ModelBackend` adapter
6. property-specific normalizers
7. `OutputValidator`
8. `PredictionStore`
9. evaluator-only `GoldLoader`
10. evaluator-only `GoldParser`
11. `SetComparator`
12. `MetricsReporter`

The exact module count may be reduced during implementation, but these responsibilities and dependency directions must remain distinct.

## Anti-leakage design

- Request creation uses a closed allowlist and defensive denylist.
- Unknown keys fail before any backend call.
- Nested forbidden keys fail.
- No arbitrary metadata dictionary exists on `ExtractionRequest`.
- Prompt/backend input is an explicit field projection.
- Benchmark inputs come from explicit caller data or a separate allowlisted case manifest.
- Extraction never opens `SUBSET_GOLD.xlsx` to construct a request.
- `GoldRecord` exists only inside the evaluation package.
- The evaluator accepts a `PersistedPredictionRef`, not an in-memory result.
- The gold loader opens the workbook only after persistence verification.
- Sentinel and event-order tests prove these boundaries.

## End-to-end flow

1. Load TXT or TEI/XML into source-located segments.
2. Validate and construct the allowlisted extraction request.
3. Execute one independent attempt per property.
4. Normalize only documentary forms allowed by the contracts.
5. Validate status/value/evidence/candidate consistency.
6. Group four property attempts into one run.
7. Persist the run atomically as immutable versioned JSON.
8. Verify the persisted reference.
9. Open the local gold in the evaluator.
10. Parse raw gold values into property-specific sets.
11. Compare prediction and gold as sets.
12. Aggregate TP/FP/FN and derived metrics by property and available strata.

Scientific abstentions, rejected candidates, technical failures, gold parse failures, and evaluation outcomes remain distinct.

## Gold parser design

- Preserve original cell and storage type.
- Preserve raw tokens.
- Caja -10: split only exactly two nucleotide tokens separated by literal ` + `.
- Caja -35: internal line break remains one token and is removed only during normalization.
- TSS: one integer token; minus is a sign.
- Sigma: one label token.
- Normalize after tokenization.
- Deduplicate after normalization while preserving raw provenance.
- Unknown or ambiguous syntax: `PARSE_ERROR / NEEDS_REVIEW`.
- Parsing performs no matching or scoring.
- Rules apply to the current workset only.

## Testing strategy

`pytest` is proposed as the first test runner because the slice requires parametrized normalization tests, temporary local stores, synthetic XLSX fixtures, exception assertions, and event-order spies.

Planned coverage:

- unit tests for each property normalizer;
- unit tests for current-workset gold parsing;
- multiple-value and line-break parsing;
- candidate rejection and `INVALID_CANDIDATE`;
- every scientific abstention;
- technical failures;
- allowlist and denylist;
- nested/renamed forbidden input;
- proof that gold does not reach the extractor or prompt;
- proof that persistence occurs before gold access;
- set TP/FP/FN comparison;
- metrics by property and modality;
- paper-grouped split validation;
- synthetic TXT and TEI integration flows;
- one complete synthetic extraction-to-evaluation flow.

Automated tests use only synthetic fixtures. They do not read `SUBSET_GOLD.xlsx` or private papers.

## Proposed dependencies

| Dependency | Purpose |
|---|---|
| `pytest` | Deterministic unit, contract, and integration tests. |
| `openpyxl` | Read-only XLSX evaluator input and synthetic workbook fixtures. |
| `defusedxml` | Fail-closed parsing of supplied TEI/XML. |

No model-provider SDK is selected yet.

## Principal risks

1. indirect leakage through generic objects or serializers;
2. gold access before durable persistence;
3. plausible but unsupported model values or evidence;
4. provider structured-output/context limitations;
5. oversized documents and unsafe truncation;
6. overgeneralized gold delimiters;
7. technical failures disappearing from metric coverage;
8. overclaiming from the positive-only subset;
9. committing local papers, gold, evidence, or prediction files;
10. incompatible XLSX dependency/environment.

Each risk has a concrete prevention or test in the plan.

## HUMAN_DECISION_REQUIRED

### Concrete model backend

Required before implementing the real provider adapter:

- provider;
- model identifier;
- credential source;
- structured-output capability;
- context limit;
- reproducibility settings.

This does not block TASKS. The extractor port, safe request, scripted backend, and all non-provider components are stable.

### Technical failures in final headline metrics

The plan reports technical failures and evaluated coverage separately.

Before freezing the final benchmark, the human must decide whether to publish an additional end-to-end metric that treats technical failures as unrecovered positives.

This does not block TASKS because the run and report retain enough information for either final view.

## Significant decisions recorded

`02-DOCS/wiki/sdd/decisions.md` records:

- synchronous single-process Python architecture;
- explicit extraction/evaluation module boundary;
- immutable local JSON prediction persistence;
- safe case manifest instead of constructing requests from gold;
- evaluator access through verified persisted references;
- minimal dependency set;
- the two non-blocking human decisions.

## Files created or modified in this phase

Created:

- `02-DOCS/wiki/sdd/plans/guided-extraction-baseline.md`
- `02-DOCS/process/2026-10-07-guided-extraction-baseline-plan.md`

Modified:

- `02-DOCS/wiki/index.md`
- `02-DOCS/wiki/sdd/decisions.md`

Existing uncommitted specify/clarify artifacts remain in the working tree.

The supplied workbook `02-DOCS/data/SUBSET_GOLD.xlsx` remains untracked and must not be committed.

## Workflow result

```json
{
  "status": "complete",
  "executive_summary": "A minimal synchronous Python architecture separates extraction from evaluation, enforces persist-before-gold, and defines deterministic tests and sequencing.",
  "artifact": "02-DOCS/wiki/sdd/plans/guided-extraction-baseline.md",
  "next_recommended": "tasks",
  "risk": "medium",
  "model": {
    "tier": "heavy",
    "resolved": "session model",
    "routing": "off"
  },
  "skill_resolution": {
    "used": ["plan", "python", "orient"],
    "missing": [],
    "fallback": [],
    "compact_rules": [
      "Keep extraction and evaluator dependencies one-way.",
      "Persist before opening gold.",
      "Use typed immutable boundaries and stdlib-first modules.",
      "Test leakage and ordering explicitly."
    ]
  },
  "evidence": [
    "plan artifact exists",
    "all spec acceptance criteria are mapped to test levels",
    "architecture and interfaces are explicit",
    "risks and human decisions are recorded",
    "TASKS gate is unblocked"
  ]
}
```

## Git and phase constraints

- No commit.
- No push.
- No pull request.
- No root requirement modification.
- No `tasks`, `analyze`, or `implement` phase executed.

Final `git status --short --branch --untracked-files=all`:

```text
## feat/guided-extraction-baseline
 M 02-DOCS/wiki/index.md
 M 02-DOCS/wiki/sdd/decisions.md
?? 02-DOCS/data/SUBSET_GOLD.xlsx
?? 02-DOCS/process/2026-10-06-guided-extraction-baseline-clarify.md
?? 02-DOCS/process/2026-10-06-guided-extraction-baseline-specify.md
?? 02-DOCS/process/2026-10-07-guided-extraction-baseline-plan.md
?? 02-DOCS/wiki/sdd/plans/guided-extraction-baseline.md
?? 02-DOCS/wiki/sdd/specs/guided-extraction-baseline.md
```

Final `git diff --stat`:

```text
02-DOCS/wiki/index.md         |  2 ++
02-DOCS/wiki/sdd/decisions.md | 83 +++++++++++++++++++++++++++++++++++++++++++
2 files changed, 85 insertions(+)
```

Untracked files are not included in `git diff --stat`. The six authoritative root documents have no diff. The branch has no commit beyond `main`.

## Next recommended step

Stop for human review. If the plan is approved, run `SDD → tasks` in a separate phase.
