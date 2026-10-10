---
type: guide
title: LIDR final demo script
description: Timed script for a 5–7 minute recording of the local scientific UI, using the completed synthetic run.
tags: [lidr, demo, ui]
timestamp: 2026-10-10T07:40:00-06:00
topic: lidr
slug: lidr-demo-script
status: draft
---

# LIDR — guion de la demostración final

- Duración objetivo: 6 minutos 30 segundos, dentro de 5–7 minutos
- Rama: `feat/lidr-application`
- HEAD: `b66f694`
- Caso en pantalla: documento sintético, `SYNTH-UI-LIVE-01` / `narnZp9`, sinónimo `narnase`
- Corrida ya hecha: HTTP 200 en 17.96 s, una petición, 3 rondas, 8 herramientas, terminación `end_turn`
- Esta grabación no pulsa «Extraer propiedades» y no llama a Anthropic ni a OpenAI

La página local no reabre una predicción guardada. El formulario se muestra en vivo. Las tarjetas, el detalle y la traza se muestran con las capturas de esa corrida.

## 0:00–0:40 — Qué hace el sistema

En pantalla: la página en `http://127.0.0.1:8765/`, todavía sin archivo.

Decir: el sistema recibe un artículo y la identidad de un promotor. Devuelve cuatro propiedades, cada una como valor validado, abstención científica o fallo técnico. El extractor no recibe el gold. La evaluación queda fuera de esta pantalla.

## 0:40–1:20 — Carga del documento

En pantalla: elegir `/tmp/ui-live-01/narnZp9.txt`. Dejar visibles el nombre, `590 B` y el formato `TXT`.

Decir: el archivo es sintético. El navegador lee el texto y lo enviará en el cuerpo de la petición. No envía una ruta de disco, una clave ni un campo de gold. El artículo completo no se pinta en la página.

## 1:20–2:00 — Identidad del promotor

En pantalla: PMID/ID `SYNTH-UI-LIVE-01`, nombre `narnZp9`, sinónimo `narnase`. Método «Agente». Proveedor Anthropic, deshabilitado. Confirmación marcada. El botón puede verse habilitado. No pulsarlo.

Decir: la identidad del paper y del promotor la fija el servidor a partir de esos campos. El agente solo puede pedir dos herramientas, y solo para una de las cuatro propiedades. El sinónimo entra en la consulta de recuperación. Cambiar el método o el proveedor no cambia el `run_id`.

## 2:00–3:20 — Recuperación y function calling

En pantalla: la captura `05-trace.png`. Recorrer la traza de arriba abajo.

Decir: FastEmbed corre en local con `BAAI/bge-small-en-v1.5`. El índice vive solo para este documento. En la corrida el modelo pidió `retrieve_evidence` para TSS, caja −10, caja −35 y factor sigma. El documento es corto: cada recuperación devolvió los siete segmentos, `txt:p:0000` a `txt:p:0006`.

Después el modelo pidió `extract_property` para las cuatro. Esa extracción espera a que el `tool_result` de la recuperación ya haya vuelto. La tercera ronda cerró con `end_turn`. Fueron 3 rondas y 8 herramientas, el tope de ejecuciones. No hubo reintento.

## 3:20–4:40 — Cuatro propiedades y el fallo del TSS

En pantalla: la captura `03-cards.png`. Luego `04-detail.png`, con el detalle de TSS.

Decir, tarjeta por tarjeta:

- TSS: fallo técnico `INVALID_BACKEND_PAYLOAD`. El validador rechazó el payload porque los identificadores de evidencia y los fragmentos no coinciden para un valor presentado como aceptado. La etapa es `extraction`. La tarjeta no dice `NOT_FOUND`.
- Caja −10: `EXTRACTED`, valor `TATAGT`, evidencia `txt:p:0003`, líneas 10–10.
- Caja −35: `EXTRACTED`, valor `TTGATA`, evidencia `txt:p:0004`, líneas 12–12.
- Factor sigma: `EXTRACTED`, valor `sigma32`, evidencia `txt:p:0005`, líneas 14–14.

No hubo candidatos rechazados. Tres resultados son científicos y validados. TSS es un fallo técnico y se queda así.

## 4:40–5:20 — Persistencia

En pantalla: el archivo `runs/ui-live-01/SYNTH-UI-LIVE-01__narnZp9.json`, abierto en el editor. Mostrar el nombre del archivo y el estado de las cuatro propiedades. No recorrer el documento ni abrir `.env`.

Decir: la predicción se escribió antes de cualquier comparación con gold. HTTP no evalúa. El `run_id` es `SYNTH-UI-LIVE-01__narnZp9`. La traza `agent` del archivo es la misma que pintó la página. El directorio está ignorado por Git.

Si alguien pulsara «Extraer propiedades» otra vez con este directorio, el servidor respondería 409 antes de llamar al proveedor y no mostraría estas tarjetas. Por eso la demostración usa las capturas.

## 5:20–6:10 — Pruebas y corpus

En pantalla: la nota `02-DOCS/process/2026-10-10-lidr-evaluation-evidence.md`, en la tabla de evidencias. Si hay tiempo, la última línea de `./scripts/verify.sh` ya ejecutada: 628 pruebas.

Decir: 628 pruebas son regresión de contratos, con fixtures sintéticos y dobles. No son 628 artículos evaluados. No llaman a un proveedor. El corpus completo sigue sin una medida de rendimiento. Hay un caso real de baseline y este documento sintético. Esta pantalla demuestra el flujo de la aplicación.

## 6:10–6:30 — Cierre

En pantalla: volver a las cuatro tarjetas de `03-cards.png`.

Decir: la aplicación local carga el documento, identifica el promotor, recupera con RAG, orquesta con function calling, valida y persiste. El fallo técnico del TSS queda visible y no se reinterpreta. El score del corpus queda pendiente.
