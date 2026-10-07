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
