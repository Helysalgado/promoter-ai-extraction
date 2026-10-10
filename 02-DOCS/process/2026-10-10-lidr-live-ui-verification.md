---
type: verification
title: Live verification — LIDR scientific UI
description: One real Chrome extraction through the local UI. Functional application check only.
tags: [lidr, ui, anthropic, verification]
timestamp: 2026-10-10T02:30:00-06:00
topic: lidr
slug: lidr-live-ui-verification
status: recorded
---

# LIDR — verificación integral real de la interfaz

- Fecha: 2026-10-10
- Rama: `feat/lidr-application`
- HEAD: `922f48d`
- Canal: Chrome, conducido por Playwright, contra FastAPI en `127.0.0.1`
- Ruta: `POST /agent/extract`
- Proveedor: Anthropic
- Modelo: `claude-sonnet-5-5`
- Recuperación: FastEmbed local
- Documento: sintético. Identidad `SYNTH-UI-LIVE-01` / `narnZp9`. Sinónimo `narnase`
- Llamadas: una, por el botón «Extraer propiedades». Sin interceptación, sin respuestas simuladas, sin reintento y sin fallback

Esta nota registra que la interfaz completa el flujo y pinta la respuesta real. No es una evaluación de calidad científica sobre un corpus. No se usó gold ni un artículo real.

## Configuración

El TXT es el mismo documento sintético de la verificación previa del agente. El identificador de paper es nuevo. El método fue el agente y el proveedor quedó fijo en Anthropic. La predicción se escribió en `runs/ui-live-01`. Playwright no sustituyó el cuerpo de ninguna respuesta HTTP.

## Resultado

HTTP 200 en 17.96 s. El navegador envió una sola petición de extracción. El registro del servidor coincide. Terminación `end_turn`: 3 rondas y 8 herramientas, en el orden cuatro `retrieve_evidence` y después cuatro `extract_property`.

| Propiedad | En la tarjeta | En el JSON |
|---|---|---|
| TSS | Fallo técnico `INVALID_BACKEND_PAYLOAD` | Técnico, etapa `extraction` |
| Caja −10 | Extraído `TATAGT` | `EXTRACTED` |
| Caja −35 | Extraído `TTGATA` | `EXTRACTED` |
| Factor sigma | Extraído `sigma32` | `EXTRACTED` |

Las cuatro tarjetas coinciden con `properties` de la respuesta HTTP. La traza visible coincide con `agent` de esa respuesta. Ese objeto es el mismo que `system_fingerprint.agent` en la predicción guardada.

No hubo candidatos rechazados. Tras guardar, el botón quedó deshabilitado para esa identidad. La consola no registró una excepción de página. El 404 de `/favicon.ico` no altera el flujo.

## TSS

El extractor recibió un payload de TSS y el validador lo rechazó. El motivo es una inconsistencia entre los identificadores de evidencia y los fragmentos para un valor presentado como aceptado. El mensaje técnico fue: el backend devolvió identificadores y fragmentos de evidencia que no coinciden para un valor aceptado.

La interfaz lo muestra como fallo técnico. No lo convierte en `NOT_FOUND`. Queda sin corregir y sin una segunda llamada.

## Persistencia

El archivo es `runs/ui-live-01/SYNTH-UI-LIVE-01__narnZp9.json`. Ese directorio está ignorado por Git. Esta nota no copia el archivo. TSS queda como fallo técnico. Las otras tres propiedades quedan `EXTRACTED` con el mismo valor que la tarjeta.

## Capturas

Las capturas de formulario, procesamiento, tarjetas, detalle y traza quedan fuera del repositorio. No entran en un commit.

## Qué es y qué no es

Esto verifica la aplicación: el navegador arma la petición, FastAPI persiste y la página representa el JSON real, incluido un fallo técnico.

No mide calidad científica sobre un corpus. Un documento sintético no aumenta la muestra de evaluación. El detalle del agente, sin la interfaz, sigue en `02-DOCS/process/2026-10-10-lidr-agent-live-verification.md`.
