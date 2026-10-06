# `promoter-ai-extraction`
# Project Requirements

**Versión:** 0.1  
**Estado:** requisitos científicos y funcionales consolidados  
**Proyecto:** `promoter-ai-extraction`  
**Dominio:** regulación transcripcional bacteriana  
**Caso inicial:** promotores de *Escherichia coli* asociados a RegulonDB  

---

## 1. Propósito del documento

Este documento consolida los requisitos humanos, científicos, curatoriales, funcionales y de evaluación de `promoter-ai-extraction`.

Su objetivo es definir **qué problema debe resolver el sistema, qué datos puede utilizar, qué debe producir, cómo debe comportarse científicamente y cómo será evaluado** antes de entrar en decisiones de arquitectura o implementación.

Este documento no define todavía:

- framework de frontend;
- proveedor de LLM;
- estrategia RAG;
- agentes;
- embeddings;
- vector database;
- infraestructura;
- despliegue;
- contratos de API;
- estructura de repositorio.

Esas decisiones deberán derivarse posteriormente de estos requisitos.

---

# 2. Problema

RegulonDB contiene promotores con propiedades curatoriales como:

- TSS;
- caja -10;
- caja -35;
- factor sigma.

Cada promotor puede estar asociado a uno o más artículos científicos. Sin embargo, históricamente la relación entre una propiedad específica y el paper que la sustenta no siempre quedó registrada explícitamente.

Por tanto, para determinar la procedencia documental de una propiedad, un curador debe revisar los papers asociados y establecer:

- qué propiedad está realmente reportada;
- qué valor puede obtenerse;
- a qué promotor corresponde;
- en qué modalidad aparece;
- si el valor coincide o no con la anotación histórica;
- si la evidencia disponible permite establecer un valor;
- o si la información no puede recuperarse de ese paper.

`promoter-ai-extraction` busca automatizar parte de este trabajo mediante extracción guiada, estructurada y trazable.

---

# 3. Pregunta principal

> **Dado un artículo científico y un promotor identificado, ¿puede un sistema de IA determinar qué valores de TSS, caja -10, caja -35 y factor sigma pueden obtenerse de ese artículo, mostrando la evidencia que sustenta cada conclusión y absteniéndose cuando no exista soporte suficiente?**

---

# 4. Objetivo general

Desarrollar y evaluar un sistema de IA que asista la curación de literatura científica mediante la extracción trazable de propiedades de promotores bacterianos a partir de artículos científicos.

---

# 5. Objetivos específicos

El sistema deberá:

1. recibir un artículo y la identidad/contexto de un promotor;
2. evaluar independientemente TSS, caja -10, caja -35 y factor sigma;
3. extraer uno o múltiples valores cuando estén suficientemente sustentados;
4. conservar la forma original del valor reportado;
5. producir una representación normalizada cuando corresponda;
6. mostrar evidencia documental;
7. conservar localización de evidencia cuando sea posible;
8. preservar calificadores como `putative`, `possible` o equivalentes;
9. distinguir extracción, insuficiencia de evidencia, ausencia de hallazgo y ambigüedad;
10. abstenerse de completar información por plausibilidad biológica;
11. producir una salida estructurada y reproducible;
12. permitir evaluación programática contra una referencia curatorial;
13. evitar leakage de los valores objetivo;
14. servir posteriormente como base para asistir la curación de literatura nueva.

---

# 6. Usuario principal

El usuario principal es un:

> **curador experto en regulación transcripcional bacteriana**

El sistema debe optimizar la revisión científica, no sustituir la decisión curatorial final.

El usuario debe poder saber rápidamente:

- qué encontró el sistema;
- qué valor propone;
- de dónde lo obtuvo;
- qué tan directa es la afirmación;
- cuándo el sistema no pudo establecer un valor.

---

# 7. Alcance de la Parte 1

La Parte 1 corresponde al sistema evaluable del Proyecto Final de AI Engineering.

Flujo principal:

```text
paper + promotor identificado
            |
            v
      extracción de:
      - TSS
      - caja -10
      - caja -35
      - sigma
            |
            v
 valor(es) + evidencia + trazabilidad + abstención
```

## 7.1 Incluido

- artículos científicos reales;
- TEI/XML;
- TXT derivado de TEI;
- PMID;
- identidad de promotor;
- nombre de promotor;
- alias/sinónimo histórico cuando exista;
- TSS;
- caja -10;
- caja -35;
- factor sigma;
- múltiples valores;
- normalización controlada;
- evidencia;
- localización;
- calificadores;
- abstención;
- ambigüedad;
- evaluación contra gold curatorial;
- interfaz mínima de uso y demostración.

## 7.2 Fuera del alcance de la Parte 1

- descubrimiento automático de todos los promotores de un paper;
- clasificación completa del paper en promotores, TUs, interacciones y otros objetos;
- decidir automáticamente si un promotor es nuevo o ya existe;
- actualización automática de RegulonDB;
- edición directa de RegulonDB;
- resolución exhaustiva de aliases;
- recuperación de material suplementario no disponible;
- reconstrucción de predicciones históricas desde archivos ausentes;
- procesamiento visual exhaustivo de figuras;
- flujo institucional completo de curación;
- sustitución automática del curador.

---

# 8. Continuación futura

Una segunda etapa podrá ampliar el sistema hacia:

```text
papers recientes
      |
      v
clasificación
      |
      v
detección de promotores
      |
      v
resolución de entidad
      |
      v
nuevo / conocido
      |
      v
extracción de propiedades
      |
      v
revisión humana
      |
      v
RegulonDB
```

Esta ampliación puede incorporar:

- descubrimiento de promotores;
- entity resolution;
- multimodalidad;
- nuevas propiedades;
- integración al flujo periódico de curación;
- evaluación prospectiva con literatura nueva.

---

# 9. Fuentes de datos

## 9.1 Papers

Los artículos científicos son la fuente primaria de evidencia.

## 9.2 TEI/XML

Los papers se encuentran disponibles en representación TEI/XML producida previamente mediante GROBID.

## 9.3 TXT

Existe texto derivado del TEI/XML que conserva estructura documental cuando es posible.

Puede contener:

- título;
- resumen;
- métodos;
- resultados;
- discusión;
- captions;
- referencias a figuras;
- tablas o texto asociado;
- otros fragmentos recuperados.

## 9.4 PDF

El PDF original puede existir como fuente de referencia, pero la primera versión del extractor se evaluará principalmente sobre TEI/TXT.

La transformación PDF -> TEI/TXT no forma parte del núcleo de extracción.

## 9.5 Material suplementario

No se dispone sistemáticamente del material suplementario.

Por tanto:

> **la información disponible únicamente en archivos suplementarios ausentes no forma parte del universo documental observable de la Parte 1.**

---

# 10. Dataset curatorial

Existe un conjunto de trabajo derivado de la revisión manual de papers asociados a RegulonDB.

El subset actual contiene:

- 329 registros;
- 76 papers;
- 130 promotores.

Distribución actual por propiedad:

| Propiedad | Registros |
|---|---:|
| Caja -10 | 101 |
| TSS | 98 |
| Caja -35 | 86 |
| Factor sigma | 44 |

Distribución actual por modalidad:

| Modalidad | Registros |
|---|---:|
| `texto_explicito` | 133 |
| `imagen_only` | 196 |

Este subset es provisional y no limita el contrato del gold final.

---

# 11. Unidad metodológica

## 11.1 Unidad de muestreo

> **paper**

## 11.2 Unidad natural de inferencia

> **paper × promotor**

## 11.3 Unidad de extracción y evaluación

> **paper × promotor × propiedad**

## 11.4 Unidad de evidencia

> uno o más elementos localizables del artículo que sustentan una conclusión

## 11.5 Unidad de partición estadística

> **paper**

Todos los registros de un mismo paper deben permanecer juntos en el mismo split.

---

# 12. Propiedades objetivo

Las propiedades iniciales son:

```text
TSS
caja -10
caja -35
factor sigma
```

Cada propiedad debe producir una conclusión independiente.

Ejemplo:

```text
TSS       -> EXTRACTED
-10       -> EXTRACTED
-35       -> NOT_FOUND
sigma     -> INSUFFICIENT_EVIDENCE
```

---

# 13. Contrato común de salida

Cada unidad `paper × promotor × propiedad` debe producir conceptualmente:

```text
identity
status
values[]
candidate_values[]
evidence_items[]
abstention_or_ambiguity_reason
```

Cada valor aceptado debe poder conservar:

```text
value_raw
value_normalized
qualifier
derivation_note
evidence_refs[]
property_specific_details
```

---

# 14. Estados del extractor

Estados iniciales:

```text
EXTRACTED
NOT_FOUND
INSUFFICIENT_EVIDENCE
UNSUPPORTED_MODALITY
AMBIGUOUS
INVALID_CANDIDATE
```

## 14.1 `EXTRACTED`

Existe evidencia suficiente para establecer uno o más valores.

## 14.2 `NOT_FOUND`

El sistema no localizó evidencia suficiente en la representación que recibió.

No significa que la propiedad no exista.

## 14.3 `INSUFFICIENT_EVIDENCE`

Se encontró información relacionada con la propiedad, pero no permite establecer responsablemente un valor.

## 14.4 `UNSUPPORTED_MODALITY`

La representación disponible indica que la información relevante probablemente depende de una modalidad que el sistema actual no puede resolver.

No debe inferirse automáticamente desde `imagen_only`.

## 14.5 `AMBIGUOUS`

Existen candidatos o interpretaciones, pero no puede resolverse responsablemente la asociación correcta.

## 14.6 `INVALID_CANDIDATE`

Estado provisional para candidatos que no cumplen una regla del contrato vigente.

Su permanencia como estado final debe revisarse posteriormente.

---

# 15. Reglas transversales de extracción

## SR-01 — Evidencia obligatoria para valores aceptados

Todo valor con `status = EXTRACTED` debe estar acompañado de evidencia producida por el sistema.

## SR-02 — Asociación obligatoria al promotor

La evidencia debe permitir asociar el valor con el promotor objetivo.

## SR-03 — Asociación obligatoria a la propiedad

Encontrar un número, secuencia o sigma no basta; debe poder asociarse con la propiedad correspondiente.

## SR-04 — Múltiples valores

Una propiedad puede tener cero, uno o múltiples valores.

## SR-05 — Múltiples promotores

Si un paper contiene varios promotores, el sistema no debe asignar valores por mera proximidad, orden de aparición o plausibilidad.

## SR-06 — Abstención

Cuando no pueda establecerse el valor, el sistema debe abstenerse.

## SR-07 — No biological guessing

No deben completarse valores usando:

- consensos;
- conocimiento general;
- valores memorizados;
- RegulonDB;
- genoma externo;
- propiedades relacionadas.

## SR-08 — Forma original y normalizada

Cuando exista normalización, deben distinguirse:

```text
value_raw
value_normalized
```

## SR-09 — Calificadores

El sistema debe preservar calificadores como:

```text
putative
predicted
possible
-like
appears to be
```

## SR-10 — Evidencia distribuida

Una conclusión puede sustentarse con uno o varios fragmentos.

---

# 16. Requisitos científicos de TSS

## TSS-01 — Representaciones válidas

El sistema puede representar un TSS como:

- posición relativa;
- coordenada genómica;
- designación `+1`;
- nucleótido;
- combinación de los anteriores cuando corresponda.

## TSS-02 — Ancla de inicio de traducción

Las siguientes expresiones pueden normalizarse conceptualmente como `translation_start` cuando el contexto lo permita:

```text
translation start
translational start
start codon
initiation codon
ATG
gene start
```

Debe conservarse la forma original.

## TSS-03 — Signo

Cuando existe un ancla válida:

```text
upstream   -> negativo
downstream -> positivo
```

## TSS-04 — Ancla ausente

Una expresión como:

```text
42 bp upstream
```

sin referencia suficiente no debe convertirse automáticamente a `-42` relativo al inicio de traducción.

## TSS-05 — `+1`

`+1` puede ser la designación del inicio de transcripción.

No debe convertirse automáticamente en distancia `+1` respecto al inicio de traducción.

## TSS-06 — Coordenada genómica

Una coordenada genómica absoluta reportada por el paper es un TSS válido aunque no pueda transformarse a posición relativa usando únicamente el paper.

## TSS-07 — Múltiples TSS

Deben aceptarse múltiples TSS cuando estén asociados al mismo promotor.

## TSS-08 — Nucleótido

El nucleótido del TSS puede registrarse cuando esté disponible documentalmente.

## TSS-09 — Técnica experimental

La técnica experimental puede conservarse cuando pueda asociarse al TSS.

No es requisito obligatorio para aceptar un valor.

---

# 17. Requisitos científicos de cajas -10 y -35

## BOX-01 — Valor principal

El valor principal es la secuencia nucleotídica que el paper asocia con la caja del promotor.

## BOX-02 — Asociación

Una secuencia no puede considerarse caja únicamente por parecerse a un consenso.

## BOX-03 — Consenso general

Una secuencia de consenso mencionada en el paper no puede asignarse automáticamente al promotor.

## BOX-04 — Normalización permitida

Se permiten transformaciones inequívocamente tipográficas:

```text
tataat  -> TATAAT
TAT AAT -> TATAAT
TAT-AAT -> TATAAT
```

## BOX-05 — Normalización prohibida

No se permite:

- corregir bases;
- completar secuencias;
- reconstruir desde el genoma;
- inferir desde sigma;
- reemplazar por un consenso.

## BOX-06 — Longitud

**No se congela todavía un mínimo definitivo de longitud para scoring.**

El subset actual contiene casos curatoriales muy cortos que requieren revisión antes de convertir la longitud en una regla excluyente.

La longitud puede utilizarse como dato descriptivo o señal diagnóstica, pero no debe invalidar automáticamente un valor del gold mientras esta regla permanezca abierta.

## BOX-07 — Calificadores

Una caja `putative`, `predicted`, `possible` o `-like` puede extraerse si el propio paper la asocia con el promotor.

El calificativo debe conservarse.

## BOX-08 — Múltiples valores

Pueden existir múltiples secuencias válidas para una misma caja del mismo promotor.

## BOX-09 — Posición sin secuencia

Si el paper sólo proporciona la posición de la caja pero el target de evaluación es la secuencia:

```text
INSUFFICIENT_EVIDENCE
```

No debe reconstruirse la secuencia externamente.

---

# 18. Requisitos científicos de factor sigma

## SIG-01 — Asociación

El sigma debe estar asociado al promotor objetivo o a su evento de transcripción.

## SIG-02 — Variantes tipográficas

Se permiten normalizaciones inequívocas como:

```text
σ32
σ 32
sigma32
sigma 32
Sigma32
Sigma 32
```

a una forma normalizada como:

```text
sigma32
```

## SIG-03 — Forma original

Debe conservarse `value_raw`.

## SIG-04 — Múltiples sigmas

Deben aceptarse múltiples factores sigma si el paper los asocia al mismo promotor.

## SIG-05 — Equivalencias biológicas

Equivalencias como:

```text
RpoS <-> sigmaS <-> sigma38
RpoH <-> sigma32
RpoN <-> sigma54
```

no se aplicarán automáticamente por ahora.

Deberán definirse posteriormente mediante una tabla explícita, global y versionada si el gold lo requiere.

---

# 19. Gold set

El gold representa el resultado de la revisión curatorial humana.

No es equivalente a una copia directa de RegulonDB.

El gold debe conservar la separación entre:

```text
valor histórico de RegulonDB
valor revisado por el curador
modalidad de origen
target operativo
```

---

# 20. Columnas actuales relevantes

El subset actual contiene:

```text
Fila_origen
ID_promotor
Nombre_promotor
Sinonimo_gen_en_este_paper
ID_paper
Propiedad
Valor_RegulonDB
Sin_dato_en_RegulonDB
Modalidad_origen
Valor_verificado_manualmente
GT_para_referencia
Año_confirmado
Técnica_confirmada_manualmente
Evidencia
```

---

# 21. Target operativo

Para el subset actual:

> **`GT_para_referencia` es el target operativo de evaluación.**

Debe conservarse su procedencia.

Cuando existe `Valor_verificado_manualmente`, éste refleja una intervención explícita del curador.

Cuando `GT_para_referencia` utiliza el valor de RegulonDB, debe interpretarse dentro del contexto de que la fila pertenece al conjunto ya revisado por el curador.

No debe asumirse de manera general que todo valor de RegulonDB constituye por sí solo un gold documental.

---

# 22. Evidencia del gold

El gold histórico **no requiere una frase de evidencia anotada** para poder evaluar la recuperación del valor.

La columna `Evidencia` puede permanecer vacía.

Esto implica:

- sí puede calcularse exactitud/precision/recall de valores;
- no puede calcularse automáticamente recall de pasajes curatoriales;
- no puede evaluarse automáticamente si el fragmento producido por el sistema coincide con el fragmento exacto usado por el curador.

Sin embargo:

> **la evidencia sigue siendo obligatoria como salida del sistema para trazabilidad.**

---

# 23. Modalidad del gold

Se mantienen conceptualmente:

```text
texto_explicito
imagen_only
ausente_en_este_paper
inferido_no_dato
```

## 23.1 `texto_explicito`

El curador estableció el valor a partir de contenido textual.

## 23.2 `imagen_only`

El curador estableció el valor originalmente a partir de una figura u otra representación visual.

**No significa que el valor sea necesariamente inaccesible desde TEI/TXT.**

El TEI/TXT puede conservar:

- captions;
- texto asociado;
- referencias;
- contenido extraído de la figura.

Por tanto, estos registros permanecen como targets positivos.

## 23.3 `ausente_en_este_paper`

Si el valor no está en el paper evaluado:

> no es un target positivo de extracción para ese paper.

No se utilizará `PMID_fuente_alternativa`.

## 23.4 `inferido_no_dato`

Si no existe un valor documental recuperable en el paper:

> no es un target positivo normal de extracción.

Puede utilizarse posteriormente para estudiar comportamiento de abstención.

---

# 24. Fila curada

Una fila se considera curada cuando:

1. el curador revisó el paper para esa combinación promotor-propiedad;
2. estableció la modalidad correspondiente;
3. determinó el valor cuando era recuperable;
4. o determinó que no existe un valor recuperable.

No se exige una frase de evidencia almacenada.

---

# 25. Fila evaluable para recuperación de valor

Una fila puede entrar al benchmark positivo cuando:

1. corresponde a una unidad revisada;
2. existe un target curatorial utilizable;
3. la propiedad está dentro del alcance;
4. no permanece bajo adjudicación humana pendiente.

`texto_explicito` e `imagen_only` pueden formar parte del benchmark positivo.

---

# 26. Anti-leakage

## 26.1 Información permitida al extractor

Puede recibir:

```text
paper / TEI / TXT
ID_paper
ID_promotor
Nombre_promotor
Sinonimo_gen_en_este_paper
Propiedad, cuando corresponda
```

## 26.2 Información prohibida

No debe recibir:

```text
Valor_RegulonDB
Sin_dato_en_RegulonDB
Modalidad_origen
Valor_verificado_manualmente
GT_para_referencia
Resultado de evaluación
outputs anteriores usados como target
```

La misma regla se aplica a información recuperada indirectamente mediante cualquier mecanismo futuro.

---

# 27. Separación desarrollo-test

Todo split debe realizarse por paper.

Un PMID no puede aparecer simultáneamente en desarrollo y test.

Las decisiones de:

- prompt;
- normalización;
- retrieval;
- equivalencias;
- reglas;

deben congelarse antes de utilizar el test final.

---

# 28. Evaluación de valores

La evaluación principal compara:

```text
predicción del sistema
vs.
GT_para_referencia
```

por propiedad.

Resultados conceptuales:

```text
EXACT_MATCH
PARTIAL_MATCH
WRONG_VALUE
MISS
EXTRA_VALUE
```

---

# 29. `EXACT_MATCH`

La predicción coincide con el gold después de aplicar únicamente la normalización previamente definida para la propiedad.

---

# 30. `PARTIAL_MATCH`

Se utiliza principalmente cuando:

- el gold contiene múltiples valores;
- el sistema recupera correctamente sólo una parte;
- o existe otra condición de coincidencia parcial explícitamente definida.

No debe confundirse con una tolerancia inventada durante la evaluación.

---

# 31. `WRONG_VALUE`

El sistema produce un valor, pero no coincide con el target curatorial.

---

# 32. `MISS`

Existe un target positivo, pero el sistema no recupera un valor correcto.

Por ejemplo:

```text
Gold: -42
System: NOT_FOUND
```

---

# 33. `EXTRA_VALUE`

El sistema produce uno o más valores adicionales que no forman parte del conjunto esperado.

Es importante especialmente en propiedades con múltiples valores.

---

# 34. Múltiples valores en evaluación

Cuando existen varios valores:

```text
Gold = {A, B}
System = {A, B}
```

es coincidencia completa.

```text
Gold = {A, B}
System = {A}
```

es recuperación parcial.

```text
Gold = {A}
System = {A, C}
```

contiene un valor correcto y un valor extra.

Los valores deben compararse como conjuntos después de normalización, no como una sola cadena concatenada.

---

# 35. Evaluación de TSS

## 35.1 Métrica primaria

Exact match después de normalización previamente congelada.

## 35.2 Métricas secundarias

Cuando la representación sea una posición numérica comparable, podrán reportarse:

```text
±1 nt
±3 nt
```

como análisis secundarios.

Nunca deben sustituir silenciosamente al exact match.

## 35.3 Representaciones heterogéneas

Coordenadas genómicas, posiciones relativas y designación `+1` no deben compararse como si fueran el mismo tipo de número sin una regla explícita de conversión.

---

# 36. Evaluación de cajas -10 / -35

La comparación primaria se realiza sobre la secuencia normalizada.

Normalizaciones permitidas deben congelarse antes del test.

No se corregirán nucleótidos por similitud.

No se aplicará por ahora un filtro de longitud excluyente en scoring.

---

# 37. Evaluación de sigma

La comparación primaria utilizará normalización tipográfica inequívoca.

Las equivalencias biológicas Rpo/sigma quedan fuera hasta que exista una tabla explícita y congelada.

---

# 38. Recall

El recall de valores puede calcularse con los datos curatoriales aunque no exista una frase de evidencia almacenada.

Conceptualmente:

```text
Recall =
valores positivos correctamente recuperados
/
valores positivos del gold
```

Debe reportarse por propiedad.

---

# 39. Recall total y estratificado por modalidad

Se reportarán al menos:

## 39.1 Recall total bajo TEI/TXT

Pregunta:

> De todos los valores curatoriales positivos, ¿qué proporción recupera el sistema usando la representación realmente disponible?

## 39.2 Recall en `texto_explicito`

Pregunta:

> ¿Qué proporción recupera cuando el curador identificó originalmente el dato en texto?

## 39.3 Recall en `imagen_only`

Pregunta:

> ¿Qué proporción de los valores originalmente identificados visualmente puede recuperarse indirectamente desde la representación TEI/TXT?

`imagen_only` no debe excluirse automáticamente del recall total.

---

# 40. Precision y F1

La evaluación podrá incluir:

```text
precision
recall
F1
```

por propiedad.

La definición exacta de TP/FP/FN deberá respetar:

- múltiples valores;
- abstenciones;
- valores extras;
- modalidad.

---

# 41. Exact row accuracy

Puede reportarse además:

> proporción de unidades `paper × promotor × propiedad` cuya predicción completa coincide exactamente con el gold.

Es una métrica complementaria.

No sustituye precision/recall por valor.

---

# 42. Evidencia producida por el sistema

Aunque no exista gold de evidencia, todo `EXTRACTED` debe proporcionar evidencia.

La evidencia podrá utilizarse para:

- revisión humana;
- análisis de errores;
- demostración de trazabilidad;
- auditoría manual de una muestra;
- estudiar qué tipos de fuente utiliza el sistema.

No se calculará automáticamente `evidence recall` contra un gold inexistente.

---

# 43. Tipos de fuente de evidencia del sistema

El sistema podrá etiquetar:

```text
body_text
table
figure_caption
figure_reference
figure_associated_text
other
```

Esto permitirá estudiar, por ejemplo, cómo se recuperan casos curatoriales `imagen_only`.

---

# 44. Validación del resultado

Antes de comparar con el gold debe validarse que la salida cumpla el contrato.

Ejemplos:

- `EXTRACTED` requiere al menos un valor;
- todo valor aceptado requiere evidencia;
- un estado de abstención no debe contener valores aceptados;
- valores ambiguos deben mantenerse separados;
- la estructura específica de TSS/cajas/sigma debe ser coherente.

Validación no equivale a evaluación.

---

# 45. Interfaz — requisito general

El sistema tendrá una interfaz MVP.

Su objetivo será permitir:

1. seleccionar/cargar un artículo;
2. introducir contexto del promotor;
3. ejecutar extracción;
4. revisar resultados;
5. revisar evidencia;
6. opcionalmente comparar contra el gold en casos benchmark.

---

# 46. Entradas de la interfaz

P0:

```text
TXT o TEI/XML
PMID
Promoter name
Promoter ID, si existe
Gene / historical alias, opcional
```

---

# 47. Resultados de la interfaz

Para cada propiedad:

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

Sólo deben mostrarse los campos aplicables.

---

# 48. Visualización de evidencia

Idealmente la interfaz utilizará una vista dividida:

```text
ARTICLE | EXTRACTION
```

y permitirá resaltar el fragmento de evidencia correspondiente a una propiedad.

---

# 49. Benchmark en interfaz

El gold debe permanecer oculto durante la extracción.

Después de guardar la predicción puede habilitarse:

```text
Show evaluation
```

La vista puede mostrar:

| Property | System | Curated reference | Result |
|---|---|---|---|
| TSS | -42 | -42 | MATCH |
| -10 | TATAAT | TATAAT | MATCH |
| -35 | NOT_FOUND | TTGTTA | MISS |
| sigma | sigma32 | sigma32 | MATCH |

---

# 50. Errores técnicos vs. estados científicos

La interfaz debe distinguir errores técnicos como:

```text
FILE_NOT_READABLE
INVALID_XML
EMPTY_DOCUMENT
MODEL_ERROR
TIMEOUT
INTERNAL_ERROR
```

de estados científicos como:

```text
NOT_FOUND
INSUFFICIENT_EVIDENCE
AMBIGUOUS
```

---

# 51. Requisitos funcionales

## FR-01 — Cargar documento

El sistema debe aceptar al menos TXT y TEI/XML.

## FR-02 — Identificar paper

El sistema debe conservar el PMID o identificador documental.

## FR-03 — Identificar promotor

El sistema debe recibir identidad suficiente del promotor.

## FR-04 — Alias opcional

El sistema debe poder recibir un sinónimo histórico.

## FR-05 — Extraer cuatro propiedades

Debe evaluar TSS, -10, -35 y sigma de forma independiente.

## FR-06 — Soportar múltiples valores

Cada propiedad debe poder devolver múltiples valores.

## FR-07 — Producir evidencia

Todo valor aceptado debe incluir evidencia.

## FR-08 — Producir localización

La salida debe registrar localización cuando la representación lo permita.

## FR-09 — Abstenerse

El sistema debe producir un estado explícito cuando no pueda establecer un valor.

## FR-10 — Conservar incertidumbre

Los calificadores científicos deben preservarse.

## FR-11 — Output estructurado

La salida debe ser procesable programáticamente.

## FR-12 — Validar salida

Debe comprobarse consistencia del contrato antes de evaluación.

## FR-13 — Ejecutar benchmark sin leakage

La referencia curatorial no debe formar parte del contexto de extracción.

## FR-14 — Comparar contra gold

Después de la predicción, el sistema debe poder comparar programáticamente el resultado con el target.

## FR-15 — Mostrar evidencia

La interfaz debe permitir revisar evidencia junto con el valor.

## FR-16 — Mantener historial reproducible

Cada ejecución debería conservar al menos:

```text
paper
promoter
timestamp
versión del sistema/prompt
resultado
```

---

# 52. Requisitos no funcionales iniciales

## NFR-01 — Trazabilidad

Toda afirmación positiva debe ser revisable.

## NFR-02 — Reproducibilidad

Debe poder conocerse qué versión produjo un resultado.

## NFR-03 — Claridad

La interfaz debe distinguir valores, candidatos y abstenciones.

## NFR-04 — Legibilidad

Las secuencias y valores deben mostrarse de forma clara.

## NFR-05 — Accesibilidad básica

Los estados no deben comunicarse únicamente mediante color.

## NFR-06 — Auditabilidad

La evaluación debe poder reconstruirse a partir de predicción, gold y reglas de normalización.

## NFR-07 — Separación de responsabilidades

Extracción, validación y evaluación deben permanecer conceptualmente separadas.

---

# 53. Casos mínimos de prueba

El sistema debe incluir al menos casos que cubran:

1. valor explícito en texto;
2. propiedad no encontrada;
3. propiedad mencionada sin valor suficiente;
4. múltiples valores para un mismo promotor;
5. múltiples promotores en un mismo paper;
6. ambigüedad de asociación;
7. TSS relativo con ancla;
8. `+1` transcripcional;
9. coordenada genómica de TSS;
10. caja `putative`;
11. consenso general que no debe asignarse;
12. sigma mencionado pero no asociado al promotor;
13. múltiples sigmas;
14. caso curatorial `imagen_only` recuperable desde TEI/TXT;
15. caso con referencia a figura pero sin valor textual suficiente;
16. discordancia entre predicción y gold;
17. valor extra;
18. múltiples valores parcialmente recuperados.

---

# 54. Criterios de aceptación del sistema

El sistema cumple el MVP cuando:

1. puede procesar TXT o TEI/XML;
2. recibe un promotor identificado;
3. produce resultados independientes para las cuatro propiedades;
4. todo valor extraído contiene evidencia;
5. puede devolver múltiples valores;
6. puede abstenerse;
7. distingue ambigüedad de ausencia de hallazgo;
8. no utiliza targets de RegulonDB/gold durante la extracción;
9. genera salida estructurada;
10. puede evaluarse programáticamente;
11. reporta resultados por propiedad;
12. puede mostrar resultados y evidencia en una interfaz;
13. el modo benchmark oculta el gold hasta después de la predicción.

---

# 55. Riesgos

## R-01 — Leakage

Mitigación:

- targets ocultos;
- separación por paper;
- comparación sólo posterior.

## R-02 — Memorización de RegulonDB

Mitigación:

- exigir evidencia del paper;
- análisis closed-book opcional;
- evaluación prospectiva futura.

## R-03 — Dependencia del TEI/TXT

Mitigación:

- distinguir fallos de representación de fallos de interpretación;
- analizar `source_type`;
- reportar `imagen_only` por separado.

## R-04 — Gold incompleto

Mitigación:

- documentar qué puede y qué no puede medir el benchmark;
- no inventar evidencia curatorial ausente.

## R-05 — Casos ambiguos

Mitigación:

- `AMBIGUOUS`;
- exclusión del benchmark final si el propio curador no puede adjudicar el caso.

## R-06 — Sobreajuste al subset

Mitigación:

- tratarlo como conjunto de trabajo provisional;
- congelar reglas antes de test final.

## R-07 — Reglas de normalización excesivas

Mitigación:

- normalización conservadora;
- tablas explícitas;
- no ajustar mirando el target.

## R-08 — Arquitectura excesiva

Mitigación:

- incorporar componentes técnicos sólo cuando exista una necesidad demostrada.

---

# 56. Supuestos

1. El promotor ya está identificado en la Parte 1.
2. El paper suministrado es el documento que se desea analizar.
3. Los valores objetivo permanecen ocultos al extractor.
4. El gold refleja una revisión curatorial previa.
5. La evidencia del curador no está disponible sistemáticamente.
6. TEI/TXT puede contener información procedente de captions o figuras.
7. `imagen_only` describe el proceso curatorial, no la accesibilidad técnica.
8. El gold completo continúa en construcción.
9. El curador mantiene la decisión científica final.

---

# 57. Decisiones cerradas

- nombre del proyecto: `promoter-ai-extraction`;
- Parte 1 = extracción guiada;
- input conceptual = paper + promotor identificado;
- cuatro propiedades iniciales;
- TEI/TXT como representaciones iniciales;
- paper como unidad de muestreo;
- paper × promotor × propiedad como unidad de evaluación;
- evidencia obligatoria en output positivo;
- evidencia curatorial no obligatoria para scoring del valor;
- múltiples valores permitidos;
- abstención obligatoria cuando corresponda;
- gold oculto durante extracción;
- `GT_para_referencia` como target operativo del subset actual;
- `imagen_only` permanece como target positivo;
- recall total y recall por modalidad;
- `PMID_fuente_alternativa` fuera del contrato;
- si un valor está ausente del paper, no se cuenta como target positivo;
- equivalencias Rpo/sigma pendientes;
- no se congela aún una longitud mínima de caja;
- interfaz MVP incluida;
- integración completa con RegulonDB fuera del MVP.

---

# 58. Decisiones abiertas antes del test final

1. revisar los casos de cajas extremadamente cortas del gold;
2. congelar normalizaciones definitivas por propiedad;
3. definir equivalencias sigma adicionales, si son necesarias;
4. definir representación final de múltiples valores en el gold;
5. definir tratamiento final de `INVALID_CANDIDATE`;
6. congelar splits desarrollo/test;
7. congelar métricas primarias/secundarias;
8. determinar el conjunto final de filas adjudicadas;
9. definir cualquier análisis manual de evidencia del sistema;
10. decidir cuándo una versión está lista para evaluación prospectiva.

---

# 59. Documentos derivados

Este documento debe complementarse con documentos especializados:

```text
docs/
├── project-requirements.md
├── extraction-contract.md
├── gold-set-contract.md
├── evaluation-contract.md
└── ux-requirements.md
```

Este archivo corresponde a:

```text
docs/project-requirements.md
```

y funciona como la referencia consolidada de requisitos antes de diseñar arquitectura e implementación.

---

# 60. Principio rector

> **`promoter-ai-extraction` debe extraer únicamente aquello que pueda sustentarse en la representación disponible del paper, mostrar la evidencia que justifica cada valor y abstenerse cuando la asociación entre paper, promotor, propiedad y valor no pueda establecerse de forma responsable.**
