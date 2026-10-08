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

## 2026-10-06 — Guided extraction baseline scoped for specify

Options considered: continue manual curation only; define the smallest guided extraction and evaluation slice; or include the wider Part 1 product with UI, retrieval, agents, and deployment.

Decision: draft `guided-extraction-baseline` as the first vertical slice. It accepts TEI/XML or TXT for an identified paper and promoter; produces independent, evidence-grounded conclusions for TSS, caja -10, caja -35, and factor sigma; validates and persists predictions before leakage-safe evaluation; and keeps development/test splits grouped by paper.

Explicitly outside this feature: RAG, embeddings, vector databases, agents, UI, deployment, promoter discovery, complex entity resolution, direct figure reading, PDF-to-GROBID conversion, RegulonDB writes, supplements, and biological sigma equivalences.

Why: this is the smallest slice that tests the project's central scientific boundary and produces an objective baseline before architectural complexity is justified.

Status: specification draft only. Human approval and `clarify` are still required. No plan or implementation decision is made here.

Open points that block planning:

- exact extractor-input field policy for benchmark cases;
- whether `INVALID_CANDIDATE` is a terminal status or a diagnostic flag;
- definitive parsing of multiple-value cells into comparison sets.

Deferred points remain recorded in the spec, including the project-wide field treatments and concrete future-gold ignore strategy.

## 2026-10-06 — Guided extraction leakage boundary fixed

Options considered: denylist only; allowlist only; or a closed allowlist plus a defensive denylist.

Decision: the guided extraction baseline uses both controls. `extractor_allowed` contains only the supplied TEI/XML or TXT, its format and paper identifier, promoter identifier/name, optional paper-specific gene synonym, and the requested property when execution is per property. Every field outside that allowlist is rejected. A defensive `extractor_forbidden` list also blocks all known gold, curator, and evaluator-only fields, including renamed, nested, joined, derived, retrieved, or embedded forms.

Where root contracts enumerate fields differently, the conservative leakage interpretation applies. `Sin_dato_en_RegulonDB`, `Técnica_confirmada_manualmente`, `Año_confirmado`, and curator/gold `Evidencia` remain outside extraction.

Why: an allowlist prevents omissions in an evolving gold schema; the denylist makes known leakage categories explicit and auditable. This fixes a scientific and evaluation boundary that was previously open.

## 2026-10-06 — `INVALID_CANDIDATE` made diagnostic for the baseline

Options considered: terminal scientific property status, or candidate-level diagnostic rejection reason.

Decision: `INVALID_CANDIDATE` is a candidate-level diagnostic rejection reason for `guided-extraction-baseline`. A rejected candidate remains outside accepted predictions and contributes no predicted value to evaluation. Candidate rejection is neither a scientific abstention nor a technical failure. The property receives a separate terminal status justified by the remaining document evidence.

Why: the authoritative contracts call `INVALID_CANDIDATE` provisional and explicitly allow it to become a diagnostic flag. No authoritative contract requires it to remain terminal.

The multiple-value gold parser remains unresolved. The documents show only `TAATAA + TATAAT`, the definitive parser is explicitly open, and no permitted local copy of the current gold was available for format-only inspection. PLAN remains blocked until the complete set of raw multi-value encodings is inspected without exposing values to extraction.

## 2026-10-06 — Current-workset multiple-value parser fixed

Evidence inspected: `02-DOCS/data/SUBSET_GOLD.xlsx` in strict read-only mode, using only worksheet structure plus `Propiedad`, `GT_para_referencia`, and non-positive-marker checks needed by the evaluator. No gold value was exposed to the extractor.

Observed target encodings:

- Caja -10: 101 non-empty targets; 100 single values; one two-value cell using literal delimiter ` + `.
- Caja -35: 86 non-empty targets; all single values; one nucleotide sequence contains an internal typographic line break.
- TSS: 98 non-empty single integer targets; 91 stored as text and 7 as numeric cells.
- Factor sigma: 44 non-empty single labels.
- No comma, semicolon, slash, list, or other multi-value syntax; no ambiguous target cell; no empty or non-positive marker in `GT_para_referencia`.

Decision: freeze a minimal property-specific parser for this baseline. Preserve the original cell and raw tokens. Split only the observed caja -10 form consisting of exactly two non-empty nucleotide tokens separated by literal ` + `. Treat the caja -35 line break as part of one raw token and remove it only during permitted typographic normalization. Treat each observed TSS and sigma cell as one token. Normalize after tokenization, represent values as unordered sets, and deduplicate only after normalization while preserving raw provenance.

Any unobserved or ambiguous syntax produces `PARSE_ERROR / NEEDS_REVIEW` and is not scored until explicit adjudication.

Why: the rule covers every encoding in the current workset without inventing delimiters or mixing parsing with matching/scoring.

Status: the final PLAN blocker recorded by clarify is resolved. The spec is `clarified`; PLAN is unlocked but has not started.

## 2026-10-07 — Minimal architecture selected for guided extraction baseline

Options considered: multiple services with a database; a framework-led application; or one synchronous Python process with small modules, explicit contracts, and local files.

Decision: use one synchronous Python process. Keep document loading, request-boundary validation, property extraction, property-specific normalization, output validation, immutable prediction persistence, evaluator-only gold loading/parsing, set comparison, and metrics as separate responsibilities. Persist each extraction run as an immutable, versioned local JSON file before evaluator code can open the gold workbook. Use no database, web framework, asynchronous orchestrator, agent framework, retrieval system, or deployment infrastructure in this slice.

The extraction request is an immutable closed shape with no arbitrary metadata. Benchmark inputs are supplied explicitly or through a separate allowlisted case manifest; extraction code never opens the gold workbook to construct a request. The evaluator accepts a verified persisted reference, not an in-memory prediction, before loading gold.

Why: this is the smallest architecture that makes the scientific boundaries and persist-before-gold ordering mechanically testable without introducing infrastructure unrelated to the first slice.

Proposed minimal dependencies:

- `pytest` for deterministic unit, contract, and integration tests;
- `openpyxl` for read-only XLSX loading and synthetic workbook fixtures;
- `defusedxml` for fail-closed TEI/XML parsing.

Still requiring human decisions, but not blocking TASKS:

1. concrete model provider/model, credential source, context limit, and reproducibility settings before implementing the real backend adapter;
2. whether the final benchmark publishes an additional end-to-end metric that treats technical failures as unrecovered positives, beyond separate technical-failure and evaluated-coverage reporting.

Status: plan drafted. TASKS is structurally unblocked but has not started.

## 2026-10-07 — T031: headline treatment of technical failures

Context: the plan left open whether final reporting adds an end-to-end denominator that treats technical failures as unrecovered positives, or keeps only scientific metrics conditioned on technically evaluable cases.

Options considered:

1. headline = scientific metrics only, on technically evaluable rows; technical failures reported separately;
2. headline = end-to-end metrics that count a technical failure on a positive gold row as FN; keep a secondary conditioned scientific view;
3. collapse technical failure into scientific abstention in scoring.

Decision: option 2. Explicit human approval for `guided-extraction-baseline` T031.

For the final benchmark:

1. The end-to-end view treats a technical failure on a positive gold row as an unrecovered positive: it contributes FN to end-to-end recall/F1.
2. A separate scientific view remains, conditioned on technically evaluable cases.
3. Always report separately: coverage, technical-failure count, technical-failure rate, and scientific abstentions.
4. A technical failure is never converted into a scientific abstention, nor the reverse (constitution principle 6).
5. The system headline is the end-to-end view, because it reflects the full pipeline.
6. The conditioned scientific view is a secondary diagnostic metric.
7. The current subset remains a positive-target benchmark. It must not be read as a complete evaluation of negatives, abstentions, or global precision outside that universe.

Why: headline metrics must not hide pipeline failures as if those rows were never attempted, while still preserving a diagnostic view of extraction quality when the pipeline actually produces a scientific result.

Status: T031 resolved. Remaining HUMAN_DECISION_REQUIRED: T036 provider/model selection. T042 must apply both views; T027–T035 keep the existing separate failure/coverage counts until that report is wired.

## 2026-10-08 — T036: OpenAI Responses API backend for the real baseline

Context: the plan left the real extractor adapter blocked until provider, model, credential source, structured-output mode, context handling, and reproducibility settings were chosen.

Options considered:

1. hosted OpenAI SDK behind the existing `ModelBackend` port;
2. an institution-approved non-OpenAI endpoint;
3. a local model;
4. a multi-provider layer (LiteLLM, LangChain, or automatic fallback).

Decision: option 1. Explicit human approval for `guided-extraction-baseline` T036.

| Item | Choice |
|---|---|
| Provider | OpenAI |
| API / interface | Responses API (`/v1/responses`) |
| Initial model | `gpt-6.1-sol` |
| Credential | `OPENAI_API_KEY` from the process environment only |
| Structured output | Responses API JSON Schema (`text.format`, `type=json_schema`, `strict=true`) mapped explicitly onto `RawPropertyPayload` |
| Fallback | none; a `gpt-6.1-sol` failure is a technical failure |
| Adapter shape | `PropertyExtractor` → `ModelBackend` → `OpenAIModelBackend` |

Credential rules:

- Read the key only from the environment variable `OPENAI_API_KEY`.
- Do not store it in code, versioned configuration, logs, prediction artifacts, or SDD reports.

Structured output and errors:

- The adapter must require schema-constrained output compatible with `RawPropertyPayload` / `PropertyExtractor` / `OutputValidator`.
- Do not accept free text and then guess its structure.
- Convert provider error, timeout, incomplete response, schema violation, structured-output failure, and adapter parse failure into `BackendFailure` → `TechnicalFailure`.
- Never convert those events into a scientific abstention (constitution principle 6).

Prompt:

- Build the prompt only from `SafeExtractionInput`.
- Do not change scientific extraction rules.
- Do not include gold, `GT_para_referencia`, curator-only modality, split, metrics, expected target, `SUBSET_GOLD.xlsx`, or other evaluator-only fields.

Context limit:

- Do not silently truncate the supplied document.
- If the SafeExtractionInput cannot be submitted within the published context window of `gpt-6.1-sol`, return technical failure `DOCUMENT_TOO_LARGE`.
- A numeric token cap is not frozen here; T038 must use the model's published window and fail closed.

Reproducibility metadata (no secrets) on each real run, via the existing persistence `system_fingerprint` / run metadata:

- `provider = openai`
- `model = gpt-6.1-sol`
- `api = responses`
- prompt/version identifier
- payload schema version
- generation/configuration parameters actually used
- existing document SHA-256
- run timestamp
- existing software/version metadata when the architecture already records it
- provider snapshot/model id from the API response, when present

Architecture constraints for T037–T038:

- Do not couple `GuidedExtractionService` to the OpenAI SDK.
- Do not introduce LiteLLM, LangChain, an agent framework, multi-provider fallback, RAG, or FastAPI.
- Keep `ModelBackend` as the extension point for future backends.
- Adding the official `openai` Python SDK is deferred to T038; it is not a current runtime dependency.

Why: this is the smallest hosted adapter that satisfies structured-output enforcement, env-only credentials, and the existing port without mixing models inside one benchmark.

Status: T036 resolved. T037–T038 remain unimplemented.
