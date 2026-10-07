---
type: constitution
title: promoter-ai-extraction — Constitution
description: Draft non-negotiable principles for every rsc-sdd phase. Not ratified.
tags: [sdd, constitution]
timestamp: 2026-10-07T00:37:54Z
topic: sdd
version: v1.0.0
status: draft
---

# promoter-ai-extraction — Constitution

> Version: v1.0.0 · Ratified: pending · Last amended: 2026-10-06
> Status: **draft**. Not in effect until explicit human ratification.
> No `02-DOCS/wiki/stack/` article exists. This file does not invent stack mechanics.
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

9. Raw papers, private datasets, gold datasets, credentials, and secrets are not committed to the public repository. A review rejects a diff that adds any of them. `.env`, `data/raw/`, and `data/private/` stay untracked.

## 4. Stack canon

10. The detected runtime is Python >=3.11, declared in `pyproject.toml` and `.python-version`. No framework, model provider, API, database, or frontend is canon. Making one canon requires an amendment.

11. No package manager and no lockfile are canon. Dependencies, when added, are declared in `pyproject.toml`.

## 5. Quality bar

12. No test runner, formatter, linter, or type checker is configured. `02-DOCS/wiki/sdd/config.yaml` records `testing.strict_tdd: false` and `testing.runners: []`. `verify` must not require a test, lint, format, typecheck, or coverage command that the config does not list. Adding a runner is an amendment.

## 6. Branching and authorship

13. Development uses a feature branch and a pull request. `main` contains consolidated work. Course delivery uses branch `finalproject-HSO`.

14. **Git authorship is the human's.** Commits and pull requests carry no `Co-Authored-By` trailer for an AI and no "generated with" footer. Enforced at the `ship` phase.

## 7. Knowledge

15. Every significant decision is appended to `02-DOCS/wiki/sdd/decisions.md` with the date, the options, and the why. This constitution is the highest-order decision record, and only after ratification.

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
- [ ] The diff commits no raw papers, private data, gold datasets, credentials, or secrets (principle 9).
- [ ] Runtime stays Python >=3.11. An unstated framework is not treated as canon (principles 10 and 11).
- [ ] `verify` runs only commands listed in `02-DOCS/wiki/sdd/config.yaml`. No coverage floor applies while `testing.runners` is empty (principle 12).
- [ ] The change is on a branch and merges through a pull request. Course submission work targets `finalproject-HSO` (principle 13).
- [ ] Authorship is the human's (principle 14).
- [ ] Significant decisions are logged (principle 15).

Principles 3 through 8 apply once a feature spec exists. Principle 12 does not invent a test command.

## Amendment log (append-only)

| Date | Version | Change | Why |
|------|---------|--------|-----|
| 2026-10-06 | v1.0.0 | Drafted. Not ratified. Not in effect. | SDD foundation only. Human ratification is still required. |
