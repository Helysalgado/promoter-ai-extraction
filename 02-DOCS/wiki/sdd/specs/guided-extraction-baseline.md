---
type: spec
title: Spec — Guided extraction baseline
description: WHAT and WHY for the first leakage-safe vertical slice of guided bacterial-promoter property extraction.
tags: [sdd, spec, extraction, evaluation]
timestamp: 2026-10-07T02:45:00Z
topic: sdd
slug: guided-extraction-baseline
status: clarified
---

# Spec — Guided extraction baseline

> Slug: `guided-extraction-baseline` · Status: clarified · Created: 2026-10-06
> Inherits: [constitution](../constitution.md)
> Authoritative requirements: the six Markdown requirement documents in the repository root.

## Problem & why

A curator who already knows which bacterial promoter and paper are under review must still inspect the paper to determine which TSS, caja -10, caja -35, and factor sigma values are actually supported by that paper. The first vertical slice must make that bounded task reproducible, traceable, and objectively evaluable without letting the extractor see curator, gold, or evaluator-only answers.

The strongest limitation is that the current 329-row subset contains positive targets but does not systematically contain documentary negatives or curator evidence passages. It can evaluate value recovery and count abstentions on positive rows as misses, but it cannot by itself fully measure whether every abstention was scientifically appropriate or establish a complete false-assertion rate.

## Cost of not building it

The project would have no end-to-end scientific baseline against which later complexity could be justified. Curators would continue locating and interpreting each property manually, and later additions such as retrieval, agents, multimodal processing, or a user interface could not be compared with a leakage-safe reference workflow.

## The cheapest alternative

The cheapest alternative is continued manual review using the existing curated spreadsheet and the TEI/TXT papers. That preserves scientific judgment but does not produce a reproducible extractor, a validated structured prediction, or an independent benchmark result. A prompt-only demonstration is also insufficient because it does not enforce the evidence, abstention, persistence, and anti-leakage boundaries.

## Problem framing

- **Actor:** a curator expert in bacterial transcription regulation reviewing one identified promoter in one identified paper.
- **Current workaround:** manually search the paper, interpret each property, and compare conclusions with existing curatorial records.
- **Desired progress:** obtain one independent, structured, evidence-grounded conclusion for each requested property, followed by an objective leakage-safe comparison when the case belongs to the benchmark.
- **Constraints:** only the supplied TEI/XML or TXT is documentary evidence; the promoter is already identified; gold and curator-only data remain outside extraction; the current gold has no systematic evidence passages or documentary negatives.
- **Known versus assumed:** the contracts define the scientific task, states, provisional scoring, and current subset. Clarify fixed the extractor field boundary, candidate-rejection semantics, and the minimal parser for the observed current-gold encodings. Final project-wide scoring and future unobserved encodings remain outside this baseline decision.

## Directions considered

1. **Do not build the slice:** continue manual curation. This gives no reproducible system baseline.
2. **Build the guided extraction and evaluation baseline:** cover one paper and one identified promoter across four independent properties, with traceable evidence and leakage-safe scoring. This is the human-selected direction for this feature.
3. **Build the wider Part 1 product now:** include UI, retrieval, agents, deployment, and other later capabilities. This is rejected for this feature because those components are not required to test the central scientific boundary.

## Goals

- Accept one supplied TEI/XML or TXT representation and retain the identity of its paper.
- Accept an already identified promoter, including its name, identifier when available, and paper-specific gene synonym when supplied.
- Produce independent conclusions for TSS, caja -10, caja -35, and factor sigma.
- Support zero, one, or multiple accepted values for each property.
- Keep each accepted value's documentary form separate from its permitted normalized form.
- Associate each accepted value with the requested paper, promoter, property, and traceable evidence from the supplied document.
- Preserve qualifiers and uncertainty expressed by the paper.
- Abstain explicitly when the supplied representation does not support an accepted value.
- Keep scientific abstention distinct from technical failure.
- Validate a prediction against the scientific output contract before evaluation.
- Persist a benchmark prediction before any evaluator access to gold or evaluator-only data.
- Compare predictions and gold at `paper × promoter × property`, while keeping development/test splits grouped by paper.
- Produce objective baseline results by property and by the curatorial modality available only to the evaluator.

## Non-goals / out of scope

- Retrieval-augmented generation (RAG), embeddings, or a vector database.
- Agent-based extraction or orchestration.
- A web, desktop, or other graphical user interface.
- Deployment or production operations.
- Discovering promoters in a paper.
- Deciding whether a promoter is new or already exists in RegulonDB.
- Complex entity resolution or exhaustive historical-alias resolution.
- Direct multimodal reading of original figures.
- PDF-to-GROBID conversion.
- Reading unavailable supplementary materials.
- Writing to or editing RegulonDB.
- Resolving biological sigma equivalences such as `RpoS ↔ sigmaS ↔ sigma38`.
- Reconstructing missing values from a genome, consensus sequence, RegulonDB, model memory, or any source outside the supplied document.
- Freezing the final project-wide gold, final test split, or final evaluation protocol beyond what this baseline needs.
- Automatically evaluating evidence-passage correctness against a curator passage, because the current gold does not provide that reference systematically.

## Users & context

The primary user is a curator expert in bacterial transcription regulation. The user supplies a paper representation and the identity of one promoter that has already been selected for review. The user needs to inspect what the system found, the documentary basis for each accepted value, and every case in which the system declined to assert a value.

A benchmark operator may run the same extraction on a curated case. The benchmark operator may access gold data only through the evaluation side of the boundary and only after the prediction is persisted.

## Inputs and scientific boundary

The boundary uses two cumulative controls:

1. a closed `extractor_allowed` allowlist containing only the inputs needed for guided extraction;
2. a defensive `extractor_forbidden` denylist naming known leakage-bearing or unnecessary gold, curator, and evaluator fields.

A field must pass both controls. A field absent from `extractor_allowed` is rejected even when it is not named in `extractor_forbidden`. Renaming, nesting, joining, deriving, retrieving, or embedding a forbidden field does not make it permissible.

### `extractor_allowed`

| Conceptual field | Requirement |
|---|---|
| Supplied document | Exactly one TEI/XML or TXT representation of the identified paper. |
| Document format | `TEI/XML` or `TXT`, only to interpret the supplied representation. |
| Paper identifier | `ID_paper`, PMID, or another stable identifier for the supplied document. |
| Promoter identifier | `ID_promotor`, when available. |
| Promoter name | `Nombre_promotor`; required identity context. |
| Paper-specific gene synonym | `Sinonimo_gen_en_este_paper`, optional and used only to locate the already identified promoter. |
| Requested property | `Propiedad`, only when execution is performed per property; otherwise the run requests the fixed four-property set. |

No other paper metadata, promoter metadata, curatorial annotation, gold value, or evaluator output is allowed into extraction unless a future approved clarification adds it to this allowlist.

### `extractor_forbidden`

The following canonical denylist applies to this feature:

| Field or information class | Role outside extraction | Reason prohibited |
|---|---|---|
| `Fila_origen` | `evaluator_only` / audit-only | Gold-row provenance is unnecessary for extraction. |
| `Valor_RegulonDB` | `gold_only` / historical comparison | It can reveal or approximate the target. |
| `Sin_dato_en_RegulonDB` | `gold_only` / evaluator metadata | It reveals historical target availability and is not required to locate the promoter. |
| `Modalidad_origen` | `curator_only` / `evaluator_only` | It reveals how the curator found the answer and may leak reachability. |
| `Valor_verificado_manualmente` | `curator_only` / `gold_only` | It is a curator-reviewed target. |
| `GT_para_referencia` | `gold_only` / `evaluator_only` | It is the operational target. |
| `Año_confirmado` | `curator_only` / `evaluator_only` | It is curator-confirmed metadata not required by the guided extraction task. |
| `Técnica_confirmada_manualmente` | `curator_only` / `evaluator_only` | It is a curator-confirmed result; a paper-derived technique may be extracted independently, but this field may not enter extraction. |
| `Evidencia` from the gold or curator | `curator_only` / `gold_only` | Curator evidence can reveal the expected answer or location. System-produced evidence must come from the supplied document independently. |
| `PMID_fuente_alternativa` | `gold_only` / out of scope | It redirects extraction to another paper and can reveal target provenance. |
| Split assignment and benchmark inclusion/adjudication fields | `evaluator_only` | They control evaluation and are unnecessary for extraction. |
| Evaluation labels or outcomes | `evaluator_only` | Includes TP/FP/FN, match classes, misses, extra-value labels, scores, and metrics. |
| Previous outputs used as expected answers | `gold_only` / `evaluator_only` | They are targets regardless of their origin. |
| Any expected answer or field derived from the entries above | Same as its source | Indirect disclosure is leakage. |

Where the root contracts differ, this feature uses the most conservative interpretation: the field stays outside extraction. In particular, `Sin_dato_en_RegulonDB`, `Técnica_confirmada_manualmente`, and `Año_confirmado` are all forbidden even though the contracts enumerate them inconsistently.

The supplied document is the only source from which a missing property value may be completed.

## Behaviour

### Guided extraction

- The system rejects an unreadable, empty, malformed, or unsupported document as a technical failure rather than returning a scientific abstention.
- For a valid document and promoter identity, the system returns one independent result for each of TSS, caja -10, caja -35, and factor sigma.
- One property's result does not determine another property's status or value.
- The system may accept zero, one, or multiple values for a property.
- The system does not assign a value merely because it is nearby, biologically plausible, resembles a consensus, appears elsewhere in the paper for another promoter, or matches prior knowledge.

### Accepted values

- `EXTRACTED` contains at least one accepted value.
- Each accepted value preserves `value_raw` when a documentary form exists.
- `value_normalized` is separate from `value_raw` and uses only transformations permitted by the authoritative contracts.
- Each accepted value preserves applicable qualifiers such as `putative`, `predicted`, `possible`, or `-like`.
- A derivation note states any documentary transformation needed to obtain the normalized form without exposing private reasoning.
- Multiple accepted values remain distinct and retain their individual evidence references.

### Candidate diagnostics

- `INVALID_CANDIDATE` is not a terminal scientific status for a property in this baseline.
- It is a diagnostic rejection reason attached to an item in `candidate_values` when that candidate violates a scientific or formal rule.
- A rejected candidate remains separate from accepted `values` and never counts as a prediction.
- Rejecting a candidate does not by itself determine the property's terminal scientific status. The property independently receives the status justified by the remaining document evidence.
- A rejected candidate is neither a scientific abstention nor a technical failure.
- The diagnostic preserves the candidate, relevant evidence when available, and the rule-based rejection reason so the rejection is auditable.

### Evidence and location

- Every accepted value references one or more evidence items from the supplied document.
- The combined evidence establishes the value, requested property, and requested promoter.
- An evidence item preserves its fragment, source type, and all location detail that the supplied representation makes available.
- Location may identify a section, page, paragraph, table, figure, caption, or other stable document reference.
- The system does not invent unavailable location precision.
- Evidence may be distributed across multiple fragments.

### Scientific abstention

- `NOT_FOUND` states only that the extractor did not locate sufficient evidence in the representation it received.
- `INSUFFICIENT_EVIDENCE` includes relevant evidence but no accepted value.
- `UNSUPPORTED_MODALITY` includes a documentary pointer showing that the needed value depends on unavailable representation content; it is not inferred from the evaluator-only `Modalidad_origen`.
- `AMBIGUOUS` includes the evidence and may preserve candidates, but exposes no candidate as an accepted value.
- Every scientific abstention contains zero accepted values and a reason appropriate to its status.
- Scientific abstention is a valid extractor outcome even when evaluation later counts it as a miss against a positive target.
- `INVALID_CANDIDATE` is not included in the scientific abstention vocabulary.

### Technical failure

- A technical failure is reported outside the scientific result statuses.
- Technical failures include inability to read or interpret the supplied input and failures that prevent extraction from completing.
- A technical failure does not create a persisted scientific prediction that claims `NOT_FOUND`, `INSUFFICIENT_EVIDENCE`, `UNSUPPORTED_MODALITY`, or `AMBIGUOUS`.

### Validation

- Validation occurs before benchmark comparison and does not read the gold.
- Validation rejects an `EXTRACTED` result with no accepted value.
- Validation rejects an accepted value with no evidence.
- Validation rejects a scientific abstention containing accepted values.
- Validation checks that each result identifies the requested paper, promoter, and property.
- Validation checks that accepted values and candidates remain distinct.
- Validation rejects any result that promotes a candidate marked `INVALID_CANDIDATE` into accepted `values`.
- Validation checks consistency with the property-specific scientific rules in the authoritative contracts.
- A validation failure is a technical failure, not a scientific abstention and not an evaluation result.

### Gold value parsing

The current operational workset is `02-DOCS/data/SUBSET_GOLD.xlsx`, inspected read-only for evaluator-format clarification. It contains one worksheet, `Hoja1`; row 4 contains the headers; rows 5–333 contain 329 records. `Propiedad` identifies the property and `GT_para_referencia` is the operational target column.

The evaluator preserves:

- `gold_value_raw`: the original cell scalar exactly as read, together with whether the cell was stored as text or numeric;
- raw token text after deterministic tokenization;
- `gold_value_set`: an unordered set produced only after property-specific normalization and deduplication.

The parsing sequence is:

```text
gold_value_raw
→ deterministic property-specific tokenization
→ permitted property-specific normalization per token
→ unordered set
→ deduplication of normalized values with raw provenance retained
```

Parsing does not perform matching or scoring.

#### Observed current-workset formats

| Property | Non-empty | Single value | Multiple values | Observed syntax relevant to parsing |
|---|---:|---:|---:|---|
| Caja -10 | 101 | 100 | 1 | Single nucleotide sequence; one cell with two nucleotide sequences separated by the literal delimiter ` + `. |
| Caja -35 | 86 | 86 | 0 | Single nucleotide sequence; one sequence contains an internal line break that is typographic, not a value delimiter. |
| TSS | 98 | 98 | 0 | One signed/unsigned integer scalar per cell; 91 stored as text and 7 as numeric cells. |
| Factor sigma | 44 | 44 | 0 | One sigma label per cell. |

No comma, semicolon, slash, pipe, tab, list syntax, or other multi-value delimiter occurs in `GT_para_referencia`. No empty, `NA`, `N/A`, `ausente_en_este_paper`, `inferido_no_dato`, or other non-positive marker occurs in that target column. `Modalidad_origen` contains only the 133 `texto_explicito` and 196 `imagen_only` positive rows described by the contracts.

#### Minimal deterministic parser

- **Caja -10:** split into multiple raw tokens only when the entire raw text consists of exactly two non-empty nucleotide-sequence tokens separated by the observed literal delimiter ` + `. The one current multi-value cell yields two tokens. A plus sign is not a generic delimiter.
- **Caja -35:** parse the entire cell as one raw token. An internal line break within an otherwise nucleotide-only sequence remains inside that token during parsing and is removed only by the permitted typographic normalization.
- **TSS:** parse one scalar token from either a text or numeric cell when it represents one integer. A leading minus sign is part of the value, not a delimiter. The current workset contains no explicit leading-plus TSS, but the extraction contract's `+1` designation means a plus sign must never be treated generically as a multi-value separator.
- **Factor sigma:** parse the entire cell as one raw token when it is one sigma label. No multi-sigma encoding occurs in the current workset.
- **All properties:** do not infer delimiters from commas, semicolons, slashes, line breaks, generic plus signs, list punctuation, or any syntax not observed and frozen above.
- **Duplicates:** apply the permitted normalization to each token, then collapse equal normalized tokens in `gold_value_set` while retaining every contributing raw token for audit.
- **Empty or non-positive marker:** produce no positive value set. Route the row according to benchmark eligibility rules; do not interpret the marker as a value.
- **Unexpected or ambiguous syntax:** return `PARSE_ERROR / NEEDS_REVIEW`, preserve `gold_value_raw`, and exclude the cell from scoring until explicit adjudication. Never split or normalize it by guessing.

### Leakage-safe benchmark evaluation

- Extraction receives only the permitted document and promoter context.
- A valid prediction is persisted with enough run identity to distinguish the paper, promoter, property, time, and system or prompt version.
- The evaluator cannot access gold fields until persistence of that prediction succeeds.
- After persistence, evaluation compares normalized value sets for each `paper × promoter × property`.
- Evaluation records exact matches, partial set matches, wrong values, misses, and extra values according to the authoritative evaluation contract.
- An abstention on a positive target contributes a miss for value recall without being relabelled as a technical failure.
- Results are reported separately for TSS, caja -10, caja -35, and factor sigma.
- The evaluator may stratify by `texto_explicito` and `imagen_only`; those fields remain invisible to the extractor.
- Development/test partitioning keeps every row from one paper in exactly one split.
- The baseline does not claim complete false-assertion or appropriate-abstention performance from the current positive-only subset.

## Acceptance criteria

- **AC-01 — TXT input:** Given a readable non-empty TXT document, an identified paper, and an identified promoter, when extraction is requested, then it returns one independent scientific result for each of the four target properties.
- **AC-02 — TEI/XML input:** Given a readable, well-formed, non-empty TEI/XML document with the same identity inputs, when extraction is requested, then it returns the same four independent scientific result units.
- **AC-03 — promoter context:** Given a promoter name and an optional identifier or paper-specific synonym, when a result is produced, then the result identifies the requested paper and promoter; the synonym is never treated as a target value.
- **AC-04 — property independence:** Given evidence sufficient for TSS but insufficient for caja -35, when extraction completes, then TSS may be `EXTRACTED` while caja -35 independently has an abstention status.
- **AC-05 — accepted value grounding:** Given an `EXTRACTED` result, when the result is validated, then every accepted value is linked to evidence that jointly identifies its value, property, and promoter in the supplied document.
- **AC-06 — raw and normalized separation:** Given a documentary value whose permitted normalized representation differs, when it is accepted, then both `value_raw` and `value_normalized` are present and distinct, and the transformation is traceable.
- **AC-07 — no forced normalization:** Given a value for which no permitted normalization is supported, when extraction completes, then the system preserves the documentary form and does not invent a normalized equivalent.
- **AC-08 — qualifiers:** Given a paper that labels a value `putative`, `possible`, `predicted`, or `-like`, when the value is accepted, then that qualifier remains attached to the value.
- **AC-09 — multiple values:** Given two or more values that the document unambiguously associates with the same promoter and property, when extraction completes, then each value is represented separately and linked to its supporting evidence.
- **AC-10 — distributed evidence:** Given a conclusion that requires multiple document fragments, when the value is accepted, then all necessary fragments are represented as evidence and linked to that value.
- **AC-11 — ambiguous association:** Given multiple promoters and values whose correspondence cannot be resolved from the document, when extraction completes, then the property is `AMBIGUOUS`, contains zero accepted values, and may retain candidates separately.
- **AC-12 — mention without value:** Given a property mention with no value sufficient for the requested output, when extraction completes, then it returns `INSUFFICIENT_EVIDENCE` with relevant evidence and no accepted value.
- **AC-13 — unavailable modality:** Given a document pointer to a figure whose needed value is absent from the supplied TEI/TXT, when extraction completes, then it may return `UNSUPPORTED_MODALITY` with that pointer and no accepted value.
- **AC-14 — image-origin leakage:** Given a benchmark row whose evaluator-only modality is `imagen_only` and whose TEI/TXT still supports a value, when extraction runs without that modality field, then it may return `EXTRACTED`.
- **AC-15 — external completion forbidden:** Given a missing or incomplete value in the supplied document, when extraction completes, then no accepted value is filled from RegulonDB, a genome, consensus knowledge, model memory, or another external source.
- **AC-16 — technical failure separation:** Given an unreadable, empty, or malformed input that prevents processing, when the run ends, then it reports a technical failure and does not report a scientific abstention.
- **AC-17 — positive validation:** Given a contract-consistent prediction, when validation runs without gold access, then validation accepts it for persistence.
- **AC-18 — negative validation:** Given an `EXTRACTED` result without a value or evidence, or an abstention with an accepted value, when validation runs, then validation rejects it before evaluation.
- **AC-19 — persistence gate:** Given a benchmark case, when prediction persistence has not succeeded, then no gold value, curatorial modality, or evaluation-only field is accessible to the evaluator path for that run.
- **AC-20 — evaluation sequence:** Given a valid persisted prediction, when evaluation starts, then gold access occurs after persistence and the comparison does not alter the persisted prediction.
- **AC-21 — comparison unit:** Given benchmark records, when scoring runs, then every comparison is keyed by one paper, one promoter, and one property.
- **AC-22 — set comparison:** Given multiple normalized gold or predicted values, when evaluation runs, then it distinguishes exact set match, missing correct values, and extra predicted values.
- **AC-23 — per-property report:** Given completed benchmark comparisons, when results are reported, then TSS, caja -10, caja -35, and factor sigma each have separate target and outcome counts.
- **AC-24 — modality strata:** Given evaluator-only modality labels, when results are reported, then total, `texto_explicito`, and `imagen_only` value recall can be reported without those labels having entered extraction.
- **AC-25 — grouped splits:** Given a development/test assignment, when all benchmark rows are inspected, then no paper identifier occurs in both splits.
- **AC-26 — positive-only limitation:** Given results from the current 329-row positive subset, when the evaluation is summarized, then it does not claim a complete documentary false-assertion rate or complete appropriateness of abstention.
- **AC-27 — out-of-scope enforcement:** Given this feature's completed artifact set, when reviewed, then it contains no required behaviour for RAG, embeddings, a vector database, agents, UI, deployment, promoter discovery, complex entity resolution, original-figure reading, PDF-to-GROBID conversion, RegulonDB writes, supplements, or biological sigma equivalences.
- **AC-28 — closed extractor allowlist:** Given any benchmark or non-benchmark extraction request, when its input fields are checked, then extraction proceeds only when every field belongs to `extractor_allowed`.
- **AC-29 — defensive denylist:** Given a field listed in `extractor_forbidden`, or information derived from one, when an extraction request is constructed, then the request is rejected before extraction even if the field has been renamed, nested, joined, retrieved, or embedded.
- **AC-30 — invalid candidate separation:** Given a candidate that violates a scientific or formal rule, when the result is validated, then the candidate may carry rejection reason `INVALID_CANDIDATE`, remains outside accepted `values`, contributes no predicted value to evaluation, and is not reported as a terminal status, scientific abstention, or technical failure.
- **AC-31 — unparseable gold cell:** Given a gold cell whose multiplicity or token boundaries cannot be determined by a frozen rule, when benchmark preparation reaches that cell, then the cell is not split or scored by guessing and is reported for explicit adjudication.
- **AC-32 — observed multiple-value encoding:** Given the observed caja -10 target composed of exactly two nucleotide tokens separated by literal ` + `, when gold parsing runs, then it preserves the full raw cell and both raw tokens and produces a normalized unordered two-value set before scoring.
- **AC-33 — typographic line break:** Given the observed caja -35 target whose one nucleotide sequence contains an internal line break, when gold parsing and normalization run, then parsing produces one raw token and permitted typographic normalization removes the line break without creating multiple values.

## Points to clarify

### A. Open decisions that block PLAN

None. The current workset was inspected read-only and the minimal observed-format parser is fixed above. PLAN is unblocked for this baseline. Any future unobserved encoding returns `PARSE_ERROR / NEEDS_REVIEW` and requires a new approved clarification before entering scoring.

### Resolved in this clarify pass

- **resolved** — Extractor inputs use a closed explicit allowlist plus a defensive denylist. Any unlisted field is rejected, and known curator, gold, or evaluator fields are forbidden directly and indirectly.
- **resolved** — `INVALID_CANDIDATE` is a candidate-level diagnostic rejection reason, not a terminal property status.
- **resolved** — The current gold parser recognizes only the observed property-specific formats, preserves raw values, normalizes after tokenization, compares unordered deduplicated sets, and fails closed on unobserved or ambiguous syntax.

### B. Open decisions that may remain deferred

- **decisión diferida** — The project-wide canonical treatment of `Sin_dato_en_RegulonDB` beyond keeping it outside extraction. The current positive baseline does not require it to produce or compare target values.
- **decisión diferida** — The evaluation use of `Técnica_confirmada_manualmente`. Paper-derived TSS technique may be output as documentary metadata, but this feature does not score it against that curator field.
- **decisión diferida** — The evaluation use of `Año_confirmado`. The feature requires a paper identifier, not curator-confirmed year metadata.
- **decisión diferida** — The concrete ignore-file and local-storage strategy for future gold files. The constitution still forbids committing raw papers, private datasets, and gold datasets; the storage mechanism belongs to a later technical decision before real private data is introduced.
- **decisión diferida** — Final biological sigma equivalences. This feature applies only the typographic normalizations already allowed by the contracts.
- **decisión diferida** — Final adjudication of extremely short caja -10/-35 values. The baseline follows the current rule that length alone does not invalidate or alter scoring.
- **decisión diferida** — Final development/test paper allocation, final frozen gold version, and final bootstrap settings. This feature requires paper-grouped splitting but does not choose the final papers or statistical settings.
- **decisión diferida** — A future curator-annotated evidence benchmark. The baseline requires system evidence but does not claim automatic evidence-passage accuracy.
- **decisión diferida** — A complete false-assertion and appropriate-abstention benchmark using reliable documentary negatives. The current positive subset cannot provide it.

## Authoritative-document inconsistencies and scope tensions

1. **Forbidden-field lists differ.** `extraction-contract.md` omits `Sin_dato_en_RegulonDB`, `Técnica_confirmada_manualmente`, and `Año_confirmado` from its explicit prohibited list. `project-requirements.md` explicitly prohibits `Sin_dato_en_RegulonDB` but does not list the latter two there. `gold-set-contract.md` explicitly prohibits `Sin_dato_en_RegulonDB` and `Técnica_confirmada_manualmente`, while treating `Año_confirmado` as evaluator metadata. The constitution records that no canonical list has been chosen.
2. **The role of `Técnica_confirmada_manualmente` is not uniform.** The gold column table describes it as “No como target” for extractor access, which could be read as allowing non-target context, while the later anti-leakage section prohibits it categorically. This feature does not resolve that conflict.
3. **The wider Part 1 includes an interface and demonstration/deployment expectations, while this first vertical slice excludes UI and deployment.** This is treated as staged scope, not a cancellation of the authoritative Part 1 requirements.
4. **Normalization is both provisionally operational and not finally frozen.** `evaluation-contract.md` defines a usable provisional profile for the current subset, while other root documents keep final per-property normalization and scoring rules open before the final test. This baseline can use only a versioned, predeclared provisional profile and cannot claim that it is the final project protocol.
5. **The current subset supports positive value recovery but not a complete abstention or false-assertion evaluation.** The requirements demand abstention behaviour, while the gold and evaluation contracts state that reliable documentary negatives are not systematically present. This is a limitation of measurable coverage, not a reason to relabel positive rows.

## Clarifications

### 2026-10-06 — Extractor boundary

- **Question:** Should the leakage boundary use a denylist, an allowlist, or both?
- **Decision:** Use a closed explicit `extractor_allowed` allowlist plus a defensive `extractor_forbidden` denylist. Reject every field not allowlisted. Apply the denylist to direct and indirect forms.
- **Why:** The root contracts agree on the minimal extraction inputs but enumerate prohibited fields inconsistently. The conservative interpretation prevents both omission-based and renamed/derived leakage.

### 2026-10-06 — `INVALID_CANDIDATE`

- **Question:** Is `INVALID_CANDIDATE` a terminal scientific status or a rejected-candidate diagnostic?
- **Decision:** It is a candidate-level diagnostic rejection reason in this baseline.
- **Why:** The authoritative contracts call the status provisional and allow it to become a diagnostic flag. No contract requires it to remain terminal. This preserves the distinction among rejected candidates, scientific abstention, and technical failure.

### 2026-10-06 — Multiple-value gold parsing

- **Question:** Can a complete deterministic gold parser be frozen from the available evidence?
- **Decision:** No. Keep this point open and blocking.
- **Why:** The documents provide one observed encoding and explicitly leave the definitive parser open. The current gold file was not available locally for format-only inspection. Generalizing unobserved delimiters would invent a rule.
- **Minimum evidence required:** a format-only inventory of every distinct multi-value encoding in the current gold, without exposing those values to extraction.

### 2026-10-06 — Multiple-value gold parsing follow-up

- **Question:** What encodings actually occur in the current operational target?
- **Evidence:** Read-only inspection of `SUBSET_GOLD.xlsx`, worksheet `Hoja1`, `Propiedad` and `GT_para_referencia`, found 329 non-empty positive targets. Only one caja -10 cell is multi-valued and uses the documented literal ` + ` delimiter. One caja -35 cell contains an internal typographic line break but remains one nucleotide sequence. TSS and factor sigma contain no multi-value cells. No ambiguous target cell or non-positive marker was observed.
- **Decision:** Freeze the minimal property-specific parser in `Gold value parsing`. Preserve raw values; tokenize only the observed caja -10 literal-delimiter form; normalize after tokenization; deduplicate normalized sets; fail closed as `PARSE_ERROR / NEEDS_REVIEW` for every unobserved or ambiguous syntax.
- **Why:** The rule now covers every observed current-workset encoding without generalizing delimiters or mixing parsing with scoring.

## Revisions

- 2026-10-06 — Initial draft created for human review. No `clarify`, `plan`, or implementation phase has run.
- 2026-10-06 — Clarify resolved the extractor boundary and `INVALID_CANDIDATE`; multiple-value gold parsing remains a PLAN blocker pending format-only gold inspection.
- 2026-10-06 — Read-only inspection of the real workset fixed the minimal gold parser. All three clarify blockers are resolved and the spec status is `clarified`.
