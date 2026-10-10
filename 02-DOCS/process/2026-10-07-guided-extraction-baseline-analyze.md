---
type: analysis
title: Analyze — Guided extraction baseline
description: Pre-implementation consistency gate across requirements, specification, plan, and tasks.
tags: [sdd, analysis, extraction, evaluation]
timestamp: 2026-10-07T00:11:00-06:00
topic: sdd
slug: guided-extraction-baseline
status: pass
---

# guided-extraction-baseline — SDD ANALYZE

**GATE: PASS** — 0 BLOCKER, 2 IMPORTANT corregidos, 0 MINOR.

- Fecha: 2026-10-07
- Rama: `feat/guided-extraction-baseline`
- Fase: `SDD → analyze`
- Resultado: `PASS`
- IMPLEMENT desbloqueado por consistencia: **SÍ**
- Workbook real abierto durante ANALYZE: **NO**

## Objetivo

Comprobar la consistencia completa:

```text
requirements → spec → plan → tasks
```

El gate revisó cobertura, alcance, contradicciones, duplicaciones, ambigüedades, cumplimiento constitucional, aislamiento anti-leakage, orden persist-before-gold y suficiencia de los contratos para implementadores aislados.

## Fuentes revisadas

- `project-overview.md`
- `project-requirements.md`
- `extraction-contract.md`
- `gold-set-contract.md`
- `evaluation-contract.md`
- `ux-requirements.md`
- `02-DOCS/wiki/sdd/constitution.md`
- `02-DOCS/wiki/sdd/decisions.md`
- `02-DOCS/wiki/sdd/specs/guided-extraction-baseline.md`
- `02-DOCS/wiki/sdd/plans/guided-extraction-baseline.md`, incluido su bloque `## Tasks`

Los seis documentos raíz se leyeron, pero no se modificaron.

## Mapa de cobertura

| Criterio | Requisito resumido | Cobertura del plan | Tareas | Estado |
|---|---|---|---|---|
| AC-01 | Input TXT y cuatro resultados | §§2–5, flujo §4 | T005–T006, T017–T018, T034–T035 | cubierto |
| AC-02 | Input TEI/XML y cuatro resultados | §§2–5, flujo §4 | T007–T008, T017–T018, T034–T035 | cubierto |
| AC-03 | Identidad de paper/promotor y sinónimo opcional | §§0, 3–4 | T003–T004, T009–T010, T013–T014, T034–T035 | cubierto |
| AC-04 | Independencia por propiedad | §§0, 2–5 | T003–T004, T015–T018, T034–T035 | cubierto |
| AC-05 | Grounding de todo valor aceptado | §§0, 2–5 | T013–T018, T034–T035 | cubierto |
| AC-06 | Separación raw/normalized | §§0, 3–5 | T011–T014, T034–T035 | cubierto |
| AC-07 | No forzar normalización | §§0, 3, 5 | T011–T014, T034–T035 | cubierto |
| AC-08 | Preservar qualifiers | §§0, 3–5 | T011–T014, T034–T035 | cubierto |
| AC-09 | Múltiples valores | §§0, 3–5 | T013–T018, T034–T035 | cubierto |
| AC-10 | Evidencia distribuida | §§2–5 | T007–T008, T013–T014, T034–T035 | cubierto |
| AC-11 | Asociación ambigua | §§0, 3–5 | T013–T018, T034–T035 | cubierto |
| AC-12 | Mención sin valor | §§0, 3–5 | T013–T018, T034–T035 | cubierto |
| AC-13 | Modalidad no disponible | §§2–5 | T007–T008, T013–T018, T034–T035 | cubierto |
| AC-14 | `imagen_only` no entra al extractor | §§0, 2–5 | T009–T010, T015–T018, T032–T035 | cubierto |
| AC-15 | Prohibición de completar externamente | §§0, 3, 5 | T011–T012, T015–T018, T043 | cubierto |
| AC-16 | Fallo técnico separado | §§0, 3–5 | T003–T008, T013–T018, T029–T030 | cubierto |
| AC-17 | Validación positiva sin gold | §§2–5 | T013–T014, T019–T022, T034–T035 | cubierto |
| AC-18 | Validación negativa antes de evaluar | §§2–5 | T013–T014, T034–T035 | cubierto |
| AC-19 | Gate de persistencia | §§0, 2–5 | T019–T022, T032–T035, T040–T042 | cubierto |
| AC-20 | Gold después de persistir; predicción inmutable | §§0, 2–5 | T019–T022, T032–T035, T040–T042 | cubierto |
| AC-21 | Comparación paper × promoter × property | §§0, 2–5 | T023–T030, T032–T035 | cubierto |
| AC-22 | Comparación por conjuntos | §§0, 3–5 | T025–T030, T033–T035 | cubierto |
| AC-23 | Reporte por propiedad | §§2–5 | T029–T030, T033–T035, T040–T042 | cubierto |
| AC-24 | Estratos de modalidad sólo en evaluator | §§0, 2–5 | T023–T024, T029–T030, T032–T035, T040–T042 | cubierto |
| AC-25 | Splits agrupados por paper | §§0, 3–5 | T023–T024, T029–T030 | cubierto |
| AC-26 | Limitación del subset positivo | §§1, 3, 5, 7 | T029–T030, T040–T042 | cubierto |
| AC-27 | Exclusiones de alcance | §§0–1, 5, 7 | T002, T043 | cubierto |
| AC-28 | Allowlist cerrada | §§0, 2–5 | T009–T010, T015–T016, T032–T035, T037–T043 | cubierto |
| AC-29 | Denylist defensiva e indirecta | §§0, 2–5 | T009–T010, T015–T016, T032–T035, T037–T043 | cubierto |
| AC-30 | `INVALID_CANDIDATE` diagnóstico | §§0, 3–5 | T003–T004, T013–T016, T034–T035 | cubierto |
| AC-31 | Gold no parseable falla cerrado | §§0, 2–5 | T025–T026, T034–T035 | cubierto |
| AC-32 | Caja -10 con literal ` + ` | §§0, 3–5 | T025–T026, T034–T035 | cubierto |
| AC-33 | Salto interno de Caja -35 no separa | §§0, 3–5 | T011–T012, T025–T026, T034–T035 | cubierto |

Resultado de cobertura: **33/33 criterios cubiertos por el plan y por al menos una tarea verificable**.

## Hallazgos

| ID | Severidad | Tipo | Evidencia | Corrección | Estado |
|---|---|---|---|---|---|
| A-01 | IMPORTANT | Dependencia incompleta | `T042` consume `$SAFE_CASE_MANIFEST` y el texto adyacente establece aprobación en `T039`, pero `T039` no figuraba en `Depends-on`. | Se añadió `T039` a las dependencias de `T042`. | RESUELTO |
| A-02 | IMPORTANT | Contradicción de secuenciación | Plan §6 hacía depender el gate determinista #11 de #1–#10; #10 es el adapter real sujeto a decisión humana, mientras TASKS y §7 declaran esa decisión no bloqueante para el baseline determinista. | §6 ahora depende de #1–#9; #10 se incluye sólo cuando exista decisión de provider/model y se valide el adapter opcional. | RESUELTO |

No quedaron hallazgos pendientes.

## Resultados de las seis comprobaciones

### 1. Cumplimiento constitucional

PASS.

- El extractor usa una entrada cerrada sin campos curatoriales, gold o evaluator-only.
- Todo valor aceptado exige asociación a promotor, propiedad y evidencia documental.
- No existe completado desde RegulonDB, genoma, consenso o conocimiento externo.
- Abstención científica y fallo técnico son tipos distintos.
- Persistencia precede al acceso al gold.
- Los splits se agrupan por paper.
- El gold real, papers privados, credenciales y outputs generados permanecen fuera de commits.

### 2. Cobertura requirements → spec → plan → tasks

PASS. Los 33 criterios de aceptación tienen cobertura explícita en plan y tareas.

### 3. Scope drift

PASS. No existe tarea que implemente RAG, embeddings, vector database, agentes, UI, deployment, promoter discovery, entity resolution compleja, lectura directa de figuras, PDF→GROBID, escritura a RegulonDB, suplementos o equivalencias biológicas Rpo↔sigma.

`T043` menciona esas capacidades únicamente como audit negativo de dependencias/imports. Los post-baseline milestones no tienen IDs de tarea y están marcados explícitamente fuera de la feature.

### 4. Contradicciones

PASS después de resolver A-01 y A-02. No se detectó contradicción científica, de leakage, evaluación, alcance o arquitectura.

### 5. Duplicación

PASS. Las tareas de test y sus pares de implementación son intencionales y tienen done-checks distintos. No hay dos tareas que posean la misma entrega.

### 6. Ambigüedad y carrier completeness

PASS.

- Cada tarea tiene objetivo, done-check, dependencias y trazabilidad.
- El plan contiene `§0 Global constraints`.
- Los contratos compartidos están definidos en `§3 Interfaces and contracts`.
- Las interfaces para tareas con consumidores aislados están repetidas en `Interfaces for context-isolated implementation`.
- Los IDs `T001`–`T044` son continuos y las dependencias apuntan sólo hacia tareas anteriores.

## Comprobaciones específicas del gate

### Frontera y orden anti-leakage

La única ruta de benchmark definida es:

```text
extractor
→ output validation
→ immutable persisted prediction
→ verified persisted reference
→ evaluator
→ gold loader/parser
```

`EvaluationService` rechaza predicciones directas en memoria. `GoldLoader` requiere la capacidad derivada de persistencia verificada. `T032–T035` prueban la frontera y el orden. `T040–T041` vuelven a probarlo en el runner local.

No hay un objeto extraction-side con gold path, ni un camino de prompts, retrieval, herramientas, logs o metadata arbitraria hacia el gold.

### Unidades metodológicas

- Sampling/split: `paper`.
- Inferencia agrupada: `paper × promoter`.
- Extracción/evaluación independiente: `paper × promoter × property`.
- Evidencia: uno o más fragmentos localizables.

### Representaciones y estados

Están representados y probados:

- `value_raw`;
- `value_normalized`;
- múltiples valores;
- evidencia y localización;
- qualifiers;
- abstención científica;
- `INVALID_CANDIDATE` sólo como diagnóstico;
- fallo técnico separado;
- `PARSE_ERROR / NEEDS_REVIEW`;
- `candidate_values` fuera de las predicciones aceptadas y de las métricas.

### Gold parser y datos privados

El parser se declara explícitamente específico de `SUBSET_GOLD.xlsx`, no universal. Los formatos no observados fallan cerrados.

El workbook real permaneció sin seguimiento y no fue abierto durante ANALYZE. Las tareas automáticas usan XLSX sintético bajo directorios temporales. El uso real aparece únicamente en `T042`, como ejecución local controlada posterior a las decisiones y aprobaciones correspondientes.

### HUMAN_DECISION_REQUIRED

Permanecen:

1. `T031`: tratamiento final de technical failures en headline metrics.
2. `T036`: provider/model real y parámetros de reproducibilidad.

Ambas decisiones siguen sin bloquear el baseline determinista. Sí bloquean el tramo controlado que depende explícitamente de ellas.

## Archivos modificados por ANALYZE

- Corregido: `02-DOCS/wiki/sdd/plans/guided-extraction-baseline.md`
- Actualizado para descubribilidad: `02-DOCS/wiki/index.md`
- Creado: `02-DOCS/process/2026-10-07-guided-extraction-baseline-analyze.md`

No se modificó la spec, constitution, decisions ni ninguno de los seis documentos raíz.

## Estado Git al cierre

```text
## feat/guided-extraction-baseline
 M 02-DOCS/wiki/index.md
 M 02-DOCS/wiki/sdd/decisions.md
?? 02-DOCS/data/SUBSET_GOLD.xlsx
?? 02-DOCS/process/2026-10-06-guided-extraction-baseline-clarify.md
?? 02-DOCS/process/2026-10-06-guided-extraction-baseline-specify.md
?? 02-DOCS/process/2026-10-07-guided-extraction-baseline-analyze.md
?? 02-DOCS/process/2026-10-07-guided-extraction-baseline-plan.md
?? 02-DOCS/process/2026-10-07-guided-extraction-baseline-tasks.md
?? 02-DOCS/wiki/sdd/plans/guided-extraction-baseline.md
?? 02-DOCS/wiki/sdd/specs/guided-extraction-baseline.md
```

`git diff --stat`:

```text
 02-DOCS/wiki/index.md         |  3 ++
 02-DOCS/wiki/sdd/decisions.md | 83 +++++++++++++++++++++++++++++++++++++++++++
 2 files changed, 86 insertions(+)
```

El stat estándar no incluye archivos sin seguimiento. `SUBSET_GOLD.xlsx` continúa sin seguimiento y no fue staged. `git diff --check` pasó, los seis documentos raíz no tienen diff y `git rev-list --count main..HEAD` devolvió `0`. No se creó commit ni se realizó push.

## Resultado y siguiente paso

ANALYZE pasa sin blockers. IMPLEMENT queda desbloqueado por el gate, pero no se ejecutó.

```json result-envelope
{
  "status": "complete",
  "executive_summary": "Cross-read completo: 33/33 criterios cubiertos; dos inconsistencias de secuenciación corregidas; cero blockers.",
  "artifact": "02-DOCS/process/2026-10-07-guided-extraction-baseline-analyze.md",
  "next_recommended": "implement",
  "risk": "medium",
  "skill_resolution": {
    "used": ["analyze"],
    "missing": [],
    "fallback": [],
    "compact_rules": [
      "Read adversarially across artifacts, not inside one.",
      "A finding without a location is an opinion."
    ]
  },
  "evidence": [
    "33/33 acceptance criteria mapped to plan and tasks",
    "A-01 and A-02 recorded and resolved",
    "root requirement documents unchanged",
    "gold workbook not opened",
    "no commit or push"
  ]
}
```
