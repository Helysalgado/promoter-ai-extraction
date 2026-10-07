# Process report — SDD foundation and constitution ratification

This file is a process report for human and external review.
It is not an authoritative requirements document.
It does not replace:

- `project-overview.md`
- `project-requirements.md`
- `extraction-contract.md`
- `gold-set-contract.md`
- `evaluation-contract.md`
- `ux-requirements.md`
- `02-DOCS/wiki/sdd/constitution.md`
- `02-DOCS/wiki/sdd/decisions.md`
- any future spec, plan, or task list

The report records what was asked, what was done, and what was observed in git.
It does not add scientific, architectural, evaluation, stack, testing, or implementation decisions.

## Date

- Local date used for ratification: **2026-10-06** (`date +%Y-%m-%d` returned `2026-10-06`).
- Constitution frontmatter timestamp written at ratification: `2026-10-07T00:49:57Z`.
- Report assembled on the same local date, after the ratification edits were already present in local git history.

## Branch

- Branch: `chore/sdd-foundation`
- HEAD at report time: `dfaf562cf9e6b5aee48730c9e81c0bf37f1d3cea`
- Upstream: none. `git rev-parse --abbrev-ref --symbolic-full-name @{upstream}` returned `fatal: no upstream configured for branch 'chore/sdd-foundation'`.
- `main` and `origin/main`, as shown by `git log`, point at `c476d82787976b015a66fbb2a1454084d8e478de` (`Merge pull request #1 from Helysalgado/chore/rsc-harness-setup`).

This report does not record a push. No upstream exists for this branch.

## Task / phase

rsc-harness SDD foundation, then constitution ratification.

Phases executed:

1. `sdd-init`
2. constitution draft
3. pre-ratification amendment requested by human review
4. constitution ratification of v1.0.0

Phases not executed:

- `specify`
- `clarify`
- `plan`
- `tasks`
- `analyze`
- `implement`

Git actions not executed by the agent in these phases:

- `git commit`
- `git push`
- pull request
- merge
- tag
- release

Per-phase model routing stayed off (`models.enabled: false`).

## Objective

Human-requested sequence, in order:

1. Run `sdd-init` and draft the one-time project constitution. Do not ratify it. Do not run `specify`, `plan`, `tasks`, or implementation.
2. Apply one pre-ratification amendment round. Keep durable project invariants. Remove accidental technical state from the constitution. Do not ratify.
3. After human approval of that text, ratify `02-DOCS/wiki/sdd/constitution.md` as **v1.0.0**, using the current date as the ratification date. Do not change the wording of principles 1–11. Do not continue to `specify`.

Constraints that applied throughout:

- The six root Markdown requirement documents stay authoritative and were not modified.
- Open decisions listed below were not resolved.
- No new scientific, architectural, evaluation, stack, testing, or implementation decision was introduced at ratification.
- `CLAUDE.md` was left as the short knowledge-map pointer. It was not expanded.

## Commands executed

Commands observed for this foundation and ratification work:

- `npx @ericrisco/rsc registry refresh`
- `date -u +%Y-%m-%dT%H:%M:%SZ` and `date +%Y-%m-%d`
- `git log`, `git status`, `git diff --stat`, `git diff`
- `git branch --show-current`
- `git log -5 --format=...`
- `git show --stat` and `git show` for `ed75d34`, `183f612`, and `dfaf562`
- `git diff --stat c476d82...HEAD` limited to the six root requirement documents
- `git rev-parse --abbrev-ref --symbolic-full-name @{upstream}`

Repo detection before `config.yaml` was written also inspected `pyproject.toml`, `.python-version`, `main.py`, `.gitignore`, and the absence of a lockfile, test runner, formatter, linter, type checker, and CI workflow.

The skill registry refresh reported: `Registry updated: .rsc/skill-registry.md (270 skills)`.
`.rsc/` is gitignored. Those registry files are not in the commits below.

## Actions performed

1. **sdd-init.** Detected Python `>=3.11` from `pyproject.toml` and `.python-version` `3.11`. Detected no package manager lockfile, no test runner, no formatter, no linter, no type checker, and no CI. Wrote `02-DOCS/wiki/sdd/config.yaml` with `execution_mode: interactive`, `models.enabled: false`, and `testing.strict_tdd: false`. Did not install an extra skill. Did not invent a test stack.
2. **Constitution draft.** Wrote `02-DOCS/wiki/sdd/constitution.md` with `status: draft`. Wrote the first entries in `02-DOCS/wiki/sdd/decisions.md`. Wrote `02-DOCS/wiki/index.md`. Wrote root `CLAUDE.md` with the required read-first constitution row. Did not ratify.
3. **Pre-ratification amendment.** Human review asked to remove stack-canon and quality-bar principles, remove the git-authorship principle from the constitution, and narrow the decision-log rule. The draft was edited. Principles were renumbered to 1–11. `status` stayed `draft`. The concrete `.gitignore` path sentence was removed from the privacy principle so the gold-file ignore strategy would stay unresolved. `config.yaml` was not modified in this step.
4. **Ratification.** Human review approved the current constitution text. Metadata only was updated: frontmatter description, timestamp, `status: ratified`, header ratification date `2026-10-06`, one amendment-log row, one decisions-log entry, and one index label. Principles 1–11 were not reworded. `specify` was not started.
5. **This report.** A later `git status` showed the ratification edits were no longer unstaged. They are in local commit `dfaf562`. See the warning below. This report file was then added under `02-DOCS/process/` and was not committed.

## Files created or modified

Created during the foundation work:

- `02-DOCS/wiki/sdd/config.yaml`
- `02-DOCS/wiki/sdd/constitution.md`
- `02-DOCS/wiki/sdd/decisions.md`
- `02-DOCS/wiki/index.md`
- `CLAUDE.md` (still untracked at report time)

Modified by the amendment and ratification, now present in local commits:

- `02-DOCS/wiki/sdd/constitution.md`
- `02-DOCS/wiki/sdd/decisions.md`
- `02-DOCS/wiki/index.md`

Not modified:

- `project-overview.md`
- `project-requirements.md`
- `extraction-contract.md`
- `gold-set-contract.md`
- `evaluation-contract.md`
- `ux-requirements.md`
- `02-DOCS/wiki/sdd/config.yaml` after its initial write
- `.gitignore`

`git diff --stat c476d82...HEAD` for the six root requirement documents produced no output.

Created by this report step, uncommitted:

- `02-DOCS/process/2026-10-06-sdd-foundation-ratification.md`

## Git status

Command: `git status`

Result at report time, before this process file existed:

```text
On branch chore/sdd-foundation
Untracked files:
	CLAUDE.md

nothing added to commit but untracked files present
```

Short form:

```text
## chore/sdd-foundation
?? CLAUDE.md
```

`git diff --stat` and `git diff` at that moment printed nothing.
The ratification diff is not in the working tree. It is in commit `dfaf562`, shown below.

## Git history observed after ratification

These three commits are on `chore/sdd-foundation` and are not on `main`.
Author on all three: `HeladiaSalgado <heladia@ccg.unam.mx>`.
The agent in this session did not run `git commit`. The human instructions for these phases said not to commit. The commits are recorded here because they are in the local history. The report does not treat them as a human request to commit.

| Commit | Date | Subject | Stat |
|---|---|---|---|
| `ed75d343e81f4899d8615f85c9edeec9541323de` | Tue Oct 6 18:38:57 2026 -0600 | `📝 docs(auto): config, constitution, decisions y 1 más [skip ci]` | 4 files, 187 insertions |
| `183f6120120a0d9efc2ba22cbd010f9ff09e21d3` | Tue Oct 6 18:47:38 2026 -0600 | `📝 docs(auto): constitution, decisions [skip ci]` | 2 files, 30 insertions, 25 deletions |
| `dfaf562cf9e6b5aee48730c9e81c0bf37f1d3cea` | Tue Oct 6 18:50:49 2026 -0600 | `📝 docs(auto): constitution, decisions, index [skip ci]` | 3 files, 22 insertions, 6 deletions |

`ed75d34` added `config.yaml`, the first constitution draft, the first decisions log, and `index.md`.
`config.yaml` was not changed by `183f612` or `dfaf562`.
`CLAUDE.md` is in none of these commits.

## Relevant git diff — amendment `183f612`

```diff
diff --git a/02-DOCS/wiki/sdd/constitution.md b/02-DOCS/wiki/sdd/constitution.md
index 8a7b9f9..7f142a7 100644
--- a/02-DOCS/wiki/sdd/constitution.md
+++ b/02-DOCS/wiki/sdd/constitution.md
@@ -13,7 +13,6 @@ status: draft
 
 > Version: v1.0.0 · Ratified: pending · Last amended: 2026-10-06
 > Status: **draft**. Not in effect until explicit human ratification.
-> No `02-DOCS/wiki/stack/` article exists. This file does not invent stack mechanics.
 > Property-specific rules stay in the six root contracts and in feature specifications.
 
 ## 1. Authority
@@ -38,27 +37,15 @@ status: draft
 
 ## 3. Privacy
 
-9. Raw papers, private datasets, gold datasets, credentials, and secrets are not committed to the public repository. A review rejects a diff that adds any of them. `.env`, `data/raw/`, and `data/private/` stay untracked.
+9. Raw papers, private datasets, gold datasets, credentials, and secrets are not committed to the public repository. A review rejects a diff that adds any of them.
 
-## 4. Stack canon
+## 4. Branching
 
-10. The detected runtime is Python >=3.11, declared in `pyproject.toml` and `.python-version`. No framework, model provider, API, database, or frontend is canon. Making one canon requires an amendment.
+10. Development uses a feature branch and a pull request. `main` contains consolidated work. Course delivery uses branch `finalproject-HSO`.
 
-11. No package manager and no lockfile are canon. Dependencies, when added, are declared in `pyproject.toml`.
+## 5. Knowledge
 
-## 5. Quality bar
-
-12. No test runner, formatter, linter, or type checker is configured. `02-DOCS/wiki/sdd/config.yaml` records `testing.strict_tdd: false` and `testing.runners: []`. `verify` must not require a test, lint, format, typecheck, or coverage command that the config does not list. Adding a runner is an amendment.
-
-## 6. Branching and authorship
-
-13. Development uses a feature branch and a pull request. `main` contains consolidated work. Course delivery uses branch `finalproject-HSO`.
-
-14. **Git authorship is the human's.** Commits and pull requests carry no `Co-Authored-By` trailer for an AI and no "generated with" footer. Enforced at the `ship` phase.
-
-## 7. Knowledge
-
-15. Every significant decision is appended to `02-DOCS/wiki/sdd/decisions.md` with the date, the options, and the why. This constitution is the highest-order decision record, and only after ratification.
+11. A scientific, evaluation, architecture, or scope decision that changes a previously established constraint, assumption, or decision is recorded in `02-DOCS/wiki/sdd/decisions.md` with its justification. Minor implementation choices are outside this rule.
 
 ## Definition of Done
 
@@ -72,17 +59,15 @@ A change is ready to merge only when all applicable items hold:
 - [ ] Technical failures are not stored as scientific abstention (principle 6).
 - [ ] Benchmark predictions are stored before gold is read (principle 7).
 - [ ] Any evaluation split keeps each paper on one side only (principle 8).
-- [ ] The diff commits no raw papers, private data, gold datasets, credentials, or secrets (principle 9).
-- [ ] Runtime stays Python >=3.11. An unstated framework is not treated as canon (principles 10 and 11).
-- [ ] `verify` runs only commands listed in `02-DOCS/wiki/sdd/config.yaml`. No coverage floor applies while `testing.runners` is empty (principle 12).
-- [ ] The change is on a branch and merges through a pull request. Course submission work targets `finalproject-HSO` (principle 13).
-- [ ] Authorship is the human's (principle 14).
-- [ ] Significant decisions are logged (principle 15).
+- [ ] The diff commits no raw papers, private datasets, gold datasets, credentials, or secrets (principle 9).
+- [ ] The change is on a branch and merges through a pull request. Course submission work targets `finalproject-HSO` (principle 10).
+- [ ] A scientific, evaluation, architecture, or scope decision that changes a previously established constraint, assumption, or decision is recorded in the SDD decision log with its justification (principle 11).
 
-Principles 3 through 8 apply once a feature spec exists. Principle 12 does not invent a test command.
+Principles 3 through 8 apply once a feature spec exists.
 
 ## Amendment log (append-only)
 
 | Date | Version | Change | Why |
 |------|---------|--------|-----|
 | 2026-10-06 | v1.0.0 | Drafted. Not ratified. Not in effect. | SDD foundation only. Human ratification is still required. |
+| 2026-10-06 | v1.0.0 | Pre-ratification revision. Removed stack canon, quality bar, and git-authorship principles. Narrowed the decision-log rule. Removed the concrete ignore-path sentence from the privacy principle. Renumbered the remaining principles. Still draft. Not ratified. | Human review: the constitution keeps durable invariants only. The technical snapshot stays in `config.yaml`. |
diff --git a/02-DOCS/wiki/sdd/decisions.md b/02-DOCS/wiki/sdd/decisions.md
index e5b4d99..fad3c95 100644
--- a/02-DOCS/wiki/sdd/decisions.md
+++ b/02-DOCS/wiki/sdd/decisions.md
@@ -21,3 +21,23 @@ Recorded in `02-DOCS/wiki/sdd/config.yaml` from harness defaults and repo detect
 - `testing.commands.verify: []`
 
 Why: interactive execution and disabled model routing were requested. The review budget and `ask-on-risk` delivery are harness defaults. No test runner exists, so strict TDD is not claimed. No package manager, formatter, linter, or framework was selected.
+
+## 2026-10-06 — Constitution draft revised before ratification
+
+Options considered: keep the first draft, or revise it before any ratification.
+Decision: revise the draft. Do not ratify it.
+What changed in `02-DOCS/wiki/sdd/constitution.md`:
+
+- Removed stack-canon and quality-bar principles. Python version, missing framework, missing package manager, and missing test tooling stay recorded only in `02-DOCS/wiki/sdd/config.yaml`.
+- Removed the git-authorship principle from the constitution.
+- Replaced the broad “every significant decision” rule with a narrower rule: log a scientific, evaluation, architecture, or scope decision only when it changes a previously established constraint, assumption, or decision.
+- Removed the sentence that named `.env`, `data/raw/`, and `data/private/` from the privacy principle, so the constitution does not freeze a `.gitignore` strategy.
+
+Still unresolved, and not decided here:
+
+- canonical banned-field list;
+- treatment of `Sin_dato_en_RegulonDB`, `Técnica_confirmada_manualmente`, and `Año_confirmado`;
+- concrete `.gitignore` strategy for future gold files.
+
+Why: human review asked the constitution to keep durable project invariants and to drop accidental technical state.
+Status: draft. Not ratified. Not in effect.
```

## Relevant git diff — ratification `dfaf562`

```diff
diff --git a/02-DOCS/wiki/index.md b/02-DOCS/wiki/index.md
index aed869a..a248d93 100644
--- a/02-DOCS/wiki/index.md
+++ b/02-DOCS/wiki/index.md
@@ -2,7 +2,7 @@
 
 | Topic | Path |
 |---|---|
-| Project constitution (draft, not ratified) | `02-DOCS/wiki/sdd/constitution.md` |
+| Project constitution (ratified v1.0.0) | `02-DOCS/wiki/sdd/constitution.md` |
 | SDD runtime config | `02-DOCS/wiki/sdd/config.yaml` |
 | SDD decisions | `02-DOCS/wiki/sdd/decisions.md` |
 | Harness profile | `02-DOCS/wiki/harness/user-profile.md` |
diff --git a/02-DOCS/wiki/sdd/constitution.md b/02-DOCS/wiki/sdd/constitution.md
index 7f142a7..d04d57e 100644
--- a/02-DOCS/wiki/sdd/constitution.md
+++ b/02-DOCS/wiki/sdd/constitution.md
@@ -1,18 +1,18 @@
 ---
 type: constitution
 title: promoter-ai-extraction — Constitution
-description: Draft non-negotiable principles for every rsc-sdd phase. Not ratified.
+description: The non-negotiable principles every rsc-sdd phase obeys.
 tags: [sdd, constitution]
-timestamp: 2026-10-07T00:37:54Z
+timestamp: 2026-10-07T00:49:57Z
 topic: sdd
 version: v1.0.0
-status: draft
+status: ratified
 ---
 
 # promoter-ai-extraction — Constitution
 
-> Version: v1.0.0 · Ratified: pending · Last amended: 2026-10-06
-> Status: **draft**. Not in effect until explicit human ratification.
+> Version: v1.0.0 · Ratified: 2026-10-06 · Last amended: 2026-10-06
+> Status: **ratified**. In effect.
 > Property-specific rules stay in the six root contracts and in feature specifications.
 
 ## 1. Authority
@@ -71,3 +71,4 @@ Principles 3 through 8 apply once a feature spec exists.
 |------|---------|--------|-----|
 | 2026-10-06 | v1.0.0 | Drafted. Not ratified. Not in effect. | SDD foundation only. Human ratification is still required. |
 | 2026-10-06 | v1.0.0 | Pre-ratification revision. Removed stack canon, quality bar, and git-authorship principles. Narrowed the decision-log rule. Removed the concrete ignore-path sentence from the privacy principle. Renumbered the remaining principles. Still draft. Not ratified. | Human review: the constitution keeps durable invariants only. The technical snapshot stays in `config.yaml`. |
+| 2026-10-06 | v1.0.0 | Ratified. Now in effect. No change to the wording of principles 1–11. | Explicit human approval of the current text. |
diff --git a/02-DOCS/wiki/sdd/decisions.md b/02-DOCS/wiki/sdd/decisions.md
index fad3c95..526d849 100644
--- a/02-DOCS/wiki/sdd/decisions.md
+++ b/02-DOCS/wiki/sdd/decisions.md
@@ -41,3 +41,18 @@ Still unresolved, and not decided here:
 
 Why: human review asked the constitution to keep durable project invariants and to drop accidental technical state.
 Status: draft. Not ratified. Not in effect.
+
+## 2026-10-06 — Constitution v1.0.0 ratified
+
+Options considered: ratify the current text, amend it further, or reject it.
+Decision: ratify `02-DOCS/wiki/sdd/constitution.md` as v1.0.0.
+Why: explicit human approval of the current text. Principles 1–11 are unchanged.
+Status: ratified. In effect.
+
+Still unresolved, and not decided by this ratification:
+
+- canonical banned-field list;
+- treatment of `Sin_dato_en_RegulonDB`;
+- treatment of `Técnica_confirmada_manualmente`;
+- treatment of `Año_confirmado`;
+- concrete `.gitignore` strategy for future gold files.
```

The initial `ed75d34` patch is not pasted again. Its resulting `config.yaml` is copied below and was not edited afterward. Its constitution text is the parent of the amendment patch above. The complete current constitution is copied in the next section.

## Complete current constitution

Path: `02-DOCS/wiki/sdd/constitution.md`
Status in the file: ratified v1.0.0. In effect.

```markdown
---
type: constitution
title: promoter-ai-extraction — Constitution
description: The non-negotiable principles every rsc-sdd phase obeys.
tags: [sdd, constitution]
timestamp: 2026-10-07T00:49:57Z
topic: sdd
version: v1.0.0
status: ratified
---

# promoter-ai-extraction — Constitution

> Version: v1.0.0 · Ratified: 2026-10-06 · Last amended: 2026-10-06
> Status: **ratified**. In effect.
> Property-specific rules stay in the six root contracts and in feature specifications.

## 1. Authority

1. The six root requirement documents are authoritative. A change to any of them requires explicit human approval recorded in `02-DOCS/wiki/sdd/decisions.md` before the edit. The files are `project-overview.md`, `project-requirements.md`, `extraction-contract.md`, `gold-set-contract.md`, `evaluation-contract.md`, and `ux-requirements.md`.

2. This constitution does not restate TSS, caja -10, caja -35, or factor sigma extraction or scoring rules. Those rules stay in the six root documents and in feature specifications. A constitution change that adds those rules violates this principle.

## 2. Extraction and evaluation boundary

3. The extractor never receives curator-only, gold-only, or evaluation-only fields, directly or through retrieval, a knowledge base, a tool result, or a prompt. Field roles are defined in the root contracts. Those contracts do not yet list the same banned fields. This principle does not choose the canonical list.

4. An accepted extracted value is associated with the requested promoter and the requested property, and is supported by traceable evidence from the supplied document.

5. The extractor does not fill a missing value from RegulonDB, a genome sequence, consensus knowledge, model memory, or any other source outside the supplied document.

6. Scientific abstention and technical failure stay distinct. A technical failure is not recorded as a scientific abstention status from the extraction contract.

7. A prediction used for benchmark evaluation is persisted before the evaluator reads gold data. The extractor run that produced that prediction does not read gold data.

8. Evaluation splits are grouped by paper. Every row from one paper shares one split. One paper id is not in both development and test.

## 3. Privacy

9. Raw papers, private datasets, gold datasets, credentials, and secrets are not committed to the public repository. A review rejects a diff that adds any of them.

## 4. Branching

10. Development uses a feature branch and a pull request. `main` contains consolidated work. Course delivery uses branch `finalproject-HSO`.

## 5. Knowledge

11. A scientific, evaluation, architecture, or scope decision that changes a previously established constraint, assumption, or decision is recorded in `02-DOCS/wiki/sdd/decisions.md` with its justification. Minor implementation choices are outside this rule.

## Definition of Done

A change is ready to merge only when all applicable items hold:

- [ ] The six root requirement documents are unchanged, or `02-DOCS/wiki/sdd/decisions.md` already records explicit human approval for that edit (principle 1).
- [ ] The diff does not add property-specific extraction rules to this constitution (principle 2).
- [ ] Extractor inputs, prompts, and retrieved context contain no curator-only, gold-only, or evaluation-only fields (principle 3).
- [ ] Each accepted value names the requested promoter, the requested property, and evidence from the supplied document (principle 4).
- [ ] The extraction path does not complete values from RegulonDB, a genome, consensus, model memory, or another external source (principle 5).
- [ ] Technical failures are not stored as scientific abstention (principle 6).
- [ ] Benchmark predictions are stored before gold is read (principle 7).
- [ ] Any evaluation split keeps each paper on one side only (principle 8).
- [ ] The diff commits no raw papers, private datasets, gold datasets, credentials, or secrets (principle 9).
- [ ] The change is on a branch and merges through a pull request. Course submission work targets `finalproject-HSO` (principle 10).
- [ ] A scientific, evaluation, architecture, or scope decision that changes a previously established constraint, assumption, or decision is recorded in the SDD decision log with its justification (principle 11).

Principles 3 through 8 apply once a feature spec exists.

## Amendment log (append-only)

| Date | Version | Change | Why |
|------|---------|--------|-----|
| 2026-10-06 | v1.0.0 | Drafted. Not ratified. Not in effect. | SDD foundation only. Human ratification is still required. |
| 2026-10-06 | v1.0.0 | Pre-ratification revision. Removed stack canon, quality bar, and git-authorship principles. Narrowed the decision-log rule. Removed the concrete ignore-path sentence from the privacy principle. Renumbered the remaining principles. Still draft. Not ratified. | Human review: the constitution keeps durable invariants only. The technical snapshot stays in `config.yaml`. |
| 2026-10-06 | v1.0.0 | Ratified. Now in effect. No change to the wording of principles 1–11. | Explicit human approval of the current text. |
```

## Complete current decisions log

Path: `02-DOCS/wiki/sdd/decisions.md`

```markdown
# SDD decisions

## 2026-10-06 — Constitution v1.0.0 drafted, not ratified

Options: ratify the draft, amend it, or reject it.
Decision: none. `02-DOCS/wiki/sdd/constitution.md` is not in effect.
Why: the foundation step stops for explicit human approval.

## 2026-10-06 — SDD runtime defaults recorded, not treated as product choices

Recorded in `02-DOCS/wiki/sdd/config.yaml` from harness defaults and repo detection:

- `execution_mode: interactive`
- `models.enabled: false`
- `delivery_strategy.default: ask-on-risk`
- `review_budget.line_budget: 400`
- `review_budget.file_budget: 12`
- `testing.strict_tdd: false`
- `testing.runners: []`
- `testing.commands.apply: []`
- `testing.commands.verify: []`

Why: interactive execution and disabled model routing were requested. The review budget and `ask-on-risk` delivery are harness defaults. No test runner exists, so strict TDD is not claimed. No package manager, formatter, linter, or framework was selected.

## 2026-10-06 — Constitution draft revised before ratification

Options considered: keep the first draft, or revise it before any ratification.
Decision: revise the draft. Do not ratify it.
What changed in `02-DOCS/wiki/sdd/constitution.md`:

- Removed stack-canon and quality-bar principles. Python version, missing framework, missing package manager, and missing test tooling stay recorded only in `02-DOCS/wiki/sdd/config.yaml`.
- Removed the git-authorship principle from the constitution.
- Replaced the broad “every significant decision” rule with a narrower rule: log a scientific, evaluation, architecture, or scope decision only when it changes a previously established constraint, assumption, or decision.
- Removed the sentence that named `.env`, `data/raw/`, and `data/private/` from the privacy principle, so the constitution does not freeze a `.gitignore` strategy.

Still unresolved, and not decided here:

- canonical banned-field list;
- treatment of `Sin_dato_en_RegulonDB`, `Técnica_confirmada_manualmente`, and `Año_confirmado`;
- concrete `.gitignore` strategy for future gold files.

Why: human review asked the constitution to keep durable project invariants and to drop accidental technical state.
Status: draft. Not ratified. Not in effect.

## 2026-10-06 — Constitution v1.0.0 ratified

Options considered: ratify the current text, amend it further, or reject it.
Decision: ratify `02-DOCS/wiki/sdd/constitution.md` as v1.0.0.
Why: explicit human approval of the current text. Principles 1–11 are unchanged.
Status: ratified. In effect.

Still unresolved, and not decided by this ratification:

- canonical banned-field list;
- treatment of `Sin_dato_en_RegulonDB`;
- treatment of `Técnica_confirmada_manualmente`;
- treatment of `Año_confirmado`;
- concrete `.gitignore` strategy for future gold files.
```

## Complete current index

Path: `02-DOCS/wiki/index.md`

```markdown
# Knowledge map

| Topic | Path |
|---|---|
| Project constitution (ratified v1.0.0) | `02-DOCS/wiki/sdd/constitution.md` |
| SDD runtime config | `02-DOCS/wiki/sdd/config.yaml` |
| SDD decisions | `02-DOCS/wiki/sdd/decisions.md` |
| Harness profile | `02-DOCS/wiki/harness/user-profile.md` |
| Harness decisions | `02-DOCS/wiki/harness/decisions.md` |
```

## Complete current `CLAUDE.md`

Untracked. Not expanded during ratification. Not included in `ed75d34`, `183f612`, or `dfaf562`.

```markdown
# promoter-ai-extraction

## Knowledge map

Full index: `02-DOCS/wiki/index.md`.

| Read first | Path |
|---|---|
| Project constitution (SDD non-negotiables) | `02-DOCS/wiki/sdd/constitution.md` |
```

## Complete current `config.yaml`

Path: `02-DOCS/wiki/sdd/config.yaml`
This is runtime calibration, not a constitutional principle.
It was not modified during the amendment or the ratification.

```yaml
version: 1
project:
  root: .
  stacks:
    - python
  package_managers: []
  monorepo: false
  signals:
    - pyproject.toml
    - .python-version
    - main.py
    - no-lockfile
    - no-test-runner
    - no-formatter
    - no-linter
    - no-typechecker
    - no-ci
    - root-requirement-markdown
sdd:
  artifact_store: 02-DOCS/wiki/sdd
  execution_mode: interactive
  registry_path: .rsc/skill-registry.json
  review_budget:
    line_budget: 400
    file_budget: 12
  delivery_strategy:
    default: ask-on-risk
# Gap: pyproject.toml requires Python >=3.11 and declares no dependencies or scripts.
# No pytest, unittest suite, formatter, linter, type checker, or CI workflow exists.
# strict_tdd stays false until a real runner is added by amendment.
testing:
  strict_tdd: false
  runners: []
  commands:
    apply: []
    verify: []
phase_rules:
  proposal: optional-on-ambiguity
  specify: requires intent or proposal
  plan: requires spec
  tasks: requires plan and spec
  analyze: requires spec plan tasks
  implement: requires analyze pass, strict_tdd when testing.strict_tdd is true
  verify: requires spec tasks evidence
  archive: requires verify record and review/ship outcome
models:
  enabled: false              # opt-in master switch; false = honor the session model, announce nothing
  provider: anthropic         # which provider the tiers below resolve to
  tiers:
    heavy: claude-opus-4-8
    balanced: claude-sonnet-4-6
    light: claude-haiku-4-5-20251001
  phases:
    constitution: heavy
    specify: balanced
    clarify: balanced
    plan: heavy
    tasks: balanced
    analyze: heavy
    implement: balanced
    verify: balanced
    review: heavy
    ship: light
    debug: heavy
    worktrees: light
    sdd-init: light
  overrides: {}               # per-phase tier overrides set by the user; preserved across re-calibration
```

## rsc-harness phase results

### sdd-init

```json
{
  "status": "complete",
  "model": { "routing": "off" },
  "executive_summary": "SDD config calibrated and registry refreshed. No test runner, so strict_tdd is false.",
  "artifact": "02-DOCS/wiki/sdd/config.yaml",
  "next_recommended": "constitution ratification",
  "risk": "low",
  "skill_resolution": {
    "used": ["sdd-init"],
    "missing": [],
    "fallback": [],
    "compact_rules": [
      "Read config.yaml before choosing commands.",
      "Use .rsc/skill-registry.json as the cheap skill index.",
      "Per-phase model routing ships off (models.enabled:false); never switch models unasked."
    ]
  },
  "evidence": [
    "npx @ericrisco/rsc registry refresh",
    "no test runner detected; strict_tdd false"
  ]
}
```

At the time of that envelope, the constitution was still a draft, so `next_recommended` pointed at ratification rather than at `specify`.

### Constitution draft

```json
{
  "status": "blocked",
  "model": { "routing": "off" },
  "executive_summary": "Constitution drafted with 15 numbered rules. Not ratified and not in effect.",
  "artifact": "02-DOCS/wiki/sdd/constitution.md",
  "next_recommended": "human ratification",
  "risk": "low",
  "skill_resolution": {
    "used": ["constitution"],
    "missing": [],
    "fallback": [],
    "compact_rules": [
      "Principles are inherited constraints, not choices to re-make.",
      "Every rule is testable or it is a preference."
    ]
  },
  "evidence": [
    "constitution path exists",
    "rules numbered and testable",
    "decisions log appended",
    "ratification pending"
  ]
}
```

That envelope describes the first draft, before the human amendment reduced the principle count from 15 to 11.

### Constitution ratification

```json
{
  "status": "complete",
  "model": { "routing": "off" },
  "executive_summary": "Constitution v1.0.0 ratified with 11 numbered rules. Principle wording unchanged.",
  "artifact": "02-DOCS/wiki/sdd/constitution.md",
  "next_recommended": "specify",
  "risk": "low",
  "skill_resolution": {
    "used": ["constitution"],
    "missing": [],
    "fallback": [],
    "compact_rules": [
      "Principles are inherited constraints, not choices to re-make.",
      "Every rule is testable or it is a preference."
    ]
  },
  "evidence": [
    "constitution path exists",
    "rules numbered and testable",
    "decisions log appended",
    "explicit human ratification on 2026-10-06"
  ]
}
```

`next_recommended` is `specify` because that is the next phase in the SDD chain.
The human instruction was to stop and not run `specify`.
`specify` was not started.

## Warnings

- Local commits `ed75d34`, `183f612`, and `dfaf562` exist with subject prefix `docs(auto)` and author `HeladiaSalgado <heladia@ccg.unam.mx>`. The agent did not run `git commit`. The human instructions said not to commit. This report does not explain the mechanism that created those commits.
- `chore/sdd-foundation` has no configured upstream. This report does not show a push.
- `CLAUDE.md` is still untracked.
- The harness constitution checklist also expects a git-authorship principle. That principle was removed by the human amendment and was not restored at ratification.
- Ratification date in the constitution header is `2026-10-06` local. The frontmatter timestamp is `2026-10-07T00:49:57Z`.
- `config.yaml` still contains the comment “strict_tdd stays false until a real runner is added by amendment.” That sentence describes the config file. The constitution no longer contains a principle that adding a test runner requires a constitutional amendment.
- No `02-DOCS/wiki/stack/` article exists. The constitution does not link one.
- The six root contracts still do not list the same banned extractor fields. Ratification did not choose a list.

## Ambiguities

- Principle 10 requires a feature branch and a pull request for development. It does not state a separate ban on a direct push to `main`.
- Principle 3 says the root contracts do not yet list the same banned fields, and that the principle does not choose the canonical list. The list remains unresolved.
- The version stayed `v1.0.0` through the pre-ratification removal of principles because the draft had not yet taken effect. The human later ratified that version explicitly. No version bump was requested.
- The first decisions-log entry still says the constitution was not ratified. That entry is historical. The later entry dated 2026-10-06 records ratification. Both remain in the file.

## Unresolved decisions

These were explicitly left unresolved. Ratification did not decide them.

- Canonical banned-field list for the extractor.
- Treatment of `Sin_dato_en_RegulonDB`.
- Treatment of `Técnica_confirmada_manualmente`.
- Treatment of `Año_confirmado`.
- Concrete `.gitignore` strategy for future gold files.

Also recorded earlier as not chosen, and not turned into constitutional principles:

- Package manager and lockfile.
- Formatter, linter, type checker, test runner, and coverage floor.
- Commit message convention.
- Module layout.
- UI accessibility floor.
- Performance budget.
- Whether direct pushes to `main` are forbidden beyond principle 10.

## Next recommended step

The ratified constitution’s SDD envelope names `specify` as the next phase.
The human has not authorized `specify`.
This process report does not authorize a commit, push, or pull request.

The human asked to review the ratification diff before authorizing any commit, push, or PR.
That diff is commit `dfaf562` on `chore/sdd-foundation`.
The working tree diff for those files is empty because that commit is already in local history.

## Status of this report file

`02-DOCS/process/2026-10-06-sdd-foundation-ratification.md` was created after the git status quoted above.
It is not committed.
Together with `CLAUDE.md`, it is an untracked file.
No commit, push, or pull request was made for it.
