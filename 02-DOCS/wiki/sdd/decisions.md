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
