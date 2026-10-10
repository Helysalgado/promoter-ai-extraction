# promoter-ai-extraction

Extracción guiada de cuatro propiedades de un promotor bacteriano, con evidencia trazable y evaluación separada del gold.

Versión de software: `0.1.0`. Python `>=3.11`.

## Objetivo y alcance

El sistema recibe un artículo (TXT o TEI/XML) y la identidad de un promotor. Produce un resultado independiente para cada propiedad:

- TSS
- Caja −10
- Caja −35
- Factor sigma

Cada resultado puede ser un valor validado, una abstención científica o un fallo técnico. El extractor no recibe el gold.

Esta rama añade tres piezas sobre el baseline: un servicio HTTP local, recuperación semántica local sobre el documento enviado, y un agente Anthropic con dos herramientas. No incluye interfaz gráfica, despliegue, descubrimiento de promotores ni escritura a RegulonDB.

Los contratos científicos están en la raíz y no se resumen aquí:

- `project-overview.md`
- `project-requirements.md`
- `extraction-contract.md`
- `gold-set-contract.md`
- `evaluation-contract.md`
- `ux-requirements.md`

## Arquitectura

Hay tres entradas. Comparten el validador científico y el almacén de predicciones. No comparten el mismo contexto de modelo.

| Entrada | Qué decide el código | Qué decide el modelo |
|---|---|---|
| CLI `python -m promoter_ai_extraction.baseline` | Carga el manifiesto, extrae las cuatro propiedades sobre el documento completo, persiste y después abre el gold. | El texto de cada propiedad. |
| `POST /extract` | Parte el documento, recupera segmentos y extrae las cuatro propiedades en orden fijo. | El texto de cada propiedad, solo sobre el contexto recuperado. |
| `POST /agent/extract` | Ejecuta solo `retrieve_evidence` y `extract_property`. La identidad del paper y del promotor la fija el servidor. | Qué herramienta llamar, para qué propiedad y cuándo parar. |

El CLI no usa RAG. Las dos rutas HTTP sí. `POST /extract` no llama al agente. El agente no llama a `GuidedExtractionService.run`.

Proveedores, sin fallback:

- OpenAI, modelo `gpt-6.1-sol`. Es el default del CLI y de `POST /extract`.
- Anthropic, modelo `claude-sonnet-5-5`. Es el único proveedor de `POST /agent/extract`.

Los dos endpoints HTTP comparten `run_id` (`paper_id__promoter_name`). El primer archivo guardado conserva ese id. La otra ruta responde 409 y no lo sobrescribe.

## Requisitos e instalación

Hace falta Python 3.11 y [uv](https://docs.astral.sh/uv/).

```bash
uv sync --all-groups
```

Eso instala el proyecto y el grupo de desarrollo (`pytest`). No hace falta una clave para la suite.

## Variables de entorno

El proceso lee el entorno. Ni el CLI ni Uvicorn cargan un archivo `.env` por sí solos. Exporta la variable en la shell antes de arrancar, o cárgala tú. No la escribas en el repositorio. `.env` está ignorado por Git.

| Variable | Quién la usa |
|---|---|
| `OPENAI_API_KEY` | CLI con `--provider openai` y `POST /extract` cuando `provider` es `openai`. |
| `ANTHROPIC_API_KEY` | CLI con `--provider anthropic`, `POST /extract` con `provider` `anthropic`, y `POST /agent/extract`. |
| `PREDICTION_DIR` | Solo el servicio HTTP. Default: `runs/http`. |

Si falta la clave del proveedor elegido, el CLI termina en 1 con `MISSING_CREDENTIAL`. HTTP responde 503 con el mismo código. No hay reintento automático (`max_retries=0`).

## CLI

```bash
uv run python -m promoter_ai_extraction.baseline \
  --manifest PATH \
  --documents PATH \
  --gold PATH \
  --predictions PATH \
  --report PATH \
  --provider openai \
  --max-output-tokens N
```

`--provider` acepta `openai` o `anthropic`. El default es `openai`.

El tope de salida por propiedad, si omites `--max-output-tokens`, es 128000 para OpenAI y 4096 para Anthropic. Un entero positivo sustituye ese default. El CLI no aplica el tope HTTP de 4096.

El manifiesto, los documentos y el gold de un caso real no están en Git. La suite construye gold y documentos sintéticos en un directorio temporal. El comando reproducible sin proveedor es `./scripts/verify.sh`.

Salida 0: se escribió un reporte de evaluación. Un fallo técnico dentro de una corrida ya persistida sigue siendo salida 0. Salida 1: falta una clave, el manifiesto o el documento no se pueden leer, o no se produjo reporte.

## FastAPI local

Escucha solo en localhost:

```bash
uv run uvicorn promoter_ai_extraction.api:app --host 127.0.0.1 --port 8765
```

El cliente envía el texto del documento. No envía una ruta de disco, una clave, un campo de gold ni el directorio de predicciones.

Abre `http://127.0.0.1:8765/` para la página local. Esa página llama a los mismos POST. No carga un archivo `.env` ni muestra la clave.

## Endpoints

### `GET /`

Devuelve la página de extracción. El CSS y el JavaScript están en `/ui/app.css` y `/ui/app.js`. `/docs` no cambia.

### `GET /health`

Responde 200:

```json
{"status": "ok", "software_version": "0.1.0"}
```

No usa modelo ni embeddings.

### `POST /extract`

Cuerpo cerrado. Una clave de más, incluido cualquier campo de gold, responde 422 `INVALID_REQUEST`.

| Campo | Regla |
|---|---|
| `paper_id`, `promoter_name` | Texto no vacío. |
| `promoter_id`, `paper_gene_synonym` | Opcionales. |
| `document_format` | `TXT` o `TEI/XML`. |
| `document` | Texto. Más de 100000 caracteres: 413 `DOCUMENT_TOO_LARGE`. |
| `provider` | `openai` o `anthropic`. Default: `openai`. |
| `max_output_tokens` | Opcional. Si viene, entero de 1 a 4096. Fuera de rango: 422 `LIMIT_EXCEEDED`. Si se omite, el servidor usa 4096 para los dos proveedores. |

La predicción ya existente para ese `run_id` responde 409 `FILE_EXISTS` antes de llamar al proveedor.

### `POST /agent/extract`

Mismo cuerpo, con dos diferencias: `provider` solo acepta `anthropic`, y la respuesta trae la traza `agent` en lugar de `retrieval`.

Límites del bucle, fijos en código:

- 6 rondas de orquestación
- 8 ejecuciones de herramienta
- 1024 tokens de salida por ronda de orquestación
- 4096 tokens de salida por extracción científica, salvo que el cliente envíe un entero entre 1 y 4096
- 0 reintentos

`extract_property` no corre en la misma respuesta en la que se pidió `retrieve_evidence` para esa propiedad. El host espera a devolver el `tool_result` y a que el modelo pida la extracción en una ronda posterior.

### `GET /predictions/{run_id}`

Lee una predicción ya guardada en `PREDICTION_DIR`. No llama a FastEmbed, a un proveedor ni al extractor. No lista el directorio y no escribe el archivo.

`run_id` es `paper_id__promoter_name`. Una barra, una barra invertida, dos puntos o `..` responden 422 `INVALID_REQUEST`. Si no hay archivo, 404 `FILE_NOT_FOUND`. El cuerpo 200 trae `properties` y, cuando la huella guardada los tiene, `agent` o `retrieval`. No trae la ruta del archivo.

La página tiene el botón «Consultar resultado guardado». Usa el PMID/ID y el nombre del promotor. No pide el documento ni la confirmación de una llamada al proveedor.

## RAG local

Solo en HTTP. El índice vive en memoria y solo para el documento de esa petición. El modelo de embeddings es `BAAI/bge-small-en-v1.5`, vía FastEmbed, y se carga en el primer uso, no al importar el paquete.

Por propiedad, la selección une anclas léxicas del nombre del promotor, los 8 vecinos semánticos más altos y el párrafo adyacente. No hay umbral de score. El contexto devuelto al extractor cabe en 12000 caracteres. La traza pública guarda modelo, modo, ids de segmento y scores. No guarda vectores ni el texto del segmento.

Si no queda ningún segmento usable, la propiedad queda como fallo técnico `INSUFFICIENT_RETRIEVAL`. Si el modelo local no carga, HTTP responde 503 `EMBEDDER_UNAVAILABLE`.

## Agente

El orquestador es la API Messages de Anthropic, con herramientas reales. No hay LangChain.

Herramientas permitidas, y solo el argumento `property`:

1. `retrieve_evidence` — ids, scores y tamaño de contexto. Sin texto del documento.
2. `extract_property` — corre `PropertyExtractor` con la identidad fijada por el servidor y el contexto ya recuperado.

Una herramienta desconocida, un argumento de más o una propiedad fuera de las cuatro se rechaza y no se ejecuta. El agente no puede cambiar paper, promotor, rutas ni gold.

Si el modelo termina antes de cubrir una propiedad, esa propiedad queda `AGENT_SKIPPED`. Si se agota el cupo, queda `AGENT_STEP_LIMIT`. Un error del orquestador queda `ORCHESTRATOR_ERROR`. Esos tres códigos son técnicos. No son abstenciones científicas.

## Extracción y evaluación

La extracción persiste primero. La evaluación abre el gold después, y solo en el CLI. HTTP no evalúa.

El reporte del CLI tiene dos vistas. `end_to_end` es la vista principal: un fallo técnico sobre un valor gold cuenta como no recuperado. `scientific` es diagnóstica y no convierte ese fallo en abstención.

Métricas de extracción, por propiedad: `precision`, `recall`, `f1`, `exact_row_accuracy`, `recall_texto_explicito`, `recall_imagen_only`, más `coverage` y `technical_failure_rate`. La definición está en `evaluation-contract.md`.

No hay métrica de calidad del RAG. La traza de recuperación no es un recall de segmentos contra evidencia anotada.

## Documentación y pruebas

| Qué | Dónde |
|---|---|
| Mapa | `02-DOCS/wiki/index.md` |
| Constitución y decisiones | `02-DOCS/wiki/sdd/` |
| Verificación real del agente | `02-DOCS/process/2026-10-10-lidr-agent-live-verification.md` |
| Evidencia de evaluación LIDR | `02-DOCS/process/2026-10-10-lidr-evaluation-evidence.md` |
| Pruebas | `tests/unit`, `tests/contract`, `tests/integration` |
| Fixture sintético versionado | `tests/fixtures/synthetic_safe_manifest.json` |
| Compuerta | `./scripts/verify.sh` |

```bash
./scripts/verify.sh
```

La corrida del 2026-10-10 pasó 616 pruebas en 4.83 s. Esas pruebas usan dobles y fixtures sintéticos. No llaman a OpenAI ni a Anthropic. No validan el corpus.

## Limitaciones

- La suite sintética no es un score científico del corpus.
- El baseline real con Claude es un caso de desarrollo. No es una evaluación del workset. El detalle está en la nota de evaluación.
- La corrida real de OpenAI de ese mismo control quedó en `PROVIDER_ERROR` por límite del proveedor. No produjo extracción científica.
- En la prueba real del agente, TSS salió `INVALID_BACKEND_PAYLOAD`: identificadores y fragmentos de evidencia que no coinciden. Caja −10, caja −35 y factor sigma sí se validaron. No se reintentó.
- Normalizar una distancia anclada no demuestra que esa distancia sea el TSS.
- El gold actual no sostiene una tasa completa de falsas afirmaciones ni una métrica de recuperación de segmentos.
- El cupo de 8 herramientas cuenta también los rechazos. Cuatro recuperaciones y cuatro extracciones en la misma respuesta agotarían el cupo antes de una extracción válida.
- La página local no hace benchmark, no muestra historial y no se despliega fuera de localhost.

## Ejemplos sintéticos

Comprobación local, sin clave y sin proveedor:

```bash
uv run python -c "from fastapi.testclient import TestClient; from promoter_ai_extraction.api import app; print(TestClient(app).get('/health').json())"
```

Salida observada: `{'status': 'ok', 'software_version': '0.1.0'}`.

Un campo de gold se rechaza antes de cualquier modelo:

```bash
uv run python -c "from fastapi.testclient import TestClient; from promoter_ai_extraction.api import app; print(TestClient(app).post('/extract', json={'paper_id':'SYNTH-DOC-01','promoter_name':'narnZp9','document_format':'TXT','document':'Synthetic paragraph.','gold_value':'no'}).status_code)"
```

Salida observada: `422`.

La petición siguiente sí llama a Anthropic si `ANTHROPIC_API_KEY` está en el entorno. No forma parte de la suite. El texto es ficticio.

```bash
uv run uvicorn promoter_ai_extraction.api:app --host 127.0.0.1 --port 8765
```

```bash
curl --silent --show-error \
  -X POST http://127.0.0.1:8765/agent/extract \
  -H 'content-type: application/json' \
  -d '{"paper_id":"SYNTH-DOC-01","promoter_name":"narnZp9","paper_gene_synonym":"narnase","document_format":"TXT","document":"In the fictional organism Narnia coli, promoter narnZp9 of narnase has a transcription start site 48 bp upstream of the start codon. The site is a guanine. The minus 10 box is TATAGT. The minus 35 box is TTGATA. The sigma factor is sigma32. A second gene, sporease, uses promoter sporZp2 and is not the target.","provider":"anthropic"}'
```

Usa otro `paper_id` si `runs/http/SYNTH-DOC-01__narnZp9.json` ya existe. La segunda llamada a ese id responde 409.
