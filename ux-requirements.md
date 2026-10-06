# Requisitos UX — `promoter-ai-extraction`

**Versión:** 0.1  
**Estado:** borrador funcional de interfaz  
**Proyecto:** `promoter-ai-extraction`  
**Alcance:** MVP de interfaz para extracción guiada y evaluación de propiedades de promotores bacterianos

---

## 1. Propósito

Este documento define los requisitos de experiencia de usuario para la interfaz inicial de `promoter-ai-extraction`.

La interfaz debe permitir que un usuario pueda:

1. seleccionar o cargar la representación disponible de un artículo científico;
2. identificar el promotor que se desea analizar;
3. ejecutar la extracción de TSS, caja -10, caja -35 y factor sigma;
4. revisar el valor o valores obtenidos;
5. revisar la evidencia utilizada por el sistema;
6. distinguir claramente extracción, abstención y ambigüedad;
7. en casos pertenecientes al benchmark, comparar la predicción con el gold **sólo después de haber generado la extracción**.

La interfaz no pretende sustituir el flujo completo de curación de RegulonDB.

---

## 2. Usuario principal

El usuario principal es un **curador experto de regulación transcripcional bacteriana**.

La interfaz debe priorizar:

- trazabilidad;
- claridad científica;
- mínima fricción;
- revisión rápida;
- separación entre evidencia y conclusión;
- abstención explícita;
- ausencia de información irrelevante.

---

## 3. Principios UX

### 3.1 Evidencia antes que apariencia de certeza

La interfaz no debe presentar únicamente:

```text
TSS = -42
```

Debe mostrar, cuando exista:

```text
valor + forma original + evidencia + localización + status
```

El usuario debe poder responder rápidamente: **¿de dónde obtuvo el sistema este valor?**

### 3.2 Los estados científicos no son errores técnicos

Estados como:

```text
NOT_FOUND
INSUFFICIENT_EVIDENCE
UNSUPPORTED_MODALITY
AMBIGUOUS
```

son resultados científicos válidos.

### 3.3 No ocultar incertidumbre

Calificadores como `putative`, `possible`, `-10-like` o `appears to be` deben mantenerse visibles.

### 3.4 No mostrar el gold antes de la predicción

En modo benchmark, la predicción debe generarse y registrarse antes de habilitar la comparación con el gold.

### 3.5 Separar extracción y evaluación

La interfaz debe distinguir claramente:

```text
EXTRAER
```

de:

```text
COMPARAR CON GOLD
```

---

## 4. Modos de uso

### 4.1 Modo extracción

Entrada:

```text
paper + promotor identificado + alias opcional
```

Salida:

```text
TSS
caja -10
caja -35
factor sigma
+
evidencia
+
status
```

No existe comparación con gold.

### 4.2 Modo benchmark

Flujo:

```text
seleccionar caso
      |
      v
ocultar gold
      |
      v
ejecutar extracción
      |
      v
guardar predicción
      |
      v
habilitar "Mostrar evaluación"
      |
      v
comparar sistema vs. referencia curatorial
```

---

## 5. Flujo principal

### Paso 1 — Seleccionar artículo

El usuario debe poder seleccionar o cargar un archivo soportado.

Formatos iniciales:

```text
TXT
TEI/XML
```

### Paso 2 — Identificar paper

Mostrar o solicitar:

```text
PMID
```

### Paso 3 — Identificar promotor

Campos:

```text
Promoter name
Promoter ID              [si existe]
Gene / historical alias  [opcional]
```

### Paso 4 — Ejecutar extracción

Acción principal:

```text
Extract promoter properties
```

### Paso 5 — Revisar resultados

Mostrar una tarjeta o bloque independiente por propiedad.

### Paso 6 — Revisar evidencia

El usuario debe poder inspeccionar fragmento, sección, tipo de fuente y localización.

### Paso 7 — Evaluación opcional

Sólo en modo benchmark y sólo después de finalizar la extracción.

---

## 6. Pantalla inicial

```text
┌─────────────────────────────────────────────────────┐
│ promoter-ai-extraction                              │
│ Evidence extraction for bacterial promoters         │
├─────────────────────────────────────────────────────┤
│ ARTICLE                                             │
│ PMID                 [________________]              │
│ Source               [ TXT / TEI ]                  │
│ Document             [ Select / Upload ]            │
│                                                     │
│ PROMOTER                                            │
│ Name                 [________________]              │
│ ID                   [________________]              │
│ Gene / alias         [________________]              │
│                                                     │
│              [ Extract properties ]                 │
└─────────────────────────────────────────────────────┘
```

---

## 7. Vista de resultados

Ejemplo:

```text
TSS                                      EXTRACTED
──────────────────────────────────────────────────

Normalized value
-42

Reported as
42 bp upstream of the ATG

Anchor
translation_start

Evidence
"The transcription start site was mapped 42 bp
 upstream of the ATG..."

Location
Results

Source type
body_text
```

---

## 8. Campos visibles por resultado

Cada propiedad debe poder mostrar:

```text
status
value_raw
value_normalized
qualifier
evidence
source_type
source_location
derivation_note
```

No deben mostrarse campos vacíos innecesarios.

---

## 9. Estados visuales

### `EXTRACTED`

Mostrar valor, evidencia, normalización, calificadores y localización.

### `NOT_FOUND`

Mensaje sugerido:

> No se localizó evidencia suficiente para establecer un valor en la representación disponible.

No usar “Property absent”.

### `INSUFFICIENT_EVIDENCE`

Mostrar evidencia relevante y la razón por la que no se aceptó un valor.

### `UNSUPPORTED_MODALITY`

Mostrar la referencia documental disponible y explicar que la representación actual no permite resolver el valor.

No debe inferirse automáticamente a partir de `Modalidad_origen = imagen_only`.

### `AMBIGUOUS`

Mostrar candidatos y razón de ambigüedad sin presentarlos como valores aceptados.

### `INVALID_CANDIDATE`

Estado provisional. Si se mantiene en el contrato final, mostrar candidato, regla incumplida y evidencia relacionada.

---

## 10. Evidencia

Para cada valor debe mostrarse una sección de evidencia visible y fácil de revisar.

```text
Evidence
────────────────────────────────

"The transcription start site was mapped
42 bp upstream of the ATG."

Source
Results

Type
body_text
```

Cuando existan varios fragmentos:

```text
Evidence 1
Evidence 2
...
```

---

## 11. Navegación evidencia-documento

Diseño recomendado:

```text
┌──────────────────────────┬──────────────────────────┐
│ ARTICLE                  │ EXTRACTION               │
│                          │                          │
│ Results                  │ TSS     -42             │
│                          │                          │
│ "...42 bp upstream..."   │ -10     TATAAT          │
│        ^ highlighted     │                          │
│                          │ -35     NOT_FOUND        │
│                          │                          │
│ Figure 2...              │ Sigma   sigma32         │
│                          │                          │
└──────────────────────────┴──────────────────────────┘
```

Al seleccionar una propiedad, la evidencia correspondiente debería resaltarse cuando sea técnicamente posible.

---

## 12. Tipo de fuente de la evidencia

`source_type` puede incluir inicialmente:

```text
body_text
table
figure_caption
figure_reference
figure_associated_text
other
```

---

## 13. Tratamiento de `imagen_only`

`imagen_only` describe la modalidad en la que el curador identificó originalmente el dato.

No significa automáticamente:

```text
UNSUPPORTED_MODALITY
```

El TEI/TXT puede contener captions, referencias a figuras o texto asociado suficiente para permitir una extracción.

En modo benchmark deben mostrarse separadamente:

```text
System status:
EXTRACTED

Curator modality:
imagen_only
```

---

## 14. Múltiples valores

La interfaz debe soportar múltiples valores explícitamente.

Ejemplo:

```text
TSS                                     EXTRACTED

Value 1
-42

Value 2
-39
```

Cada valor debe poder asociarse con su evidencia.

---

## 15. Reglas específicas de visualización — TSS

Puede mostrar:

```text
relative_position
genomic_coordinate
designation
anchor_raw
anchor_normalized
nucleotide
experimental_method
```

No debe mostrar `+1` como posición relativa si sólo es la designación del TSS.

---

## 16. Reglas específicas — cajas -10 / -35

Mostrar:

```text
sequence
raw representation
normalized sequence
qualifier
position, if reported
```

La interfaz no debe convertir una caja `putative` en una caja “confirmada”.

---

## 17. Reglas específicas — sigma

Mostrar:

```text
raw designation
normalized designation
qualifier
```

Por ahora no deben presentarse equivalencias Rpo como resueltas automáticamente.

---

## 18. Modo benchmark — comparación

Después de generar la predicción:

```text
[ Show evaluation ]
```

Ejemplo:

| Property | System | Curated reference | Result |
|---|---|---|---|
| TSS | -42 | -42 | MATCH |
| -10 | TATAAT | TATAAT | MATCH |
| -35 | NOT_FOUND | TTGTTA | MISS |
| sigma | sigma32 | sigma32 | MATCH |

---

## 19. Información visible en evaluación

La vista puede incluir:

```text
GT_para_referencia
Modalidad_origen
Valor_RegulonDB
Valor_verificado_manualmente
resultado de comparación
```

Estos campos deben estar claramente identificados como **datos de evaluación** y nunca utilizarse como entrada del extractor.

---

## 20. Resultados posibles de comparación

Como mínimo:

```text
EXACT_MATCH
PARTIAL_MATCH
WRONG_VALUE
MISS
EXTRA_VALUE
```

Las definiciones deben seguir el `Evaluation Contract`.

---

## 21. Resumen del caso

Puede mostrarse un resumen como:

```text
3 / 4 properties correctly recovered
```

pero siempre manteniendo los resultados individuales de TSS, -10, -35 y sigma.

---

## 22. Métricas agregadas

El MVP no necesita un dashboard complejo.

Una vista posterior puede incluir:

- recall total;
- recall `texto_explicito`;
- recall `imagen_only`;
- precision;
- F1;
- resultados por propiedad.

---

## 23. Manejo de errores técnicos

Los errores técnicos deben distinguirse de los estados científicos.

Ejemplos:

```text
FILE_NOT_READABLE
INVALID_XML
EMPTY_DOCUMENT
MODEL_ERROR
TIMEOUT
INTERNAL_ERROR
```

No usar `NOT_FOUND` para un fallo técnico.

---

## 24. Validaciones de entrada

Antes de ejecutar:

- debe existir un documento válido;
- debe existir identidad mínima del promotor;
- el tipo de archivo debe ser soportado;
- el documento no debe estar vacío;
- en modo benchmark debe existir una unidad válida del dataset.

---

## 25. Estado de procesamiento

Durante la extracción mostrar:

```text
Analyzing article...
```

Etapas opcionales comprensibles:

```text
Reading document
Finding promoter context
Extracting properties
Preparing evidence
```

No se debe presentar razonamiento interno del modelo.

---

## 26. Historial de ejecución

Para el MVP es deseable conservar:

```text
paper
promoter
timestamp
system/prompt version
result
```

Esto facilita reproducibilidad y evaluación.

---

## 27. Feedback del curador

No es obligatorio para el MVP inicial, pero la interfaz debe quedar preparada conceptualmente para una futura acción:

```text
Accept
Correct
Needs review
```

En la primera versión puede omitirse para evitar mezclar extracción con modificación del gold.

---

## 28. Acciones fuera del MVP

La interfaz inicial no debe:

- editar RegulonDB;
- actualizar automáticamente registros curatoriales;
- descubrir todos los promotores del paper;
- decidir automáticamente si un promotor es nuevo;
- gestionar usuarios y roles complejos;
- resolver todo el flujo curatorial institucional;
- recuperar automáticamente materiales suplementarios;
- exigir procesamiento visual de figuras;
- modificar el gold desde la vista de evaluación.

---

## 29. Accesibilidad y legibilidad

La interfaz debe:

- evitar textos excesivamente pequeños;
- utilizar estados acompañados de texto, no sólo color;
- mantener contraste suficiente;
- permitir copiar valores y evidencia;
- no depender de hover para información esencial;
- permitir navegación mediante teclado en los flujos principales;
- conservar secuencias en una tipografía claramente legible.

---

## 30. Prioridades del MVP

### P0 — imprescindible

- cargar/seleccionar TXT o TEI;
- indicar PMID;
- indicar promotor;
- alias opcional;
- ejecutar extracción;
- mostrar cuatro propiedades;
- mostrar status;
- mostrar valor raw/normalizado;
- mostrar evidencia;
- mostrar localización;
- soportar múltiples valores;
- separar error técnico de abstención científica.

### P1 — altamente deseable

- panel de documento junto a resultados;
- resaltado de evidencia;
- modo benchmark;
- comparación después de predicción;
- mostrar modalidad curatorial;
- historial básico de ejecuciones.

### P2 — posterior

- feedback del curador;
- dashboards;
- anotación correctiva;
- multimodalidad;
- integración con flujo real de RegulonDB;
- resolución de entidad;
- descubrimiento de promotores.

---

## 31. Criterios de aceptación UX

### UC-01 — extracción básica

**GIVEN** un TXT o TEI válido y un promotor identificado  
**WHEN** el usuario ejecuta la extracción  
**THEN** la interfaz muestra un resultado independiente para TSS, -10, -35 y sigma.

### UC-02 — valor extraído

**GIVEN** una propiedad con evidencia suficiente  
**WHEN** el sistema devuelve `EXTRACTED`  
**THEN** la interfaz muestra al menos valor, evidencia y status.

### UC-03 — abstención

**GIVEN** una propiedad sin evidencia suficiente  
**WHEN** el sistema se abstiene  
**THEN** la interfaz muestra claramente el tipo de abstención y no inventa un valor.

### UC-04 — múltiples valores

**GIVEN** dos o más valores válidos para la misma propiedad del mismo promotor  
**WHEN** el sistema devuelve la extracción  
**THEN** la interfaz presenta cada valor como elemento independiente.

### UC-05 — benchmark sin leakage

**GIVEN** un caso del gold  
**WHEN** el usuario abre el caso  
**THEN** los valores curatoriales permanecen ocultos.

**AND WHEN** la extracción termina y queda registrada  
**THEN** se habilita la comparación con el gold.

### UC-06 — evidencia originalmente visual

**GIVEN** un registro curatorial `imagen_only`  
**WHEN** el TEI/TXT contiene suficiente información textual asociada a la figura  
**THEN** el sistema puede mostrar `EXTRACTED`.

### UC-07 — error técnico

**GIVEN** un archivo corrupto o un fallo de procesamiento  
**WHEN** la extracción no puede ejecutarse  
**THEN** la interfaz muestra un error técnico distinto de los estados científicos.

---

## 32. Arquitectura de información mínima

```text
promoter-ai-extraction
|
|-- Extraction
|   |-- Article
|   |-- Promoter
|   `-- Results
|       |-- TSS
|       |-- -10
|       |-- -35
|       `-- Sigma
|
|-- Evidence view
|
`-- Benchmark evaluation   [cuando aplique]
```

---

## 33. Relación con otros contratos

La interfaz debe implementar conceptualmente las decisiones descritas en:

```text
proyecto_formal_promoter-ai-extraction
gold-set-contract
evaluation-contract
contrato-comun-extraccion
```

La interfaz no redefine reglas científicas.

---

## 34. Decisiones cerradas

- habrá una interfaz para el sistema;
- será un MVP enfocado en extracción;
- se utilizarán inicialmente TEI/TXT;
- el usuario proporciona un promotor identificado;
- se presentan las cuatro propiedades de forma independiente;
- valor y evidencia deben visualizarse juntos;
- se soportan múltiples valores;
- la abstención es visible;
- `imagen_only` no implica automáticamente inaccesibilidad desde TEI/TXT;
- el gold sólo se muestra después de generar la predicción;
- la interfaz no edita RegulonDB;
- descubrimiento automático de promotores queda fuera del MVP.

---

## 35. Decisiones abiertas para diseño visual

Quedan para una etapa posterior:

- layout final;
- navegación exacta;
- componentes visuales;
- uso de panel lateral o pantalla dividida;
- diseño responsivo;
- framework de frontend;
- mecanismo de subida/selección;
- representación exacta de highlights;
- persistencia de historial;
- autenticación, si llegara a ser necesaria.

---

## 36. Principio rector de la interfaz

> **La interfaz debe permitir que un curador vea rápidamente qué afirma el sistema, qué evidencia encontró para afirmarlo y cuándo decidió no afirmar nada.**
