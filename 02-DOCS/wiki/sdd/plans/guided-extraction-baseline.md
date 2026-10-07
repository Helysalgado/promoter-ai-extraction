---
type: plan
title: Plan — Guided extraction baseline
description: Structure-level implementation plan for the first leakage-safe guided extraction and evaluation vertical slice.
tags: [sdd, plan, python, extraction, evaluation]
timestamp: 2026-10-07T05:55:00Z
topic: sdd
slug: guided-extraction-baseline
status: approved
---

# Plan — Guided extraction baseline

> Spec: [../specs/guided-extraction-baseline.md](../specs/guided-extraction-baseline.md) · Constitution: [../constitution.md](../constitution.md) · Status: approved
> Last updated: 2026-10-07

## 0. Global constraints

- **Language:** Python `>=3.11`, matching the current `pyproject.toml`.
- **Extraction unit:** exactly one `paper × promoter × property`.
- **Properties:** exactly `TSS`, `Caja -10`, `Caja -35`, and `Factor sigma`, evaluated independently and then grouped by paper/promoter.
- **Allowed extractor inputs:** supplied TEI/XML or TXT document; document format; paper identifier; promoter identifier when available; promoter name; optional paper-specific gene synonym; requested property when execution is per property.
- **Default deny:** every input field not in the closed allowlist is rejected before extraction.
- **Defensive denylist:** `Fila_origen`, `Valor_RegulonDB`, `Sin_dato_en_RegulonDB`, `Modalidad_origen`, `Valor_verificado_manualmente`, `GT_para_referencia`, `Año_confirmado`, `Técnica_confirmada_manualmente`, curator/gold `Evidencia`, `PMID_fuente_alternativa`, split/adjudication fields, evaluation labels or metrics, previous outputs used as targets, and direct or indirect derivations of those fields.
- **No indirect leakage:** gold, curator, and evaluator-only data never enter prompts, retrieval, intermediate extraction objects, backend tools, or extractor logs.
- **Benchmark input source:** extraction requests are supplied explicitly or through a separate allowlisted case manifest; extraction code never opens the gold workbook to construct a request.
- **Document-only completion:** the extractor does not fill a missing value from RegulonDB, a genome, consensus knowledge, model memory, or another source outside the supplied document.
- **Accepted values:** every accepted value identifies the requested promoter and property and references traceable evidence from the supplied document.
- **Value shape:** preserve `value_raw` separately from `value_normalized`; support zero, one, or multiple values; preserve qualifiers and per-value evidence references.
- **Candidates:** `candidate_values` never count as accepted predictions. `INVALID_CANDIDATE` is only a candidate-level rejection reason.
- **Outcome separation:** scientific abstention, rejected candidates, technical failure, gold parse failure, and evaluation result remain distinct types.
- **Scientific statuses:** `EXTRACTED`, `NOT_FOUND`, `INSUFFICIENT_EVIDENCE`, `UNSUPPORTED_MODALITY`, and `AMBIGUOUS`.
- **Persistence gate:** a benchmark prediction is persisted before any evaluator code opens or reads gold data.
- **Evaluation key:** compare at `paper × promoter × property`.
- **Splits:** all rows from one paper share one split; a paper identifier never occurs in both development and test.
- **Current gold parser:** preserve the raw cell; split only the observed Caja -10 form of exactly two nucleotide tokens separated by literal ` + `; treat an internal Caja -35 line break as one sequence; parse one integer TSS and one sigma label per observed cell; return `PARSE_ERROR / NEEDS_REVIEW` for unobserved or ambiguous syntax.
- **Gold scope:** the current parser describes `SUBSET_GOLD.xlsx`; it is not a universal future-gold grammar.
- **Private data:** raw papers, private datasets, gold datasets, credentials, secrets, and generated prediction/evidence files are not committed.
- **Test data:** automated tests use minimal synthetic fixtures and never depend on `SUBSET_GOLD.xlsx`.
- **Explicit exclusions:** no RAG, embeddings, vector database, agents, UI, deployment, promoter discovery, complex entity resolution, direct figure reading, PDF-to-GROBID conversion, RegulonDB writes, unavailable supplements, or biological Rpo/sigma equivalences.

## 1. Context and constraints

- The design must satisfy spec AC-01–AC-04 with two document formats and four independent property attempts grouped in one run.
- Spec AC-05–AC-15 require evidence-grounded accepted values, controlled normalization, qualifiers, multiple values, abstention, and no external completion.
- Spec AC-16–AC-20 require technical-failure separation, output validation, immutable persistence, and the persist-before-gold ordering.
- Spec AC-21–AC-26 require set comparison, TP/FP/FN metrics by property, modality strata when available, paper-grouped splits, and explicit limits of the positive-only workset.
- Spec AC-28–AC-30 require a closed allowlist, defensive denylist, and candidate-level `INVALID_CANDIDATE`.
- Spec AC-31–AC-33 require fail-closed gold parsing, the observed Caja -10 two-value encoding, and the single Caja -35 sequence containing a typographic line break.
- Constitution principles 3–8 make leakage isolation, documentary grounding, abstention/failure separation, persistence ordering, and paper-grouped splits architectural boundaries rather than optional checks.
- The current project has Python `>=3.11`, no dependency lock, no test runner, and no framework. The plan adds only dependencies tied to this slice.
- The real gold is a local evaluator input. It is not packaged, copied, or used by automated tests.
- The extraction engine may use one model-backed call per property, but no provider or model has yet been approved.
- Out-of-scope capabilities remain absent from imports, dependencies, runtime paths, and acceptance tests.

## 2. Architecture

```text
                                    EXTRACTION SIDE

[TEI/XML or TXT]
       |
       v
[DocumentLoader] ---> [LoadedDocument: ordered source-located segments]
       |
       v
[Explicit input / safe case manifest] ---> [ExtractionRequestFactory: allowlist + denylist]
       |
       v
[GuidedExtractionService]
       |  one isolated request per property
       +-----------> [PropertyExtractor port] ---> [ModelBackend adapter: EXTERNAL]
       |                         |
       |                         v
       |               [raw values / candidates / evidence refs]
       |                         |
       v                         v
[Property Normalizers] ---> [OutputValidator]
       |                         |
       +------------+------------+
                    v
          [ExtractionRun: 4 attempts]
                    |
                    v
          [PredictionStore: immutable local JSON]
                    |
                    v
          [PersistedPredictionRef]

                                  EVALUATION SIDE

[PersistedPredictionRef]
          |
          v
[EvaluationService verifies persisted record]
          |
          +---- only after successful verification ----> [GoldLoader]
                                                        |
                                                        v
                                                [GoldParser]
                                                        |
                                                        v
                                      [SetComparator] -> [MetricsReporter]
```

- **DocumentLoader** (internal) — reads TXT or TEI/XML into ordered, stable, source-located document segments without consulting gold.
- **ExtractionRequestFactory** (internal) — creates the only request type accepted by extraction and rejects unknown, forbidden, nested, or derived metadata at the boundary.
- **GuidedExtractionService** (internal) — invokes one independent extraction attempt for each fixed property, collects scientific results or technical failures, and never depends on evaluator modules.
- **PropertyExtractor port** (internal contract) — accepts only the typed extraction request and returns one property result or one technical failure.
- **ModelBackend adapter** (external boundary) — performs one structured extraction call without tools, retrieval, or access to any object beyond the explicit request projection.
- **Property Normalizers** (internal) — apply only contract-approved, property-specific transformations as pure functions.
- **OutputValidator** (internal) — enforces status/value/evidence/candidate consistency and verifies that evidence references resolve to supplied-document segments.
- **PredictionStore** (internal) — writes an immutable, versioned local run record atomically and returns a verifiable persisted reference.
- **EvaluationService** (internal, evaluation-only) — verifies the persisted reference, then and only then coordinates gold loading, parsing, comparison, and reporting.
- **GoldLoader** (internal, evaluation-only) — opens a configured local XLSX in read-only mode only after receiving a verified-persistence capability from the evaluation service.
- **GoldParser** (internal, evaluation-only) — preserves raw cells and creates comparable sets using only the observed current-workset grammar.
- **SetComparator** (internal, evaluation-only) — computes value-level intersections and differences without changing either prediction or gold.
- **MetricsReporter** (internal, evaluation-only) — aggregates TP/FP/FN and derived metrics by property and optional evaluator-only strata.

**Top architectural decision:** use one synchronous Python process with explicit extraction and evaluation boundaries, immutable typed data objects, and local files. This is chosen over services, databases, asynchronous orchestration, or agent frameworks because the slice is local, small, and must make leakage ordering mechanically testable. The critical seam is not a network boundary; it is the type and dependency boundary between `ExtractionRequest` and evaluation-only `GoldRecord`.

## 3. Interfaces and contracts

| Component operation | Input → output | Required invariants and failures |
|---|---|---|
| `DocumentLoader.load` | `DocumentSource → LoadedDocument` | TXT/TEI only; ordered stable segments with available location; unreadable, empty, malformed, unsupported, or oversized input is `TechnicalFailure`; no silent truncation. |
| `ExtractionRequestFactory.create` | raw mapping → immutable `ExtractionRequest` | Exact allowlist only; unknown or recursively forbidden keys fail before backend use; original mapping and arbitrary metadata are discarded. |
| `PropertyExtractor.extract` | one-property request → `PropertyResult | TechnicalFailure` | No evaluator dependency; values and candidates separate; every accepted value has supplied-document evidence. |
| `ModelBackend.generate` | explicit `SafeExtractionInput → RawPropertyPayload | BackendFailure` | No tools, retrieval, web, RegulonDB, hidden metadata, credentials, or chain-of-thought; malformed output is technical failure. |
| `normalize` | property + raw value/details → normalized value or rejected candidate | Pure, deterministic, gold-independent; raw and derivation preserved; no biological sigma equivalence. |
| `OutputValidator.validate` | result + loaded document → validated result or failure | Enforces status/value/candidate consistency, identity match, evidence references, and evidence text in referenced segments. Failure stays technical. |
| `GuidedExtractionService.run` | base request → `ExtractionRun` | Creates four sequential isolated attempts; one result or technical failure per property; no cross-property inference. |
| `PredictionStore.save/load_verified` | run → persisted ref → verified persisted prediction | Schema version 1; immutable run id/time; atomic local JSON write; document hash and model/config fingerprint; load rechecks content hash. |
| `EvaluationService.evaluate` | persisted ref + gold path → `EvaluationReport` | Obtains a verified persisted prediction before invoking `GoldLoader`; never accepts an in-memory prediction as the benchmark source. |
| `GoldLoader.load` | verified-persistence capability + local path → `GoldDataset` | Cannot be reached through the benchmark service without successful verification; opens XLSX read-only/data-only; validates sheet/headers; returns evaluation-only records. |
| `GoldParser.parse` | gold record → parsed set or parse error | Raw cell/type and tokens preserved; clarified grammar only; normalization then deduplication; unknown syntax is `PARSE_ERROR / NEEDS_REVIEW`. |
| `SetComparator.compare` | prediction set + gold set → comparison | TP = intersection; FP = prediction−gold; FN = gold−prediction; exact iff sets equal; partial and extra flags retained. |
| `MetricsReporter.aggregate` | comparisons + optional strata → report | Per-property TP/FP/FN, precision/recall/F1, exact-row accuracy, modality strata, parse/failure/coverage counts, and positive-only limitation. |

`ExtractionRequest` contains only document, document format, paper id, optional promoter id, promoter name, optional paper gene synonym, and one property. Benchmark input comes from explicit arguments or a separate safe manifest. No extraction-side object contains a gold path.

TXT locations use stable line/paragraph ranges and section labels when present. TEI locations use available section, paragraph, table, figure, caption, page, and XML identifiers; unavailable precision stays absent.

The four backend calls are sequential. Four calls do not justify concurrency, and sequential execution keeps logs and failure attribution simple. A per-property technical failure may coexist with valid results in the persisted run but never becomes an accepted value or abstention.

The prediction store uses one local JSON file per run and never stores the full paper. Evidence excerpts remain local and uncommitted. The adapter records model/config fingerprints, never credentials.

Property normalizers remain separate: TSS preserves representation type and allowed anchor/sign derivation; boxes apply only typographic sequence normalization; sigma applies only typographic normalization.

Gold parsing recognizes only: one Caja -10 sequence or exactly two separated by literal ` + `; one Caja -35 sequence with an optional internal typographic line break; one integer TSS; one sigma label. No other character is a delimiter.

Scientific abstention on a positive target yields no predicted values and therefore FN. Gold parse errors are not compared. Technical failures remain separately reported operational outcomes. Reports include parser/normalizer and persistence schema versions.

## 4. Data model and flow

### Entities

- **DocumentSource** — path or supplied content plus declared TXT/TEI format; no gold fields.
- **DocumentSegment** — `segment_id`, text, `source_type`, and available location fields.
- **LoadedDocument** — paper id, format, ordered segments, and document hash.
- **ExtractionRequest** — immutable allowlisted paper/promoter/property input.
- **SafeCaseManifest** — optional extraction-side list containing only allowlisted identities and document references; no target, modality, curator, or evaluator columns.
- **EvidenceItem** — fragment, segment reference, source type, and source location.
- **ExtractedValue** — `value_raw`, `value_normalized`, qualifier, derivation note, property details, and evidence references.
- **RejectedCandidate** — raw candidate, `INVALID_CANDIDATE` reason, relevant evidence, and violated rule; never an accepted value.
- **PropertyResult** — identity, one scientific status, accepted values, rejected/ambiguous candidates, evidence, and abstention reason where applicable.
- **TechnicalFailure** — stage, stable code, safe message, and cause category; never a scientific status.
- **PropertyAttempt** — either one validated `PropertyResult` or one `TechnicalFailure`.
- **ExtractionRun** — run metadata and exactly four property attempts.
- **PersistedPredictionRef** — run id, file path, schema version, and content hash proving persistence.
- **VerifiedPersistedPrediction** — immutable persisted run plus verification capability required before evaluator gold access.
- **GoldRecord** — evaluation-only paper/promoter/property key, raw target cell, storage type, and optional evaluator strata.
- **ParsedGoldValue** — raw cell, raw tokens, normalized unordered set, and parser version.
- **GoldParseError** — raw-preserving `PARSE_ERROR / NEEDS_REVIEW` diagnostic; excluded from comparison.
- **ComparisonResult** — key, TP/FP/FN sets, exact-match flag, partial/extra diagnostics, scientific status, and strata.
- **EvaluationReport** — per-property and per-stratum counts/metrics plus coverage and error counts.

### Primary extraction and evaluation flow

1. The caller supplies a TEI/XML or TXT document and explicit paper/promoter context, directly or from a separately prepared allowlisted case manifest.
2. `DocumentLoader` creates source-located segments or stops with a technical failure.
3. `ExtractionRequestFactory` rejects any non-allowlisted or forbidden data.
4. `GuidedExtractionService` creates four independent property requests.
5. `PropertyExtractor` invokes the backend separately for TSS, Caja -10, Caja -35, and sigma.
6. Pure normalizers transform only permitted documentary forms; invalid candidates remain diagnostics.
7. `OutputValidator` checks each result against the request and loaded document.
8. The service groups four attempts into an `ExtractionRun`.
9. `PredictionStore` atomically persists the immutable run and returns a verified reference.
10. Only now may `EvaluationService` accept the reference and configured local gold path.
11. `GoldLoader` verifies persistence, then opens the workbook and selects matching evaluation keys.
12. `GoldParser` preserves raw cells and produces comparable sets or parse errors.
13. `SetComparator` computes intersections and differences for persisted scientific predictions.
14. `MetricsReporter` aggregates by property and available evaluator-only modality, while reporting parse failures, technical failures, and coverage separately.

### Consistency boundaries

- The request boundary is all-or-nothing: any unexpected input key prevents backend invocation.
- Each property result validates independently.
- The persisted run is immutable and written atomically.
- Gold access is ordered after persisted-reference verification, not merely after an in-memory extraction.
- Parsing precedes normalization; normalization precedes comparison; comparison precedes metrics.
- Evaluation never mutates the persisted prediction or raw gold representation.

### Storage and migration impact

- No database, schema migration, service, or backfill.
- New local prediction files use schema version `1`.
- Test outputs use temporary directories.
- Real gold and generated prediction files stay untracked and outside commits.

## 5. Testing strategy

Use `pytest` as the first configured test runner. It is justified by parametrized normalization matrices, exception assertions, temporary paths, synthetic workbook fixtures, and lightweight spies needed to prove ordering and leakage boundaries. Tests remain deterministic and do not call a real model provider.

### Acceptance-criterion coverage

| Acceptance criteria | Level | What proves them | Fakes / fixtures |
|---|---|---|---|
| AC-01–AC-03 | Unit + integration | TXT and TEI load successfully; stable paper/promoter identity; optional synonym retained only in request context | Synthetic TXT/TEI files |
| AC-04, AC-09 | Unit + integration | Four property attempts remain independent; multiple accepted values remain separate; grouping preserves all attempts | Scripted extractor |
| AC-05, AC-10 | Contract | Every accepted value resolves to one or more supplied-document segments; distributed evidence maps correctly | Synthetic segments |
| AC-06–AC-08 | Unit | Raw/normalized separation, derivation notes, no forced normalization, qualifier preservation | Parametrized values |
| AC-11–AC-15 | Unit | Ambiguous, insufficient, unsupported-modality, image-origin-with-text, and no-external-completion cases produce exact expected shapes | Scripted scientific cases |
| AC-16 | Unit + integration | Unreadable/empty/malformed input and malformed backend payload produce technical failures, never scientific abstentions | Temporary files and failing backend |
| AC-17–AC-18 | Unit | Validator accepts valid results and rejects missing evidence, empty EXTRACTED, accepted invalid candidates, and abstentions with values | Constructed domain objects |
| AC-19–AC-20 | Contract + integration | Gold loader is not called before atomic persistence succeeds; persisted prediction is unchanged by evaluation | Event-log spies, temporary store |
| AC-21–AC-24 | Unit + integration | Keys are paper/promoter/property; set outcomes and per-property/modality reports are correct | Synthetic gold rows |
| AC-25 | Unit | Split validator rejects any paper present in both development and test | Synthetic split assignments |
| AC-26 | Report contract | Report states positive-only limitations and exposes coverage/error counts | Synthetic report input |
| AC-27 | Dependency/scope audit | No disallowed runtime modules, services, or workflows are imported or required | Package/import inspection |
| AC-28–AC-29 | Unit + contract | Unknown keys and every denylisted key are rejected; nested forbidden data and renamed unknown keys never reach prompt/backend input | Sentinel values and capture backend |
| AC-30 | Unit | Invalid candidate remains diagnostic, outside accepted sets and metrics, and distinct from abstention/failure | Constructed candidate |
| AC-31–AC-33 | Unit + integration | Unknown gold syntax fails closed; literal ` + ` parses exactly two Caja -10 values; Caja -35 newline remains one token then normalizes | Synthetic workbook cells |

### Required focused tests

1. **Normalization units**
   - TSS sign/anchor cases, `+1` designation, genomic-coordinate preservation, and missing-anchor non-conversion.
   - Caja uppercase/typographic whitespace/hyphen/line-break normalization without base correction.
   - Sigma typographic normalization without Rpo equivalences.
2. **Gold parser units**
   - single values for all four properties;
   - exactly one observed Caja -10 literal-` + ` form;
   - Caja -35 internal line break as one token;
   - TSS stored as both text and numeric;
   - duplicate normalized tokens retain raw provenance;
   - comma, slash, extra plus tokens, malformed labels, or other unknown shapes return `PARSE_ERROR / NEEDS_REVIEW`.
3. **Scientific-result units**
   - multiple accepted values;
   - `INVALID_CANDIDATE` remains rejected;
   - each abstention status has zero accepted values and the required evidence/reason shape.
4. **Technical-failure units**
   - file, XML, backend, payload, validation, and persistence failures remain outside scientific statuses.
5. **Leakage contract tests**
   - allowlisted request succeeds;
   - each canonical forbidden field fails;
   - unknown aliases and nested forbidden keys fail;
   - a capture backend receives only the explicit safe projection;
   - a sentinel gold target never appears in request, prompt payload, intermediate extraction objects, or extractor logs;
   - extraction succeeds without importing or opening the evaluator gold loader, and no extraction-side object contains a gold path.
6. **Persistence-order contract**
   - failed persistence means gold loader call count stays zero;
   - successful persistence is recorded before the first gold-loader event;
   - evaluator accepts a verified `PersistedPredictionRef`, not an in-memory prediction.
7. **Set evaluation units**
   - exact set, partial recovery, extra value, wrong value, and abstention-on-positive-target yield expected TP/FP/FN sets.
8. **End-to-end integration**
   - synthetic TXT and TEI documents;
   - scripted model backend;
   - four grouped property attempts;
   - real local JSON persistence in a temporary directory;
   - synthetic XLSX generated during the test;
   - parse, compare, and per-property/modality report;
   - assertion that persistence precedes workbook access.

### Real versus fake dependencies

- Real in deterministic tests: document loaders, normalizers, validator, local prediction store, gold parser, comparator, metrics, and XLSX reader over synthetic workbooks.
- Fake: model backend only.
- Not used by tests: private papers and `SUBSET_GOLD.xlsx`.
- Optional provider smoke tests, once selected, are separate, credential-gated, and not part of the deterministic default suite.

## 6. Sequencing and dependencies

1. **Establish package/test foundation** — explicit domain enums/value objects, `pytest`, and synthetic fixture conventions — depends on: none — serial.
2. **Build document and request boundaries** — TXT/TEI segments, allowlist/denylist, immutable request — depends on: #1 — parallelizable with #3 after shared models stabilize.
3. **Build pure normalizers and validator** — property rules, candidates, statuses, evidence checks — depends on: #1 — parallelizable with #2.
4. **Build extractor port and grouped orchestration** — scripted backend first; four independent attempts — depends on: #2 and #3 — serial.
5. **Build immutable prediction persistence** — versioned local JSON and verified reference — depends on: #1; integration depends on #4 — parallelizable at module level.
6. **Build evaluator-only gold loader/parser** — read-only XLSX, current-workset grammar, parse errors — depends on: #1 — parallelizable with #2–#5.
7. **Build set comparison and metrics** — TP/FP/FN, exact rows, strata, coverage/error reporting — depends on: #6 and shared models — parallelizable with backend adapter work.
8. **Prove leakage and ordering contracts** — capture backend, sentinel data, import/type boundary, persist-before-gold event order — depends on: #2, #4, #5, #6 — serial integration gate.
9. **Add full synthetic end-to-end flow** — TXT and TEI through persistence and evaluation — depends on: #4–#8 — serial.
10. **Add one concrete model backend adapter** — depends on: provider/model human decision and #4; does not change domain/evaluator contracts — isolated.
11. **Run the complete deterministic suite and scope audit** — depends on: #1–#9 — final deterministic implementation gate. Include #10 only after the provider/model decision when validating the optional real adapter; the default suite remains provider-independent.

Parallel candidates after domain contracts stabilize:

- document boundary (#2), normalizers/validator (#3), persistence (#5), and gold loader/parser (#6);
- comparison/metrics (#7) and provider adapter (#10) once their respective dependencies are met.

Hard ordering constraints:

- extraction boundary precedes any provider adapter;
- persistence precedes gold access in both production flow and tests;
- tokenization precedes normalization; normalization precedes set comparison;
- deterministic tests precede any real-provider or real-gold controlled run.

## 7. Dependencies, risks, and open decisions

### Proposed dependencies

| Dependency | Scope | Concrete need | Why not a larger alternative |
|---|---|---|---|
| `pytest` | development | Parametrization, `tmp_path`, failure assertions, fixtures, spies, and readable integration tests | Standard `unittest` can work but would add boilerplate around the exact test seams required here. |
| `openpyxl` | runtime/evaluation | Read `SUBSET_GOLD.xlsx` in read-only/data-only mode and create synthetic XLSX fixtures | `pandas`/`numpy` are unnecessary for 329 rows and would blur loading, parsing, and metrics boundaries. |
| `defusedxml` | runtime/input | Parse supplied TEI/XML while rejecting unsafe XML constructs | A web/XML framework is unnecessary; raw standard XML parsing lacks the same fail-closed protections for untrusted documents. |

No web framework, ORM, database driver, dataframe library, agent framework, vector client, or RAG dependency is proposed. The concrete model-provider dependency is deliberately not selected without human approval.

### Risks

| Priority | Risk | Trigger | Impact | Mitigation / retirement evidence |
|---:|---|---|---|---|
| 1 | Leakage through a convenience object or prompt serializer | An implementation forwards a spreadsheet row, arbitrary metadata dict, or generic model object | Invalid benchmark | Typed request with no metadata bag; explicit projection; denylist/unknown-key tests; capture-backend sentinel test. |
| 2 | Gold opened before durable persistence | Benchmark orchestration constructs evaluator state too early or persistence fails | Violates constitution and invalidates prediction independence | Evaluator accepts only verified persisted refs; event-order contract test; gold loader call count remains zero on persistence failure. |
| 3 | Model returns plausible but unsupported values/evidence | Backend output cites absent text or wrong promoter/property | Scientific false assertion | Exact evidence-reference validation; accepted values require supplied-document segments; invalid candidates stay rejected. |
| 4 | Provider/model choice changes structured-output behavior | Selected backend lacks reliable schema output or context capacity | Adapter complexity and unstable extraction | Provider adapter isolated behind port; HUMAN_DECISION_REQUIRED before adapter task; provider contract/smoke test. |
| 5 | Whole document exceeds provider context | Loaded paper cannot be submitted without truncation | Technical failure or hidden loss of evidence | No silent truncation; report `DOCUMENT_TOO_LARGE`; measure representative inputs before considering any later retrieval/chunking feature. |
| 6 | Gold parser overgeneralizes a delimiter | Future or malformed cell resembles current syntax | Silent target corruption | Current-workset-only grammar; raw preservation; unknown syntax fails as `PARSE_ERROR / NEEDS_REVIEW`. |
| 7 | Technical failures disappear from headline metrics | Only successful persisted predictions are evaluated | Inflated apparent performance | Report technical-failure and evaluated-coverage counts alongside value metrics; retain open final-denominator decision. |
| 8 | Positive-only workset overstates abstention/false-assertion quality | Report interpreted beyond supported negatives | Misleading scientific conclusion | Required limitation text; no complete false-assertion claim; later negative benchmark remains out of scope. |
| 9 | Local evidence/prediction files are committed | Output directory falls under version control | Privacy violation | Configurable ignored/local output; pre-commit/status review; tests use temporary directories. |
| 10 | XLSX dependency/environment is broken | `openpyxl` import or workbook smoke test fails in the configured environment | Evaluation path blocked | Pin a compatible version in the project environment and make a synthetic-workbook smoke test the first evaluator task. |

### HUMAN_DECISION_REQUIRED

1. **Concrete model provider/model for the real extractor adapter**
   - Material alternatives: hosted provider SDK, institution-approved endpoint, or local model.
   - Must decide before sequencing step #10 is implemented.
   - Does not block TASKS: all domain, boundary, persistence, evaluator, and scripted-backend tasks are stable.
   - Required answer later: provider, model identifier, credential source, structured-output capability, context limit, and reproducibility settings.

2. **Final benchmark treatment of technical failures in headline denominators**
   - Current plan preserves technical failures separately and reports evaluated coverage.
   - Material alternatives: conditional scientific metrics only, or an additional end-to-end view that treats failed attempts as unrecovered positives.
   - Must decide before the final benchmark protocol is frozen.
   - Does not block TASKS: the data model retains enough information to compute either view without changing extraction or persistence.

### TASKS gate

TASKS is unblocked. The architecture, interfaces, test seams, sequence, and fail-closed behavior are concrete. The two human decisions above become explicit decision checkpoints in the future task breakdown; neither changes the stable core contracts.

### Isolation

Implementation is already isolated on `feat/guided-extraction-baseline`. A separate worktree is optional unless another session will modify the same branch concurrently.

## Tasks
<!-- generated by tasks on 2026-10-07; IDs are stable, do not renumber -->

### Increment 1 — Contracts, test foundation, and private-data guard

| ID | [P] | Task | Done-check | Depends-on | Trace |
|---|---|---|---|---|---|
| T001 |  | Protect the real gold and local prediction outputs with narrow Git ignore rules (`.gitignore`) | `git check-ignore -q 02-DOCS/data/SUBSET_GOLD.xlsx` exits 0; `git check-ignore -q tests/fixtures/synthetic_gold.xlsx` exits non-zero; `git status --short` does not list the real workbook | — | constitution principle 9; plan §0 Private data |
| T002 |  | Configure the Python package and deterministic test gate (`pyproject.toml`, `src/`, `tests/`, `scripts/verify.sh`) | `python -c "import pytest, openpyxl, defusedxml"` exits 0; `python -m pytest --collect-only` exits 0; `./scripts/verify.sh` invokes the test suite | T001 | plan §5; spec AC-27 |
| T003 |  | Write failing domain-contract tests for properties, statuses, values, evidence, candidates, attempts, and failures (`tests/unit/test_models.py`) | `python -m pytest tests/unit/test_models.py` fails for missing domain contracts, not import/configuration errors | T002 | spec §Behaviour; AC-03–AC-04, AC-30 |
| T004 |  | Implement immutable domain contracts and enums (`src/promoter_ai_extraction/models.py`) | `python -m pytest tests/unit/test_models.py` passes | T003 | spec §Behaviour; AC-03–AC-04, AC-30 |

### Increment 2 — TXT and TEI/XML input

| ID | [P] | Task | Done-check | Depends-on | Trace |
|---|---|---|---|---|---|
| T005 | [P] | Write failing TXT loader tests for segments, locations, empty files, decoding failures, and document hash (`tests/unit/test_txt_loader.py`) | `python -m pytest tests/unit/test_txt_loader.py` fails for missing TXT behavior | T004 | spec AC-01, AC-03, AC-16 |
| T006 |  | Implement the TXT document loader (`src/promoter_ai_extraction/documents.py`) | `python -m pytest tests/unit/test_txt_loader.py` passes | T005 | spec AC-01, AC-03, AC-16 |
| T007 |  | Write failing TEI loader tests for sections, captions, tables, malformed XML, unsafe XML, and missing location precision (`tests/unit/test_tei_loader.py`) | `python -m pytest tests/unit/test_tei_loader.py` fails for missing TEI behavior | T006 | spec AC-02, AC-10, AC-13, AC-16 |
| T008 |  | Implement the fail-closed TEI/XML loader with `defusedxml` (`src/promoter_ai_extraction/documents.py`) | `python -m pytest tests/unit/test_tei_loader.py tests/unit/test_txt_loader.py` passes | T007 | spec AC-02, AC-10, AC-13, AC-16 |

### Increment 3 — Safe extractor boundary

| ID | [P] | Task | Done-check | Depends-on | Trace |
|---|---|---|---|---|---|
| T009 | [P] | Write failing allowlist/denylist tests, including unknown, nested, and renamed forbidden fields (`tests/unit/test_boundary.py`) | `python -m pytest tests/unit/test_boundary.py` fails for missing boundary rejection behavior | T004 | spec AC-28–AC-29 |
| T010 |  | Implement immutable request construction and safe case-manifest projection (`src/promoter_ai_extraction/boundary.py`) | `python -m pytest tests/unit/test_boundary.py` passes; capture assertion shows no arbitrary metadata or gold path | T009 | spec §Inputs; AC-28–AC-29 |

### Increment 4 — Normalization and scientific validation

| ID | [P] | Task | Done-check | Depends-on | Trace |
|---|---|---|---|---|---|
| T011 | [P] | Write failing property-normalization tests for TSS, boxes, sigma, raw preservation, and forbidden inference (`tests/unit/test_normalization.py`) | `python -m pytest tests/unit/test_normalization.py` fails for missing normalizers | T004 | spec AC-06–AC-08, AC-15, AC-33 |
| T012 |  | Implement pure property-specific normalizers (`src/promoter_ai_extraction/normalization.py`) | `python -m pytest tests/unit/test_normalization.py` passes | T011 | spec AC-06–AC-08, AC-15, AC-33 |
| T013 |  | Write failing validator tests for evidence, identities, abstention, multiple values, and `INVALID_CANDIDATE` separation (`tests/unit/test_validation.py`) | `python -m pytest tests/unit/test_validation.py` fails for missing validation behavior | T004, T012 | spec AC-05, AC-09–AC-13, AC-17–AC-18, AC-30 |
| T014 |  | Implement output validation against request and document segments (`src/promoter_ai_extraction/validation.py`) | `python -m pytest tests/unit/test_validation.py` passes | T013 | spec AC-05, AC-09–AC-13, AC-17–AC-18, AC-30 |

### Increment 5 — Extractor ports and deterministic orchestration

| ID | [P] | Task | Done-check | Depends-on | Trace |
|---|---|---|---|---|---|
| T015 | [P] | Write extractor/backend contract tests with a deterministic scripted backend (`tests/contract/test_extractor_port.py`) | `python -m pytest tests/contract/test_extractor_port.py` fails for missing port and safe payload behavior | T010, T014 | spec AC-04–AC-05, AC-14–AC-16 |
| T016 |  | Implement `PropertyExtractor`, `ModelBackend`, safe payload, and scripted backend contracts (`src/promoter_ai_extraction/extraction.py`, `tests/fakes.py`) | `python -m pytest tests/contract/test_extractor_port.py` passes | T015 | spec AC-04–AC-05, AC-14–AC-16 |
| T017 |  | Write failing four-property orchestration tests for independence, grouping, multiple values, abstention, and per-property technical failure (`tests/unit/test_extraction_service.py`) | `python -m pytest tests/unit/test_extraction_service.py` fails for missing orchestration | T008, T010, T014, T016 | spec AC-04, AC-09, AC-11–AC-16 |
| T018 |  | Implement sequential guided extraction orchestration (`src/promoter_ai_extraction/extraction.py`) | `python -m pytest tests/unit/test_extraction_service.py tests/contract/test_extractor_port.py` passes | T017 | spec AC-04, AC-09, AC-11–AC-16 |

### Increment 6 — Immutable prediction persistence

| ID | [P] | Task | Done-check | Depends-on | Trace |
|---|---|---|---|---|---|
| T019 | [P] | Write failing schema-version and round-trip serialization tests for extraction runs (`tests/unit/test_prediction_schema.py`) | `python -m pytest tests/unit/test_prediction_schema.py` fails for missing schema/serialization | T004 | spec AC-19–AC-20; plan §4 |
| T020 |  | Implement prediction schema version 1 and deterministic serialization (`src/promoter_ai_extraction/persistence.py`) | `python -m pytest tests/unit/test_prediction_schema.py` passes | T019 | spec AC-19–AC-20; plan §4 |
| T021 |  | Write failing atomic-write, immutability, hash-verification, and corruption tests (`tests/unit/test_prediction_store.py`) | `python -m pytest tests/unit/test_prediction_store.py` fails for missing persistence guarantees | T020 | constitution principle 7; spec AC-19–AC-20 |
| T022 |  | Implement local JSON `PredictionStore` and verified-persistence capability (`src/promoter_ai_extraction/persistence.py`) | `python -m pytest tests/unit/test_prediction_store.py tests/unit/test_prediction_schema.py` passes | T021 | constitution principle 7; spec AC-19–AC-20 |

### Increment 7 — Evaluator-only gold loading and parsing

| ID | [P] | Task | Done-check | Depends-on | Trace |
|---|---|---|---|---|---|
| T023 | [P] | Write failing synthetic-XLSX gold-loader tests for read-only access, headers, keys, strata, and missing/corrupt workbooks (`tests/unit/evaluation/test_gold_loader.py`) | `python -m pytest tests/unit/evaluation/test_gold_loader.py` fails for missing loader behavior and does not read `SUBSET_GOLD.xlsx` | T002, T004 | spec AC-21, AC-24–AC-25 |
| T024 |  | Implement evaluator-only XLSX `GoldLoader` (`src/promoter_ai_extraction/evaluation/gold_loader.py`) | `python -m pytest tests/unit/evaluation/test_gold_loader.py` passes; fixture paths are all under `tmp_path` | T023 | spec AC-21, AC-24–AC-25 |
| T025 |  | Write failing gold-parser tests for raw preservation, single values, literal ` + `, Caja -35 line break, numeric/text TSS, sigma, deduplication, and parse errors (`tests/unit/evaluation/test_gold_parser.py`) | `python -m pytest tests/unit/evaluation/test_gold_parser.py` fails for missing parser rules | T012, T024 | spec AC-22, AC-31–AC-33 |
| T026 |  | Implement the current-workset `GoldParser` and `PARSE_ERROR / NEEDS_REVIEW` (`src/promoter_ai_extraction/evaluation/gold_parser.py`) | `python -m pytest tests/unit/evaluation/test_gold_parser.py` passes | T025 | spec AC-22, AC-31–AC-33 |

### Increment 8 — Set comparison, metrics, and split validation

| ID | [P] | Task | Done-check | Depends-on | Trace |
|---|---|---|---|---|---|
| T027 | [P] | Write failing set-comparison tests for exact, partial, extra, wrong, miss, and abstention outcomes (`tests/unit/evaluation/test_comparison.py`) | `python -m pytest tests/unit/evaluation/test_comparison.py` fails for missing TP/FP/FN behavior | T004, T026 | spec AC-21–AC-22 |
| T028 |  | Implement normalized-set comparison and row diagnostics (`src/promoter_ai_extraction/evaluation/comparison.py`) | `python -m pytest tests/unit/evaluation/test_comparison.py` passes | T027 | spec AC-21–AC-22 |
| T029 |  | Write failing metrics and split tests for precision, recall, F1, exact-row accuracy, per-property/modality strata, coverage, failures, and paper grouping (`tests/unit/evaluation/test_metrics.py`) | `python -m pytest tests/unit/evaluation/test_metrics.py` fails for missing aggregation/split behavior | T028 | spec AC-23–AC-26 |
| T030 |  | Implement metrics reporting and paper-grouped split validation (`src/promoter_ai_extraction/evaluation/metrics.py`) | `python -m pytest tests/unit/evaluation/test_metrics.py` passes | T029 | spec AC-23–AC-26 |
| T031 |  | **HUMAN_DECISION_REQUIRED — choose final headline treatment of technical failures** (`02-DOCS/wiki/sdd/decisions.md`) | Decision log states whether final reporting adds an end-to-end denominator view; existing separate failure/coverage metrics remain unchanged | T030 | plan §7 HUMAN_DECISION_REQUIRED; spec AC-16, AC-26 |

### Increment 9 — Leakage ordering and synthetic end-to-end integration

| ID | [P] | Task | Done-check | Depends-on | Trace |
|---|---|---|---|---|---|
| T032 |  | Write failing contract tests proving gold isolation and persist-before-gold ordering (`tests/contract/test_leakage_ordering.py`) | `python -m pytest tests/contract/test_leakage_ordering.py` fails for missing verified-reference gate; failed persistence records zero gold-loader calls | T010, T018, T022, T024 | constitution principles 3 and 7; spec AC-19–AC-20, AC-28–AC-29 |
| T033 |  | Implement `EvaluationService` with verified-persistence capability (`src/promoter_ai_extraction/evaluation/service.py`) | `python -m pytest tests/contract/test_leakage_ordering.py` passes; evaluator rejects direct in-memory predictions | T032, T026, T028, T030 | constitution principles 3 and 7; spec AC-19–AC-24 |
| T034 |  | Write failing parametrized TXT/TEI synthetic end-to-end tests (`tests/integration/test_guided_baseline.py`) | `python -m pytest tests/integration/test_guided_baseline.py` fails for missing application wiring, not fixture/configuration errors | T008, T018, T022, T033 | spec AC-01–AC-24, AC-28–AC-33 |
| T035 |  | Wire synthetic extraction → validation → persistence → evaluation flow (`src/promoter_ai_extraction/application.py`) | `python -m pytest tests/integration/test_guided_baseline.py` passes for both TXT and TEI with a scripted backend and synthetic XLSX | T034 | spec AC-01–AC-24, AC-28–AC-33 |

### Increment 10 — Real model backend without blocking deterministic work

| ID | [P] | Task | Done-check | Depends-on | Trace |
|---|---|---|---|---|---|
| T036 |  | **HUMAN_DECISION_REQUIRED — select provider and model for the real backend** (`02-DOCS/wiki/sdd/decisions.md`, configuration documentation) | Decision log records provider, model id, credential source, structured-output mode, context limit, and reproducibility settings | T016 | plan §7 HUMAN_DECISION_REQUIRED; spec §Goals |
| T037 |  | Write provider-adapter contract tests without live credentials (`tests/contract/test_real_backend_adapter.py`) | `python -m pytest tests/contract/test_real_backend_adapter.py` fails for the selected adapter's missing mapping/error behavior and performs no network call | T035, T036 | spec AC-05–AC-16, AC-28–AC-30 |
| T038 |  | Implement the selected provider adapter and safe prompt projection (`src/promoter_ai_extraction/backends/`) | `python -m pytest tests/contract/test_real_backend_adapter.py tests/contract/test_extractor_port.py` passes; captured payload contains only allowlisted request fields | T037 | spec AC-05–AC-16, AC-28–AC-30 |

### Increment 11 — Controlled baseline execution

| ID | [P] | Task | Done-check | Depends-on | Trace |
|---|---|---|---|---|---|
| T039 |  | Approve a safe development case manifest and local document directory without target columns | Manifest schema validation passes; field audit contains only allowlisted identities/document references; manifest and papers remain untracked | T010 | spec §Inputs; AC-28–AC-29 |
| T040 |  | Write failing local-runner tests for safe manifest input, immutable predictions, evaluator sequencing, and untracked outputs (`tests/integration/test_baseline_runner.py`) | `python -m pytest tests/integration/test_baseline_runner.py` fails for missing runner behavior using only synthetic inputs | T035 | spec AC-19–AC-26, AC-28–AC-29 |
| T041 |  | Implement the local baseline runner without UI or service framework (`src/promoter_ai_extraction/baseline.py`) | `python -m pytest tests/integration/test_baseline_runner.py` passes; runner accepts safe manifest/documents/gold/output paths and opens gold only after persistence | T040 | spec AC-19–AC-26, AC-28–AC-29 |
| T042 |  | Execute the controlled development baseline with the selected backend and real local evaluator inputs | `python -m promoter_ai_extraction.baseline --manifest "$SAFE_CASE_MANIFEST" --documents "$DOCUMENT_ROOT" --gold "$GOLD_PATH" --predictions "$PREDICTION_DIR" --report "$REPORT_PATH"` exits 0; report includes per-property metrics, strata, coverage/failures, parser/model versions; `git status --short` shows no private/generated file staged | T031, T038, T039, T041 | spec §Goals; AC-19–AC-26 |

### Increment 12 — Deterministic completion gate

| ID | [P] | Task | Done-check | Depends-on | Trace |
|---|---|---|---|---|---|
| T043 |  | Run the deterministic suite and explicit scope/leakage audit (`scripts/verify.sh`, dependency/import audit) | `./scripts/verify.sh` exits 0; `python -m pytest` passes without network, private papers, or `SUBSET_GOLD.xlsx`; audit finds no FastAPI, RAG, agent, frontend, deployment, vector, or database dependency | T035, T041 | spec AC-01–AC-33 |
| T044 |  | Record implementation evidence and remaining limitations in the SDD progress artifact (`02-DOCS/wiki/sdd/progress/guided-extraction-baseline.md`) | Progress artifact maps T001–T043 to commands/results, records T042 separately as controlled local evidence, and contains no private values or paths | T042, T043 | spec §Problem, §Acceptance; constitution Definition of Done |

### Critical implementation order

```text
T001 → T002 → T003 → T004
→ (T005–T008, T009–T010, T011–T014)
→ T015–T018
→ T019–T022
→ T023–T030
→ T032–T035
→ T040–T041
→ T043
```

`T036–T038` and `T039` can be resolved after deterministic core work starts. They gate the controlled real baseline (`T042`), not the preceding implementation.

### Interfaces for context-isolated implementation

**T004 — Interfaces**
- Produces: immutable enums/value objects for four properties, five scientific statuses, evidence, values, rejected candidates, property attempts, and technical failures.
- Consumed by: T006–T043.

**T010 — Interfaces**
- Produces: `ExtractionRequestFactory.create(mapping) -> ExtractionRequest | BoundaryViolation`; immutable request has no metadata bag or gold path.
- Consumed by: T015–T018, T032–T042.

**T016 — Interfaces**
- Produces: `ModelBackend.generate(SafeExtractionInput) -> RawPropertyPayload | BackendFailure`; `PropertyExtractor.extract(ExtractionRequest) -> PropertyResult | TechnicalFailure`.
- Consumed by: T017–T018, T034–T038.

**T022 — Interfaces**
- Produces: `save(ExtractionRun) -> PersistedPredictionRef`; `load_verified(ref) -> VerifiedPersistedPrediction | PersistenceFailure`.
- Consumed by: T032–T042.

**T024/T026 — Interfaces**
- Produces: evaluator-only `GoldRecord`; `GoldParser.parse(record) -> ParsedGoldValue | GoldParseError`.
- Consumed by: T027–T035, T040–T042.

**T028/T030 — Interfaces**
- Produces: TP/FP/FN set comparison and per-property/stratum `EvaluationReport` with separate parse/failure/coverage counts.
- Consumed by: T033–T044.

**T033 — Interfaces**
- Produces: `EvaluationService.evaluate(PersistedPredictionRef, gold_path) -> EvaluationReport`; gold access requires verified persistence and rejects in-memory predictions.
- Consumed by: T034–T044.

**T038 — Interfaces**
- Produces: selected provider adapter implementing the T016 backend port with only the safe input projection.
- Consumed by: T042.

**T041 — Interfaces**
- Produces: local runner accepting explicit safe-manifest, document-root, gold-path, prediction-output, and report-output arguments; no UI/API.
- Consumed by: T042–T043.

## Review workload forecast

| Dimension | Forecast | Why |
|---|---|---|
| Estimated changed lines | 1,500–2,500 | Domain contracts, two loaders, boundary, extraction, persistence, evaluator, tests, and local runner |
| Files / areas | 25–35 files across 8–10 areas | Small modules plus paired unit/contract/integration tests |
| Review risk | high | Scientific correctness, leakage boundary, persistence ordering, and evaluator metrics |
| Suggested delivery | `ask-on-risk`, reviewed in functional increments | Exceeds the configured 400-line / 12-file review budget; checkpoints should follow increments 1–5, 6–9, and 10–12 |

Implementation remains on `feat/guided-extraction-baseline`. Do not fan out tasks that share `models.py`, `pyproject.toml`, or integration fixtures. Parallel markers are limited to disjoint failing-test files and modules.

## Post-baseline course milestones

These are future project deliverables, not tasks of `guided-extraction-baseline`:

- FastAPI service;
- RAG;
- at least one agent;
- end-to-end and regression evals beyond this baseline;
- deployment/demo;
- recommended frontend;
- recommended CI/CD.
