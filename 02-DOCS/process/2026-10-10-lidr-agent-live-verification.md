---
type: verification
title: Live verification — LIDR Anthropic agent
description: One real POST /agent/extract on a fully synthetic document. Technical integration only.
tags: [lidr, agent, anthropic, verification]
timestamp: 2026-10-10T01:28:00-06:00
topic: lidr
slug: lidr-agent-live-verification
status: recorded
---

# LIDR — verificación real del agente Anthropic

- Fecha: 2026-10-10
- Rama: `feat/lidr-application`
- HEAD: `2c42d62`
- Endpoint: `POST /agent/extract`
- Proveedor: Anthropic
- Modelo: `claude-sonnet-5-5`
- Documento: sintético, identidad ficticia `SYNTH-AGENT-01` / `narnZp9`
- Llamadas: una. Sin reintento, sin fallback, sin cambio de código ni de contratos científicos

Esta nota registra integración técnica. No es una evaluación de rendimiento sobre el corpus. No se usó gold ni un artículo real.

## Qué demuestra cada capa

| Capa | Resultado |
|---|---|
| Orquestación | Éxito. HTTP 200 en 17.6 s. Terminación `end_turn`. |
| Recuperación documental | Éxito. FastEmbed local. Cuatro `retrieve_evidence` con modo `retrieved`. |
| Resultados científicos validados | Tres. Caja −10, caja −35 y factor sigma. |
| TSS | Fallo técnico. No es una conclusión científica. |

## Flujo real de function calling

Límites vigentes en la corrida: 6 rondas, 8 ejecuciones de herramienta, 1024 tokens de salida por ronda de orquestación, 4096 tokens de salida por extracción científica, 0 reintentos.

Se usaron 3 rondas y 8 herramientas.

1. El modelo pidió `retrieve_evidence` para TSS, caja −10, caja −35 y factor sigma.
2. El host ejecutó las cuatro recuperaciones y devolvió cada `tool_result` al modelo.
3. En la ronda siguiente el modelo pidió `extract_property` para las cuatro propiedades. Esa petición solo corre después de que Anthropic ya recibió el resultado de recuperación de esa propiedad.
4. La tercera ronda cerró con `end_turn`.

El cupo de herramientas no cortó la corrida.

## Recuperación

FastEmbed usó el modelo local. Cada una de las cuatro recuperaciones devolvió los siete segmentos del documento sintético corto (`txt:p:0000`–`txt:p:0006`), 577 caracteres de contexto. El documento cabe entero en la ventana, así que el conteo no es una selección de cuatro segmentos.

## Propiedades

| Propiedad | Capa del resultado | Estado | Valor validado | Evidencia citada |
|---|---|---|---|---|
| TSS | Técnica | `INVALID_BACKEND_PAYLOAD` | ninguno | ninguna |
| Caja −10 | Científica | `EXTRACTED` | `TATAGT` | `txt:p:0003` |
| Caja −35 | Científica | `EXTRACTED` | `TTGATA` | `txt:p:0004` |
| Factor sigma | Científica | `EXTRACTED` | `sigma32` | `txt:p:0005` |

Se intentaron cuatro extracciones científicas. Tres pasaron la validación. TSS llegó al extractor y el validador rechazó el payload.

## Persistencia

La predicción quedó en `runs/agent-live-01`, identificador `SYNTH-AGENT-01__narnZp9`. Ese directorio está ignorado por Git. Esta nota no copia el archivo.

## Limitación conocida

El payload de TSS traía identificadores de evidencia y fragmentos en número distinto para un valor que el modelo presentaba como aceptado. El mensaje técnico fue: el backend devolvió identificadores y fragmentos de evidencia que no coinciden para un valor aceptado.

Eso no invalida el ciclo de herramientas. Queda sin corregir y sin una segunda llamada.

## Fuera de alcance

- No se midió rendimiento sobre el corpus.
- El SDK no dejó conteo de tokens en la respuesta persistida.
- No hubo cambio de prompts, código, contratos científicos, ni de la predicción guardada.
