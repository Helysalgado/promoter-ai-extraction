# SDD clarify — guided-extraction-baseline

## Metadata

- Date: 2026-10-06
- Branch: `feat/guided-extraction-baseline`
- Phase: `SDD → clarify`
- Scope: only the three PLAN blockers recorded by `specify`
- Phase result: complete
- PLAN unlocked: yes

## Objective

Clarify:

1. the leakage-safe extractor input boundary;
2. the role of `INVALID_CANDIDATE`;
3. deterministic parsing of multiple values in the current gold.

The six authoritative root requirements were used as sources and were not modified.

## Sources

- `project-overview.md`
- `project-requirements.md`
- `extraction-contract.md`
- `gold-set-contract.md`
- `evaluation-contract.md`
- `ux-requirements.md`
- `02-DOCS/wiki/sdd/constitution.md`
- `02-DOCS/wiki/sdd/decisions.md`
- `02-DOCS/wiki/sdd/specs/guided-extraction-baseline.md`

## Clarification results

| Point | Decision | Justification | Status |
|---|---|---|---|
| Extractor boundary | Closed `extractor_allowed` allowlist plus defensive `extractor_forbidden` denylist. Fields must pass both controls; unlisted and indirect forms are rejected. | The contracts agree on the minimal required input but list forbidden fields inconsistently. The conservative interpretation prevents leakage by omission or transformation. | RESOLVED |
| `INVALID_CANDIDATE` | Candidate-level diagnostic rejection reason, not terminal property status. It is not an accepted prediction, scientific abstention, or technical failure. | The contracts call it provisional and permit conversion to a diagnostic flag. No authoritative contract requires terminal-status semantics. | RESOLVED |
| Multiple-value gold parsing | Minimal property-specific parser frozen for every encoding observed in `SUBSET_GOLD.xlsx`; unobserved or ambiguous syntax fails closed as `PARSE_ERROR / NEEDS_REVIEW`. | Read-only inspection found one literal ` + ` two-value caja -10 cell, one single caja -35 sequence with a typographic line break, and no other multiple-value syntax. | RESOLVED |

## Canonical extractor boundary for this feature

### `extractor_allowed`

- supplied TEI/XML or TXT document;
- document format;
- paper identifier;
- promoter identifier, when available;
- promoter name;
- optional paper-specific gene synonym;
- requested property when execution is per property.

### `extractor_forbidden`

- `Fila_origen`;
- `Valor_RegulonDB`;
- `Sin_dato_en_RegulonDB`;
- `Modalidad_origen`;
- `Valor_verificado_manualmente`;
- `GT_para_referencia`;
- `Año_confirmado`;
- `Técnica_confirmada_manualmente`;
- curator/gold `Evidencia`;
- `PMID_fuente_alternativa`;
- split, benchmark-inclusion, and adjudication fields;
- evaluation labels, TP/FP/FN, match classes, scores, and metrics;
- previous outputs used as expected answers;
- any expected answer or direct/indirect derivation of a forbidden field.

The policy is default-deny: absence from the allowlist is sufficient to reject a field.

## Field-role interpretation

- `gold_only`: target values and gold provenance needed only after prediction persistence.
- `curator_only`: manual review results or curator evidence.
- `evaluator_only`: split control, modality stratification, adjudication, labels, and metrics.

When one field has more than one role, all applicable restrictions remain.

## `INVALID_CANDIDATE` semantics

- It is attached only to a rejected candidate.
- The candidate remains in `candidate_values`, not accepted `values`.
- It contributes no predicted value to evaluation.
- It records the scientific/formal rejection reason and relevant evidence when available.
- Candidate rejection does not itself choose the property's terminal status.
- The property independently receives `EXTRACTED`, `NOT_FOUND`, `INSUFFICIENT_EVIDENCE`, `UNSUPPORTED_MODALITY`, or `AMBIGUOUS` as justified by the remaining evidence.
- It is not a technical failure.

### Multiple-value gold inventory

Source inspected read-only:

```text
02-DOCS/data/SUBSET_GOLD.xlsx
```

- Worksheet: `Hoja1`
- Header row: 4
- Data rows: 5–333
- Property column: `Propiedad`
- Operational target: `GT_para_referencia`
- Records: 329
- Workbook SHA-256 before inspection: `4c7311144d76cf9c4f3123d8105f4f1d111f6f7f72e494a0f84fccfa662b63af`
- Workbook SHA-256 after inspection: `4c7311144d76cf9c4f3123d8105f4f1d111f6f7f72e494a0f84fccfa662b63af` (unchanged)

| Propiedad | Patrón observado | Nº casos | Parser determinista |
|---|---|---:|---|
| Caja -10 | Una secuencia nucleotídica | 100 | sí |
| Caja -10 | Exactamente dos secuencias nucleotídicas separadas por literal ` + ` | 1 | sí |
| Caja -35 | Una secuencia nucleotídica en una línea | 85 | sí |
| Caja -35 | Una sola secuencia nucleotídica con salto de línea tipográfico interno | 1 | sí |
| TSS | Un entero por celda: 91 almacenados como texto y 7 como número | 98 | sí |
| Factor sigma | Una etiqueta sigma por celda | 44 | sí |

Totals by property:

| Propiedad | No vacíos | Un valor | Múltiples valores |
|---|---:|---:|---:|
| Caja -10 | 101 | 100 | 1 |
| Caja -35 | 86 | 86 | 0 |
| TSS | 98 | 98 | 0 |
| Factor sigma | 44 | 44 | 0 |

Observed separator and marker findings:

- Literal ` + ` occurs once and separates exactly two caja -10 sequences.
- One caja -35 cell contains a line break inside one nucleotide sequence. It is not a multiple-value separator.
- TSS includes 92 negative values; the minus sign is part of the value, not a separator. Six TSS values are unsigned or zero. No explicit leading-plus TSS occurs in this workset.
- No comma, semicolon, slash, pipe, tab, list syntax, or other multi-value delimiter occurs in the target.
- `GT_para_referencia` has no empty cells and no `NA`, `N/A`, `ausente_en_este_paper`, `inferido_no_dato`, or other non-positive marker.
- `Modalidad_origen` contains 133 `texto_explicito` and 196 `imagen_only` positive rows.
- No ambiguous target cell was found.

Minimal parsing rule:

1. Preserve the complete original cell and its text/numeric storage type as `gold_value_raw`.
2. Preserve every raw token produced by deterministic tokenization.
3. For caja -10, split only the observed form of exactly two non-empty nucleotide tokens separated by literal ` + `.
4. For caja -35, TSS, and factor sigma, parse the observed cell as one token. The caja -35 line break remains within that token until normalization.
5. Apply only the permitted property-specific normalization after tokenization.
6. Produce an unordered `gold_value_set`.
7. Deduplicate normalized values while retaining every raw token as provenance.
8. For unobserved, malformed, or ambiguous syntax, return `PARSE_ERROR / NEEDS_REVIEW`; do not score or guess.

Parsing remains separate from matching and scoring.

## Spec changes

Updated the same artifact:

```text
02-DOCS/wiki/sdd/specs/guided-extraction-baseline.md
```

Changes:

- formalized `extractor_allowed`;
- formalized `extractor_forbidden`;
- classified field roles;
- made `INVALID_CANDIDATE` diagnostic;
- added validation and acceptance criteria for both decisions;
- documented the complete current-workset encoding inventory;
- fixed the minimal evaluator parser and fail-closed rule;
- added a dated clarification log.

The spec is now `clarified`. No PLAN blocker remains.

## Decision-log changes

`02-DOCS/wiki/sdd/decisions.md` records the three restrictions fixed in this phase:

1. closed allowlist plus defensive denylist;
2. diagnostic semantics for `INVALID_CANDIDATE`;
3. the minimal parser for observed current-workset encodings.

## Files created or modified in this phase

Created:

- `02-DOCS/process/2026-10-06-guided-extraction-baseline-clarify.md`

Modified:

- `02-DOCS/wiki/sdd/specs/guided-extraction-baseline.md`
- `02-DOCS/wiki/sdd/decisions.md`

Existing uncommitted `specify` changes remain in the working tree.

## Git and workflow constraints

- No commit.
- No push.
- No pull request.
- No root requirement document modified.
- The supplied untracked workbook `02-DOCS/data/SUBSET_GOLD.xlsx` remains byte-for-byte unchanged and must not be committed.
- No `plan`, `tasks`, `analyze`, or `implement` phase executed.

## Result envelope

```json
{
  "status": "complete",
  "executive_summary": "All three clarify points are resolved. Read-only inspection of the real workset fixed a minimal property-specific gold parser with fail-closed handling for unobserved syntax.",
  "artifact": "02-DOCS/wiki/sdd/specs/guided-extraction-baseline.md",
  "next_recommended": "plan",
  "risk": "medium",
  "model": {
    "tier": "balanced",
    "resolved": "session model",
    "routing": "off"
  },
  "skill_resolution": {
    "used": ["clarify", "orient"],
    "missing": [],
    "fallback": [],
    "compact_rules": [
      "Resolve only the three approved blockers.",
      "Choose the conservative leakage interpretation.",
      "Do not invent unobserved gold delimiters.",
      "Bake decisions into the existing spec."
    ]
  },
  "evidence": [
    "allowlist and denylist added to the spec",
    "INVALID_CANDIDATE semantics added to the spec",
    "real workset inspected read-only",
    "329 target encodings inventoried without printing the dataset",
    "minimal parser and fail-closed rule added to the spec",
    "no clarify blocker remains"
  ]
}
```

## Next recommended step

Stop after clarify for human review. PLAN is unlocked but has not started.
