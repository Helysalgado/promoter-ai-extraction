# SDD specify — guided-extraction-baseline

## Metadata

- Date: 2026-10-06
- Branch: `feat/guided-extraction-baseline`
- Phase: `SDD → specify`
- Status: draft produced; stopped before `clarify`
- Knowledge sync: inactive (`reason: opted-out`)

## Objective

Define the first functional vertical slice for guided extraction of bacterial-promoter properties from a supplied TEI/XML or TXT article for an already identified promoter.

The slice must produce independent TSS, caja -10, caja -35, and factor sigma conclusions with evidence, conservative normalization, multiple-value support, explicit scientific abstention, output validation, and leakage-safe evaluation.

## Authoritative sources read in full

- `project-overview.md`
- `project-requirements.md`
- `extraction-contract.md`
- `gold-set-contract.md`
- `evaluation-contract.md`
- `ux-requirements.md`

Additional SDD sources:

- `02-DOCS/wiki/sdd/constitution.md`
- `02-DOCS/wiki/sdd/decisions.md`
- `02-DOCS/wiki/sdd/config.yaml`
- `02-DOCS/wiki/harness/user-profile.md`

The six root requirement documents were not modified.

## Commands executed

```text
node .rsc/session-memory.mjs resume
git fetch origin main
git branch --show-current
git status --porcelain
git rev-list --left-right --count main...origin/main
npx @ericrisco/rsc@3.0.7 knowledge-sync status
git switch -c feat/guided-extraction-baseline
git status --short --branch
npm run spec:gate -- 02-DOCS/wiki/sdd/specs/guided-extraction-baseline.md
```

Read-only Git inspection and final audit commands are listed in the final Git state section.

## Preconditions and branch action

Before creating the feature branch:

- current branch was `main`;
- working tree was clean;
- `main...origin/main` was `0 0`;
- knowledge sync reported `"active": false` and `"reason": "opted-out"`.

The local branch `feat/guided-extraction-baseline` was then created from synchronized `main`.

## Actions performed

1. Read the authoritative requirements and SDD foundation artifacts.
2. Drafted a WHAT/WHY feature specification.
3. Kept implementation technologies and architecture outside the specification.
4. Classified unresolved decisions into PLAN blockers and deferrable decisions.
5. Recorded authoritative-document inconsistencies and scope tensions.
6. Performed a fresh-eyes, read-only review.
7. Corrected AC-01 and AC-02 so valid supported inputs must produce the four scientific result units rather than satisfying acceptance through a technical-failure alternative.
8. Added the draft spec to the knowledge index.
9. Logged the significant scope decision in the SDD decision log.
10. Created this phase report.

No `clarify`, `plan`, `tasks`, `analyze`, `implement`, `verify`, or `ship` phase was executed.

## Artifact generated

Primary artifact:

```text
02-DOCS/wiki/sdd/specs/guided-extraction-baseline.md
```

Status:

```text
draft
```

The spec covers:

- TEI/XML and TXT inputs;
- identified paper and promoter;
- optional paper-specific gene synonym;
- independent TSS, caja -10, caja -35, and sigma conclusions;
- multiple values;
- separate raw and normalized values;
- evidence and location;
- qualifiers;
- scientific abstention;
- technical-failure separation;
- output validation;
- persisted predictions before gold access;
- leakage-safe evaluation;
- `paper × promoter × property` comparison;
- paper-grouped splits.

The spec excludes all user-requested later capabilities.

## Decisions that block PLAN

1. **Extractor-input field policy.** The exact benchmark-case boundary must be fixed as a canonical denylist, an explicit allowlist, or both. The authoritative documents do not contain one consistent forbidden-field list.
2. **`INVALID_CANDIDATE`.** Its role must be fixed as either a terminal scientific status or a diagnostic candidate flag.
3. **Multiple-value gold parsing.** A frozen rule is needed to convert all encoded multiple-value cells into comparison sets.

These decisions were not selected silently.

## Decisions that may remain deferred

- Project-wide treatment of `Sin_dato_en_RegulonDB` beyond keeping it outside extraction.
- Evaluation use of `Técnica_confirmada_manualmente`.
- Evaluation use of `Año_confirmado`.
- Concrete ignore-file and local-storage strategy for future gold files.
- Biological Rpo/sigma equivalences.
- Final adjudication of extremely short caja -10/-35 values.
- Final development/test paper allocation and final frozen gold version.
- Final bootstrap settings.
- A curator-annotated evidence benchmark.
- A complete documentary-negative benchmark for false assertions and appropriate abstention.

## Contradictions and scope tensions found

1. The explicit forbidden-field lists differ across the root contracts.
2. `Técnica_confirmada_manualmente` is described as “No como target” in one gold table but is categorically prohibited later in the same contract.
3. The wider Part 1 includes UI and demonstration/deployment expectations, while this first slice intentionally excludes UI and deployment. This is staged scope, not cancellation.
4. The evaluation contract has a usable provisional normalization profile, while the root requirements keep final normalization and scoring open before final test.
5. The current subset supports positive value-recovery evaluation but not a complete evaluation of appropriate abstention or documentary false assertions.

## Specification review

The fresh-eyes review initially found one serious loophole:

```text
AC-01 and AC-02 allowed valid supported inputs to end in technical failure
and still satisfy acceptance.
```

The criteria were corrected. They now require the four scientific result units for readable, valid TXT and TEI/XML inputs. Technical failure remains separately covered by AC-16.

## rsc-harness phase result

The installed `specify` guidance requires:

```text
npm run spec:gate <spec-path>
```

The command was executed and could not run because this repository has no `package.json` or configured npm script:

```text
npm error code ENOENT
npm error path <repository>/package.json
npm error enoent Could not read package.json
```

No test runner or package-manager configuration was invented. The spec was instead checked manually for complete sections, typed open points, WHAT/WHY scope, observable acceptance criteria, and constitution alignment, then reviewed with fresh context.

Phase result:

```json
{
  "status": "complete",
  "executive_summary": "Draft specification written with three explicit PLAN blockers and deferred decisions preserved.",
  "artifact": "02-DOCS/wiki/sdd/specs/guided-extraction-baseline.md",
  "next_recommended": "clarify",
  "risk": "high",
  "model": {
    "tier": "balanced",
    "resolved": "session model",
    "routing": "off"
  },
  "skill_resolution": {
    "used": ["sdd", "specify", "orient"],
    "missing": [],
    "fallback": ["Manual spec gate because no package.json/spec:gate script exists."],
    "compact_rules": [
      "Keep the spec WHAT/WHY only.",
      "Make acceptance criteria observable.",
      "Do not resolve scientific ambiguities silently.",
      "Keep extraction isolated from gold and evaluator-only data."
    ]
  },
  "evidence": [
    "spec path exists",
    "open points are typed and classified",
    "fresh-eyes review issue corrected",
    "knowledge index and SDD decision log updated"
  ]
}
```

## Files created or modified

Created:

- `02-DOCS/wiki/sdd/specs/guided-extraction-baseline.md`
- `02-DOCS/process/2026-10-06-guided-extraction-baseline-specify.md`

Modified:

- `02-DOCS/wiki/index.md`
- `02-DOCS/wiki/sdd/decisions.md`

## Final Git state

The final audit must show:

- branch `feat/guided-extraction-baseline`;
- no commit created;
- no push performed;
- the four expected files as working-tree changes;
- no diff in the six authoritative root requirement documents.

Exact final `git status --short --branch` and `git diff --stat` are shown in the Cursor review output for this phase.

## Warnings and ambiguities

- The automated `spec:gate` is unavailable because the repository has no npm package configuration.
- The specification is still `draft` and has not received human approval.
- Three open decisions block planning.
- The current positive-only subset cannot support every desired abstention or false-assertion claim.
- No authoritative requirement was changed to resolve these gaps.

## Next recommended step

After human review and approval of this draft, run `SDD → clarify` to resolve the three PLAN blockers. Do not start `plan` until those blockers are resolved and folded back into the same specification.
