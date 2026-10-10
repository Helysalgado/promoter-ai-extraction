---
type: guide
title: LIDR demo preparation
description: Checklist to record the demo by reloading the saved synthetic prediction, without a new provider call.
tags: [lidr, demo, ui]
timestamp: 2026-10-10T08:00:00-06:00
topic: lidr
slug: lidr-demo-prep
status: draft
---

# LIDR — preparación de la demostración

Guion: `02-DOCS/process/2026-10-10-lidr-demo-script.md`.

No pulses «Extraer propiedades». No exportes `ANTHROPIC_API_KEY` ni `OPENAI_API_KEY`. No abras gold, artículos reales ni `.env`.

La vista principal es la consulta en la página. Las capturas de `Documents/LIDR/promoter-ai-extraction/demo-evidence/` son evidencia secundaria y no se agregan a Git.

## Arranque, sin credenciales

Desde `.worktrees/lidr-application`:

```bash
unset ANTHROPIC_API_KEY OPENAI_API_KEY
export PREDICTION_DIR="$PWD/runs/ui-live-01"
uv run uvicorn promoter_ai_extraction.api:app --host 127.0.0.1 --port 8765
```

En otra terminal:

```bash
curl -sS http://127.0.0.1:8765/health
```

La respuesta esperada es `{"status":"ok","software_version":"0.1.0"}`.

Abre `http://127.0.0.1:8765/`. No cargues un archivo. Escribe `SYNTH-UI-LIVE-01` y `narnZp9`. Pulsa «Consultar resultado guardado».

## Comprobación antes de grabar

- Servidor: `GET /health` responde 200 y el proceso no tiene `ANTHROPIC_API_KEY` ni `OPENAI_API_KEY`.
- Navegador: una ventana en `http://127.0.0.1:8765/`, con zoom suficiente para las cuatro tarjetas. La pestaña de `.env` está cerrada.
- Formulario: PMID/ID `SYNTH-UI-LIVE-01`, promotor `narnZp9`, sin archivo y sin confirmación. «Consultar resultado guardado» está habilitado. «Extraer propiedades» está deshabilitado.
- Consulta: el estado dice «Resultado previamente guardado».
- Evidencias: la tarjeta de caja −10 muestra `TATAGT`, el fragmento literal, `txt:p:0003` y `lines:10-10`.
- Traza: `end_turn`, 3 rondas y 8 herramientas. TSS aparece como `INVALID_BACKEND_PAYLOAD`.
- Credenciales: no hay una clave visible en el navegador, en la terminal ni en un archivo abierto.
- Archivo: `runs/ui-live-01/SYNTH-UI-LIVE-01__narnZp9.json` existe. No lo edites durante la toma.

Si la consulta no pinta las tarjetas, detén la grabación. No pulses «Extraer propiedades» para reconstruirlas.

## Qué decir del resultado

La frase obligatoria, al pulsar el botón: se está recuperando una extracción ya ejecutada con Anthropic. No se está ejecutando otra vez el modelo.

TSS quedó en `INVALID_BACKEND_PAYLOAD` porque los identificadores de evidencia y los fragmentos no coincidían. El sistema no aceptó ese valor.

## Pruebas

`./scripts/verify.sh` no llama a un proveedor. La compuerta de este HEAD pasó 639 pruebas. En el video, esas 639 son pruebas del software. El README todavía cita 616 en un párrafo histórico: no leas ese número. Tampoco leas la frase antigua que dice que la rama no incluye interfaz.

## Al terminar

Detén Uvicorn. Confirma que la terminal no tiene `ANTHROPIC_API_KEY` ni `OPENAI_API_KEY`. No hagas commit de capturas ni de `runs/`.
