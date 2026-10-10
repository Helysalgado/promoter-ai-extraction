---
type: guide
title: LIDR demo preparation
description: Checklist to record the final demo from the completed synthetic run, without a new provider call.
tags: [lidr, demo, ui]
timestamp: 2026-10-10T07:40:00-06:00
topic: lidr
slug: lidr-demo-prep
status: draft
---

# LIDR — preparación de la demostración

Guion: `02-DOCS/process/2026-10-10-lidr-demo-script.md`.

No pulses «Extraer propiedades». No exportes `ANTHROPIC_API_KEY` ni `OPENAI_API_KEY`. No abras gold, artículos reales ni `.env`.

## Antes de grabar

- Cierra la pestaña de `.env`.
- Las cinco capturas ya tienen respaldo local, fuera del repositorio y fuera de Git: `Documents/LIDR/promoter-ai-extraction/demo-evidence/`. Los originales siguen en `/tmp/ui-live-01/shots/`. No las agregues a Git.
- Comprueba que siguen estos archivos:
  - `/tmp/ui-live-01/narnZp9.txt` (590 bytes)
  - `/tmp/ui-live-01/shots/01-form-before.png`
  - `/tmp/ui-live-01/shots/02-processing.png`
  - `/tmp/ui-live-01/shots/03-cards.png`
  - `/tmp/ui-live-01/shots/04-detail.png`
  - `/tmp/ui-live-01/shots/05-trace.png`
  - `runs/ui-live-01/SYNTH-UI-LIVE-01__narnZp9.json`
- Ten a mano un grabador de pantalla y una ventana del navegador. El zoom del navegador debe dejar las cuatro tarjetas en una fila.

## Arranque, sin proveedor

Desde `.worktrees/lidr-application`:

```bash
export PREDICTION_DIR="$PWD/runs/ui-live-01"
uv run uvicorn promoter_ai_extraction.api:app --host 127.0.0.1 --port 8765
```

En otra terminal:

```bash
curl -sS http://127.0.0.1:8765/health
```

La respuesta esperada es `{"status":"ok","software_version":"0.1.0"}`.

Abre `http://127.0.0.1:8765/`. Selecciona el TXT sintético y completa `SYNTH-UI-LIVE-01`, `narnZp9` y `narnase`. Marca «Agente» y la confirmación. Detente ahí.

`PREDICTION_DIR` apunta al directorio de la corrida ya guardada. Un clic accidental con esa identidad recibe 409 antes del proveedor y no pinta las tarjetas. Las tarjetas de la demostración son las capturas.

## Qué mostrar de los resultados

- Procesamiento: `02-processing.png`. El botón está deshabilitado y las tarjetas siguen en «Sin resultado».
- Resultado: `03-cards.png`.
- Detalle del TSS: `04-detail.png`.
- Traza: `05-trace.png`.
- Archivo persistido: solo el nombre y el estado de las cuatro propiedades.

## Pruebas

`./scripts/verify.sh` no llama a un proveedor. La compuerta de este HEAD pasó 628 pruebas. En el video, esas 628 son regresión. El README todavía cita 616 en un párrafo histórico: no leas ese número. Tampoco leas la frase antigua que dice que la rama no incluye interfaz.

## Al terminar

Detén Uvicorn. Confirma que el entorno de la terminal no tiene `ANTHROPIC_API_KEY` ni `OPENAI_API_KEY`. No hagas commit de capturas ni de `runs/`.

## Recurso que falta para un único plano en vivo

La página no tiene historial. No puede volver a dibujar `SYNTH-UI-LIVE-01` desde el JSON sin una petición nueva. La grabación del resultado usa las cinco capturas. El respaldo local está en `Documents/LIDR/promoter-ai-extraction/demo-evidence/`. Si `/tmp` se vacía, usa esas copias. No hagas otra llamada al proveedor para reconstruirlas.
