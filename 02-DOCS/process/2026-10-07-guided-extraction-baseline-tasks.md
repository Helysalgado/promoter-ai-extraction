# guided-extraction-baseline — SDD TASKS

- Date: 2026-10-07
- Branch: `feat/guided-extraction-baseline`
- Phase: `SDD → tasks`
- Feature: `guided-extraction-baseline`
- Result: TASKS complete
- Task artifact: `02-DOCS/wiki/sdd/plans/guided-extraction-baseline.md` (`## Tasks`)

## Objective

Derive small, dependency-ordered, independently verifiable implementation tasks from the approved specification and plan. The decomposition keeps tests beside the behavior they prove, protects private gold data, preserves extraction/evaluation isolation, and leaves post-baseline course work outside this feature.

## Actions performed

1. Read the six authoritative root requirements, constitution, decision log, approved specification, approved plan, and the SDD TASKS workflow.
2. Marked the approved plan as `approved`.
3. Appended the standard TASKS section to the existing plan; no parallel task document was created.
4. Added 44 stable tasks (`T001`–`T044`) in 12 functional increments.
5. Embedded runnable done-checks, dependencies, and requirement traces in every task.
6. Included tests in the increments that introduce each behavior.
7. Added the requested post-baseline course milestones as reminders, not as tasks in this feature.
8. Updated the knowledge index to show that the plan is approved and contains TASKS.
9. Audited IDs, dependency direction, diff hygiene, root-requirement integrity, and branch history.

## Task decomposition

The 44 tasks are grouped into these 12 increments:

1. Contracts, test foundation, and private-data guard (`T001`–`T004`).
2. TXT and TEI/XML input (`T005`–`T008`).
3. Safe extractor boundary (`T009`–`T010`).
4. Normalization and validation (`T011`–`T014`).
5. Extractor ports and orchestration (`T015`–`T018`).
6. Prediction persistence (`T019`–`T022`).
7. Evaluator-only gold loader and parser (`T023`–`T026`).
8. Set comparison and metrics (`T027`–`T031`).
9. Leakage ordering and end-to-end integration (`T032`–`T035`).
10. Real model backend decision and adapter (`T036`–`T038`).
11. Controlled local baseline execution (`T039`–`T042`).
12. Deterministic completion gate and evidence (`T043`–`T044`).

Seven test-writing tasks are marked `[P]` because they touch disjoint test/module seams after their shared prerequisites.

## Critical implementation order

The deterministic critical path is:

`T001 → T002 → T003 → T004`

After `T004`, the document, boundary, normalization, persistence, and evaluator tracks can progress according to their recorded dependencies. They converge through:

`T015–T018 → T032–T035 → T040–T041 → T043`

The controlled real-backend path is deliberately later:

`T036 → T037 → T038`, plus `T039`, then `T042 → T044`.

`T040` and `T041` use synthetic inputs and therefore do not wait for the real provider/model decision or approval of a real development manifest.

## Tests and evidence represented in TASKS

The decomposition explicitly includes:

- `pytest` configuration and a deterministic verification script;
- TXT and TEI/XML loader tests;
- property-specific normalization tests;
- current-workset gold-parser tests, including literal ` + ` for Caja -10 and an internal line break as part of one Caja -35 sequence;
- multiple-value and set-comparison tests;
- `INVALID_CANDIDATE` diagnostic tests;
- scientific abstention tests;
- technical-failure tests;
- allowlist/denylist tests, including nested and renamed forbidden fields;
- a capture test proving gold/curator/evaluator-only data does not reach the extractor;
- verified persist-before-gold ordering tests;
- TP/FP/FN, precision, recall, F1, exact-row accuracy, coverage, and per-property reporting;
- paper-grouped split validation;
- synthetic TXT and TEI/XML end-to-end flows;
- a synthetic extraction → persistence → evaluation flow;
- a deterministic no-network suite that does not access private papers or `SUBSET_GOLD.xlsx`.

All automated tests use synthetic fixtures. The real workbook remains local evaluator input only.

## HUMAN_DECISION_REQUIRED

Two explicit decision checkpoints remain:

- `T031`: choose the final headline treatment of technical failures. Existing separate technical-failure and coverage reporting remains fixed; this decision concerns whether to add an end-to-end denominator view.
- `T036`: select the provider and model for the real backend, including reproducibility and credential-handling parameters.

Neither checkpoint blocks the deterministic implementation through the synthetic end-to-end baseline. `T036` blocks only the selected provider adapter and controlled real-model run. `T031` is required before the controlled baseline report in `T042`.

`T039` also requires human approval of the leakage-safe development manifest and local paper directory before a controlled real-data run; it does not alter scientific or architectural decisions.

## IMPLEMENT gate

`IMPLEMENT` is not yet unlocked by the SDD workflow because `02-DOCS/wiki/sdd/config.yaml` requires `analyze: pass` before implementation. The task decomposition itself has no critical blocker for beginning deterministic implementation once ANALYZE passes.

Next workflow phase: `SDD → analyze`, only after explicit human authorization.

## Review workload forecast

- Overall: medium.
- Highest-risk review areas: extractor boundary, output validation, immutable persistence, gold isolation/order, and set-based evaluator behavior.
- Lower-risk review areas: loader mechanics, pure normalization helpers, report formatting, and index/progress updates.

## Post-baseline course milestones

The plan records these future project deliverables without converting them into tasks for this feature:

- FastAPI service;
- RAG;
- at least one agent;
- end-to-end/regression evals;
- deployment/demo;
- recommended frontend;
- recommended CI/CD.

## Files created or modified by TASKS

- Modified: `02-DOCS/wiki/sdd/plans/guided-extraction-baseline.md`
- Modified: `02-DOCS/wiki/index.md`
- Created: `02-DOCS/process/2026-10-07-guided-extraction-baseline-tasks.md`

No ordinary task decomposition was added to `decisions.md`.

## Verification evidence

Task-table audit:

```text
TASK_ROWS_VALID=44
PARALLEL_TASKS=7
DEPENDENCIES_BACKWARD_ONLY=true
POST_BASELINE_HAS_NO_TASK_IDS=true
```

Repository audit:

```text
ROOT_REQUIREMENTS_UNCHANGED
COMMITS_AHEAD_MAIN=0
```

`git diff --check` completed successfully with no output.

The six authoritative root documents have no diff:

- `project-overview.md`
- `project-requirements.md`
- `extraction-contract.md`
- `gold-set-contract.md`
- `evaluation-contract.md`
- `ux-requirements.md`

No commit or push was performed.

## Git status

```text
## feat/guided-extraction-baseline
 M 02-DOCS/wiki/index.md
 M 02-DOCS/wiki/sdd/decisions.md
?? 02-DOCS/data/SUBSET_GOLD.xlsx
?? 02-DOCS/process/2026-10-06-guided-extraction-baseline-clarify.md
?? 02-DOCS/process/2026-10-06-guided-extraction-baseline-specify.md
?? 02-DOCS/process/2026-10-07-guided-extraction-baseline-plan.md
?? 02-DOCS/process/2026-10-07-guided-extraction-baseline-tasks.md
?? 02-DOCS/wiki/sdd/plans/guided-extraction-baseline.md
?? 02-DOCS/wiki/sdd/specs/guided-extraction-baseline.md
```

The real gold workbook remains untracked. `T001` is the first implementation task that will add a narrow ignore rule for it; the workbook is not a commit candidate.

## Git diff --stat

```text
 02-DOCS/wiki/index.md         |  2 ++
 02-DOCS/wiki/sdd/decisions.md | 83 +++++++++++++++++++++++++++++++++++++++++++
 2 files changed, 85 insertions(+)
```

This standard `git diff --stat` output covers tracked-file changes only. The plan, specification, process reports, and private workbook are currently untracked and therefore do not appear in that statistic.

## Warnings and unresolved items

- Do not stage or commit `02-DOCS/data/SUBSET_GOLD.xlsx`.
- The real provider/model remains undecided (`T036`).
- Final headline handling of technical failures remains undecided (`T031`).
- The approved safe development manifest must be reviewed before any controlled real-data run (`T039`).
- ANALYZE has not run; IMPLEMENT remains workflow-gated.

## Recommended next step

After human review of this TASKS artifact, explicitly authorize `SDD → analyze`. Do not begin implementation before that gate passes.
