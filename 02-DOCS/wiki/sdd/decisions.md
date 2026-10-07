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
