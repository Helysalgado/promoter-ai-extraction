---
type: guide
title: LIDR final demo script
description: Six-minute script that reloads the saved synthetic prediction from the local page, without a new provider call.
tags: [lidr, demo, ui]
timestamp: 2026-10-10T08:00:00-06:00
topic: lidr
slug: lidr-demo-script
status: draft
---

# LIDR — guion de la demostración final

- Duración objetivo: 6 minutos
- Rama: `feat/lidr-application`
- HEAD: `dc200a8`
- Caso: `SYNTH-UI-LIVE-01` / `narnZp9`
- Archivo ya guardado: `runs/ui-live-01/SYNTH-UI-LIVE-01__narnZp9.json`
- Acción en pantalla: «Consultar resultado guardado»
- Esta grabación no pulsa «Extraer propiedades» y no llama a Anthropic ni a OpenAI

La corrida original ya se hizo con Anthropic, FastAPI y FastEmbed. El video recupera ese resultado. No vuelve a ejecutar el modelo.

Las capturas de `Documents/LIDR/promoter-ai-extraction/demo-evidence/` quedan como evidencia secundaria. No son el plano principal.

## 0:00–0:35 — Problema y cuatro propiedades

En pantalla: `http://127.0.0.1:8765/`, con el formulario vacío.

Decir: el sistema lee un artículo y la identidad de un promotor bacteriano. Devuelve cuatro propiedades: TSS, caja −10, caja −35 y factor sigma. Cada una puede ser un valor validado, una abstención científica o un fallo técnico. El extractor no recibe el gold.

## 0:35–1:05 — Interfaz y datos de entrada

En pantalla: el mismo formulario. No selecciones archivo. No marques la confirmación. No abras `.env`.

Decir: la página es local. Para esta demostración no hace falta volver a cargar el documento. La extracción que vamos a ver ya se ejecutó sobre un texto sintético, con el agente de Anthropic. El archivo de esa corrida está en el directorio de predicciones del servidor.

## 1:05–1:35 — Artículo y promotor

En pantalla: escribe PMID/ID `SYNTH-UI-LIVE-01` y nombre `narnZp9`. Deja visible que «Consultar resultado guardado» se habilita y que «Extraer propiedades» sigue deshabilitado.

Decir: la identidad consultada es ese artículo y ese promotor. El `run_id` es `SYNTH-UI-LIVE-01__narnZp9`. La corrida original también usó el sinónimo `narnase`. La consulta no lo necesita y no envía el documento.

## 1:35–2:10 — Consulta del resultado guardado

En pantalla: pulsa «Consultar resultado guardado». Espera el texto «Resultado previamente guardado».

Decir, en ese momento: esto recupera una extracción ya ejecutada con Anthropic. No está llamando otra vez al modelo. No hay RAG nuevo ni una petición de extracción.

## 2:10–3:05 — Cuatro propiedades

En pantalla: las cuatro tarjetas, sin abrir todavía el detalle.

Decir:

- TSS: fallo técnico `INVALID_BACKEND_PAYLOAD`. El modelo presentó un valor, pero los identificadores de evidencia y los fragmentos no coincidían. El validador rechazó ese payload. El sistema no lo aceptó y la tarjeta no lo convierte en `NOT_FOUND`.
- Caja −10: `EXTRACTED`, `TATAGT`.
- Caja −35: `EXTRACTED`, `TTGATA`.
- Factor sigma: `EXTRACTED`, `sigma32`.

Tres resultados son científicos y validados. TSS queda como fallo técnico.

## 3:05–3:45 — Evidencia y localización

En pantalla: pulsa la tarjeta de caja −10.

Decir: el valor informado y el normalizado son `TATAGT`. El fragmento es «The minus 10 box of promoter narnZp9 is TATAGT.» El segmento es `txt:p:0003` y la ubicación `lines:10-10`. La fuente es `body_text`. La página muestra ese fragmento. No muestra el artículo completo.

## 3:45–4:35 — Traza del agente y RAG

En pantalla: abre «Traza de recuperación o del agente». Recórrela de arriba abajo.

Decir: la traza es la de la corrida previa. FastEmbed usó el modelo local `BAAI/bge-small-en-v1.5`. El documento sintético es corto y cada recuperación devolvió los siete segmentos, de `txt:p:0000` a `txt:p:0006`. El modelo pidió `retrieve_evidence` para las cuatro propiedades y, en la ronda siguiente, `extract_property` para las cuatro. La tercera ronda cerró con `end_turn`. Fueron 3 rondas y 8 herramientas. TSS quedó `INVALID_BACKEND_PAYLOAD`. Las otras tres quedaron `EXTRACTED`. No hubo reintento.

## 4:35–5:15 — Persistencia y reproducibilidad

En pantalla: el nombre del archivo `runs/ui-live-01/SYNTH-UI-LIVE-01__narnZp9.json` en el editor, sin recorrer el documento. Vuelve después a las tarjetas. «Extraer propiedades» sigue deshabilitado.

Decir: esa consulta leyó el archivo ya guardado. No lo modificó. La predicción se escribió antes de cualquier comparación con gold. HTTP no evalúa. El mismo `run_id` responde 409 si alguien intenta extraer otra vez, y esa respuesta sale antes de llamar al proveedor. El directorio está ignorado por Git. Otra persona reproduce la vista arrancando el servidor con ese `PREDICTION_DIR` y pulsando el mismo botón.

## 5:15–6:00 — Limitaciones y siguiente paso

En pantalla: la tabla de `02-DOCS/process/2026-10-10-lidr-evaluation-evidence.md`. Si cabe, la línea de `./scripts/verify.sh` con 639 pruebas.

Decir: 639 pruebas son pruebas del software, con fixtures sintéticos y dobles. No son 639 evaluaciones científicas. No llaman a un proveedor. El corpus completo sigue sin una medida de rendimiento. Hay un caso real de baseline y este documento sintético. El fallo del TSS queda registrado y no se reinterpreta. El score del corpus sigue pendiente.
