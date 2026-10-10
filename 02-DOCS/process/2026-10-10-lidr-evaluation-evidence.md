---
type: verification
title: LIDR evaluation evidence
description: What has been measured, on which inputs, and what is still not a corpus score.
tags: [lidr, evaluation, evidence]
timestamp: 2026-10-10T01:33:00-06:00
topic: lidr
slug: lidr-evaluation-evidence
status: recorded
---

# LIDR — evidencia de evaluación

- Fecha: 2026-10-10
- Rama: `feat/lidr-application`
- HEAD de código: `2c42d62`
- Esta nota no copia predicciones, gold, texto de artículos ni credenciales.

Las pruebas sintéticas demuestran contratos y regresión. No validan el corpus.

## Seis evidencias distintas

| Evidencia | Entrada | Qué afirma | Qué no afirma |
|---|---|---|---|
| Suite automatizada | Fixtures sintéticos y dobles | 616 pruebas pasan sin proveedor. | Rendimiento sobre papers reales. |
| Baseline real con Claude | Un caso de desarrollo, CLI, `claude-sonnet-5-5` | El baseline persistió y el evaluador escribió un reporte. | Un score del workset. |
| Baseline real con OpenAI | El mismo control, otra corrida | Fallo técnico de proveedor en los cuatro slots. | Una extracción científica. |
| RAG con FastEmbed | El `POST /agent/extract` sintético | El modelo local `BAAI/bge-small-en-v1.5` recuperó segmentos. | Calidad de recuperación contra evidencia anotada. |
| Agente real | Un documento sintético, Anthropic | Un ciclo `retrieve_evidence` → `tool_result` → `extract_property` quedó persistido. | Las cuatro propiedades correctas, ni un corpus. |
| Interfaz real | El mismo tipo de documento sintético, desde Chrome | La página envió una petición y pintó el JSON real, incluido un fallo técnico. | Calidad científica sobre un corpus. |

## Suite

`./scripts/verify.sh` el 2026-10-10: 616 passed en 4.83 s. La compuerta también confirmó que `data/`, `02-DOCS/data/` y el workbook real están ignorados, y que los fixtures sintéticos no lo están.

No hubo llamada a OpenAI ni a Anthropic en esa corrida.

## Baseline real

El cierre está en `02-DOCS/wiki/sdd/progress/guided-extraction-baseline.md`, sección T042. Los artefactos siguen en `runs/`, ignorados. Esta nota no los reabre.

Claude, un caso, modelo `claude-sonnet-5-5`, tope 4096, cero reintentos. Cuatro resultados científicos y cero fallos técnicos en esa corrida: TSS `EXTRACTED`, caja −10 `AMBIGUOUS`, caja −35 `NOT_FOUND`, factor sigma `NOT_FOUND`. El reporte histórico, vista `end_to_end` y vista científica, cuenta TP 0, FP 1, FN 3, `n_targets` 3, `coverage` 1.0, `technical_failure_rate` 0.0. Esos números describen un caso. No son el score del subconjunto.

OpenAI, modelo `gpt-6.1-sol`, misma forma de control: cuatro slots `PROVIDER_ERROR` con `RateLimitError`. No hubo extracción científica. El reporte cuenta `technical_failures` 3 porque factor sigma tiene `n_targets` 0, `coverage` 0.0 y TP 0, FP 0, FN 3.

## Embeddings y recuperación

La verificación real de FastEmbed es la del agente sintético, no una evaluación aparte. Modelo local `BAAI/bge-small-en-v1.5`. Cuatro llamadas `retrieve_evidence`, todas en modo `retrieved`. Cada una devolvió los siete segmentos del documento corto. El detalle está en `02-DOCS/process/2026-10-10-lidr-agent-live-verification.md`.

## Agente real

`POST /agent/extract`, documento sintético, HTTP 200 en 17.6 s, 3 rondas, 8 herramientas, terminación `end_turn`. Cuatro extracciones intentadas. Caja −10, caja −35 y factor sigma quedaron `EXTRACTED` y validadas. TSS no.

## Interfaz real

La verificación desde Chrome está en `02-DOCS/process/2026-10-10-lidr-live-ui-verification.md`. Comprueba la aplicación: una petición, persistencia y tarjetas alineadas con el JSON. No es una evaluación de corpus. El TSS repitió el fallo técnico ya registrado; no hubo segunda llamada.

## Métricas

Métricas de extracción que el evaluador calcula, por propiedad: `precision`, `recall`, `f1`, `exact_row_accuracy`, `recall_texto_explicito`, `recall_imagen_only`. El reporte añade `coverage`, `technical_failure_rate`, abstenciones científicas y fallos técnicos. La vista principal es `end_to_end`. La definición vive en `evaluation-contract.md`.

Aquí «recuperación» del contrato es recuperar valores gold, no acertar segmentos. El RAG no calcula precision ni recall de segmentos. Su traza guarda modo, ids y scores. No hay denominador de evidencia anotada para esos ids: el contrato ya dice que el gold no trae de forma sistemática las frases del curador.

## Errores técnicos observados

- OpenAI en el baseline real: `PROVIDER_ERROR` / `RateLimitError` en los cuatro slots. Sin valor científico.
- Agente sintético, TSS: `INVALID_BACKEND_PAYLOAD`. El modelo devolvió identificadores de evidencia y fragmentos que no coinciden para un valor presentado como aceptado. El validador lo rechazó. No se repitió la petición y no se cambió el código.
- Limitación ya registrada, independiente de esa corrida: normalizar una distancia anclada no demuestra que la distancia sea el TSS.

## Tamaño de muestra

No hay evaluación completa del corpus ni del subconjunto de trabajo. Hay un caso real de baseline y un documento sintético de agente. La prueba de interfaz usa ese mismo tipo de documento y no aumenta la muestra. La suite de 616 no aumenta ese tamaño.
