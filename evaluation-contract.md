# Evaluation Contract — `promoter-ai-extraction`

**Versión:** v0.1  
**Estado:** contrato de evaluación provisional, basado en el subset curatorial disponible  
**Dataset de trabajo:** `SUBSET_GOLD(2).xlsx`  
**Unidad de evaluación:** `paper × promotor × propiedad`

---

## 1. Propósito

Este documento define cómo se compararán las salidas de `promoter-ai-extraction` contra la referencia curatorial disponible.

La evaluación responde principalmente a la pregunta:

> **Dado un paper y un promotor identificado, ¿qué proporción de los valores curatoriales de TSS, caja -10, caja -35 y factor sigma puede recuperar correctamente el sistema a partir de la representación TEI/TXT disponible?**

El contrato se centra en la recuperación correcta de **valores**. El gold histórico no contiene de forma sistemática las frases de evidencia utilizadas por el curador, por lo que la evidencia producida por el sistema se utilizará como requisito de trazabilidad, pero no como target automático de comparación en esta primera evaluación.

---

## 2. Fuente del gold

En el subset actual, la referencia operativa se encuentra en:

```text
GT_para_referencia
```

La regla utilizada en el archivo es:

```text
si Valor_verificado_manualmente tiene valor:
    GT_para_referencia = Valor_verificado_manualmente
si no:
    GT_para_referencia = Valor_RegulonDB
```

Para este proyecto, esta regla se acepta como referencia operativa porque las filas incluidas corresponden al conjunto que ya fue revisado por el curador.

Por tanto, un `Valor_verificado_manualmente` vacío en este subset no se interpreta automáticamente como “fila no revisada”.

---

## 3. Dataset de trabajo actual

El subset disponible contiene:

- **329 registros**;
- **76 papers**;
- **130 promotores**.

Distribución por propiedad:

| Propiedad | Registros |
|---|---:|
| Caja -10 | 101 |
| TSS | 98 |
| Caja -35 | 86 |
| Factor sigma | 44 |

Distribución por `Modalidad_origen`:

| Modalidad | Registros |
|---|---:|
| `texto_explicito` | 133 |
| `imagen_only` | 196 |

Este archivo es un subset de trabajo y no debe confundirse con el gold final completo.

---

## 4. Qué representa `Modalidad_origen`

`Modalidad_origen` describe cómo el curador identificó originalmente el dato.

### `texto_explicito`

El curador determinó el valor a partir de contenido textual del paper.

### `imagen_only`

El curador determinó el valor mediante una figura, gel, mapa u otra representación visual.

La categoría `imagen_only` **no significa automáticamente que el valor sea inaccesible al sistema**.

La representación TEI/TXT puede conservar:

- captions;
- texto asociado con figuras;
- referencias a figuras;
- etiquetas o fragmentos extraídos durante la conversión;
- información equivalente mencionada en otra parte del texto.

Por ello, los registros `imagen_only` permanecen como targets positivos del benchmark y se reportan también como un estrato separado.

---

## 5. Fuentes de entrada del sistema

La evaluación inicial utilizará como fuente documental disponible:

```text
TEI/XML
TXT derivado del TEI/XML
```

No se asume acceso directo a las imágenes originales de las figuras.

El sistema puede utilizar cualquier texto legítimamente presente en la representación suministrada, incluyendo:

- cuerpo del artículo;
- captions;
- tablas representadas textualmente;
- referencias a figuras;
- texto asociado con figuras recuperado por el proceso PDF → TEI/TXT.

---

## 6. Información que el extractor puede recibir

El extractor puede recibir:

- `ID_paper` / PMID;
- documento TEI/TXT;
- `ID_promotor`;
- `Nombre_promotor`;
- `Sinonimo_gen_en_este_paper`, cuando exista;
- propiedad, si la ejecución se realiza por propiedad.

---

## 7. Información que el extractor no puede recibir

Durante la generación de la predicción deben permanecer ocultos:

- `Valor_RegulonDB`;
- `Valor_verificado_manualmente`;
- `GT_para_referencia`;
- `Modalidad_origen`;
- etiquetas de evaluación;
- resultados previos del sistema utilizados como respuesta;
- cualquier campo que revele directa o indirectamente el target.

La comparación contra el gold ocurre **después** de generar y guardar la predicción.

---

## 8. Universo positivo de evaluación

Una fila entra al benchmark positivo de extracción de valor cuando:

1. identifica un `paper × promotor × propiedad`;
2. tiene un `GT_para_referencia` utilizable;
3. el curador determinó que existe un valor correspondiente en el paper;
4. la fila no está pendiente de adjudicación curatorial.

En el subset actual, las filas fueron seleccionadas precisamente porque contienen un valor de referencia derivable y pertenecen a `texto_explicito` o `imagen_only`.

---

## 9. Casos sin valor documental

Si en el conjunto completo aparecen categorías como:

```text
ausente_en_este_paper
inferido_no_dato
```

no se incluirán en el denominador del recall de valores positivos.

La regla de alcance del proyecto es:

> **Si el valor no está sustentado en el paper evaluado, no se considera un target positivo de extracción para ese paper.**

No se buscará un `PMID_fuente_alternativa` como parte del benchmark principal.

Estos casos podrían conservarse en análisis auxiliares posteriores, pero no forman parte del target positivo principal.

---

# 10. Representación de los valores

Antes de comparar, gold y predicción deben transformarse mediante reglas de normalización previamente congeladas.

La normalización debe ser:

- reproducible;
- global;
- independiente de la fila evaluada;
- independiente del valor esperado;
- suficientemente conservadora para no convertir valores biológicamente diferentes en equivalentes.

---

# 11. Comparación de TSS

## 11.1 Situación del subset actual

Los 98 valores TSS del subset actual están representados como posiciones enteras relativas, por ejemplo:

```text
-145
-42
-12
0
```

Por tanto, la evaluación primaria del subset puede realizarse mediante comparación numérica exacta.

## 11.2 Normalización primaria

Ejemplos equivalentes:

```text
"-42" -> -42
-42    -> -42
```

No debe alterarse el significado de `0` ni de otros valores mediante conocimiento externo.

## 11.3 Exact match primario

Una predicción TSS es correcta cuando el valor relativo normalizado coincide exactamente con el valor normalizado del gold.

```text
gold = -42
prediction = -42
=> MATCH
```

## 11.4 Tolerancias secundarias

Podrán reportarse como análisis secundarios:

```text
±1 nt
±3 nt
```

Estas tolerancias nunca sustituyen al exact match primario ni se utilizan para corregir silenciosamente la predicción.

## 11.5 Representaciones adicionales

El contrato de extracción permite TSS expresados como coordenadas genómicas, designación `+1` u otras formas documentales válidas.

Sin embargo, si el gold de una fila sólo contiene una posición relativa, una coordenada absoluta no se declarará automáticamente equivalente utilizando RegulonDB o el genoma.

Para contar como match en el benchmark actual, el sistema deberá producir una representación comparable con el target disponible.

---

# 12. Comparación de cajas -10 y -35

## 12.1 Normalización permitida

Se permite:

- convertir a mayúsculas;
- eliminar espacios inequívocamente tipográficos;
- eliminar saltos de línea dentro de una misma secuencia;
- retirar separadores puramente tipográficos cuando la interpretación sea inequívoca.

Ejemplo observado en el subset:

```text
TT\nGTTA -> TTGTTA
```

No se permite:

- corregir nucleótidos por similitud con un consenso;
- reconstruir bases desde el genoma;
- completar la secuencia utilizando TSS o sigma;
- sustituir una secuencia por otra biológicamente más plausible.

## 12.2 Longitud

La longitud de una secuencia **no se utilizará como criterio de scoring en esta versión del contrato**.

El subset contiene valores curatoriales tan cortos como:

```text
GC
GG
```

Por tanto, no se rechazará automáticamente una predicción por tener menos de 3 nt mientras el gold curatorial contenga ese valor.

La validez biológica o representación exacta de estos casos debe revisarse por separado y no debe resolverse modificando el scoring a posteriori.

## 12.3 Múltiples valores

El subset contiene al menos un caso representado como:

```text
TAATAA + TATAAT
```

Para evaluación debe interpretarse conceptualmente como un conjunto:

```text
{TAATAA, TATAAT}
```

El delimitador textual no forma parte del valor biológico.

---

# 13. Comparación de factor sigma

## 13.1 Valores observados actualmente

En el subset aparecen:

```text
sigma70
sigma38
sigma54
sigma24
sigma28
```

## 13.2 Normalización tipográfica

Se permiten equivalencias inequívocas como:

```text
σ32
Sigma32
sigma 32
sigma32
```

normalizadas a:

```text
sigma32
```

La misma regla se aplica a otras denominaciones numéricas claras.

## 13.3 Equivalencias biológicas no congeladas

No se utilizarán por ahora equivalencias como:

```text
RpoS <-> sigma38
RpoH <-> sigma32
RpoN <-> sigma54
```

hasta definir una tabla explícita y revisada contra el gold completo.

---

# 14. Múltiples valores: comparación de conjuntos

Cuando una fila contenga más de un valor válido, gold y predicción se interpretarán como conjuntos normalizados.

Ejemplo:

```text
gold       = {TAATAA, TATAAT}
prediction = {TAATAA, TATAAT}
```

Resultado:

```text
EXACT_SET_MATCH
```

Si:

```text
gold       = {TAATAA, TATAAT}
prediction = {TAATAA}
```

la predicción es parcialmente correcta pero incompleta.

Para métricas a nivel de valor:

```text
TP = |gold ∩ prediction|
FP = |prediction - gold|
FN = |gold - prediction|
```

En el ejemplo:

```text
TP = 1
FP = 0
FN = 1
```

Además del scoring a nivel de valor, se reportará si la fila completa obtuvo `EXACT_SET_MATCH`.

---

# 15. Clasificación básica del resultado

Para cada fila evaluable se pueden derivar las siguientes categorías de comparación.

## `EXACT_MATCH`

La predicción contiene exactamente el valor esperado.

Para múltiples valores, el conjunto completo coincide.

## `PARTIAL_MATCH`

Aplica únicamente cuando existen múltiples valores y la predicción recupera una parte correcta del conjunto, pero no todo el conjunto.

## `WRONG_VALUE`

El sistema produce uno o más valores que no coinciden con el gold y no recupera correctamente el target completo.

## `MISS`

Existe un target positivo en el gold, pero el sistema no devuelve ningún valor aceptado.

Puede corresponder a estados del extractor como:

```text
NOT_FOUND
INSUFFICIENT_EVIDENCE
UNSUPPORTED_MODALITY
AMBIGUOUS
```

Para el recall global de valores, estos casos cuentan como valores no recuperados.

## `EXTRA_VALUE`

El sistema recupera correctamente uno o más valores del gold pero añade valores no sustentados por el gold.

Esto se refleja como FP a nivel de valor y evita considerar la fila como exact set match.

---

# 16. Relación entre status del extractor y scoring

El `status` generado por el sistema describe su conclusión documental.

El scoring se calcula posteriormente.

Ejemplo:

```text
gold = -42
system.status = NOT_FOUND
system.values = []
```

Evaluación:

```text
MISS
FN = 1
```

Ejemplo:

```text
gold = -42
system.status = EXTRACTED
system.values = [-41]
```

Evaluación exacta:

```text
WRONG_VALUE
FP = 1
FN = 1
```

En una métrica secundaria TSS ±1 podría registrarse además como match tolerante, pero no como exact match.

---

# 17. Recall principal

Para una propiedad determinada:

```text
Recall = TP / (TP + FN)
```

Interpretación:

> De todos los valores que el curador determinó que estaban presentes en los papers evaluados, ¿qué proporción recuperó correctamente el sistema?

La ausencia de evidencia textual anotada por el curador no impide calcular este recall.

---

# 18. Precision

A nivel de valores predichos dentro del universo evaluable:

```text
Precision = TP / (TP + FP)
```

Una predicción incorrecta genera un FP.

Cuando además deja sin recuperar el valor esperado, genera simultáneamente un FN.

Esta precisión evalúa la exactitud de los valores afirmados dentro de los casos positivos disponibles.

El subset actual no contiene de forma sistemática casos negativos documentales; por ello, no debe interpretarse esta métrica como una caracterización completa de la tasa de falsas afirmaciones sobre papers sin ningún valor target.

---

# 19. F1

Cuando precision y recall sean pertinentes:

```text
F1 = 2 * Precision * Recall / (Precision + Recall)
```

Se reportará por propiedad antes de considerar una agregación global.

---

# 20. Exact row accuracy

Además de las métricas a nivel de valor, se reportará:

```text
Exact row accuracy = filas con EXACT_MATCH / filas evaluables
```

Para filas con múltiples valores, sólo cuenta como exacta si el conjunto completo coincide y no existen valores adicionales.

Esta métrica responde:

> ¿En qué proporción de unidades `paper × promotor × propiedad` produjo el sistema exactamente la respuesta curatorial esperada?

---

# 21. Recall estratificado por modalidad

Se reportarán al menos tres recalls:

## 21.1 Recall total bajo TEI/TXT

Incluye todos los targets positivos del benchmark, independientemente de `Modalidad_origen`.

Responde:

> ¿Qué proporción del trabajo curatorial puede recuperar el sistema utilizando realmente TEI/TXT como entrada?

## 21.2 Recall en `texto_explicito`

Se calcula únicamente sobre filas clasificadas por el curador como `texto_explicito`.

Responde:

> ¿Qué tan bien recupera el sistema valores que el curador identificó textualmente?

## 21.3 Recall en `imagen_only`

Se calcula únicamente sobre filas clasificadas como `imagen_only`.

Responde:

> ¿Qué fracción de la información que el curador obtuvo originalmente de figuras queda aun recuperable desde la representación TEI/TXT disponible?

No se asume que este recall sea cero ni que todos esos casos sean inalcanzables.

---

# 22. Reporte por propiedad

Las métricas principales deben presentarse por separado para:

```text
TSS
Caja -10
Caja -35
Factor sigma
```

Como mínimo, para cada propiedad:

- número de targets;
- número de predicciones con valor;
- TP;
- FP;
- FN;
- precision;
- recall;
- F1;
- exact row accuracy;
- recall por `Modalidad_origen`.

Una única métrica global no sustituye este desglose.

---

# 23. Agregación global

Puede reportarse una agregación global como resumen secundario.

Debe indicarse claramente si se utiliza:

- micro-average;
- macro-average por propiedad.

La evaluación primaria seguirá mostrando cada propiedad de forma independiente.

---

# 24. Evidencia producida por el sistema

Aunque el gold no contenga de manera sistemática la frase curatorial de evidencia, toda salida `EXTRACTED` debe incluir evidencia localizable producida por el sistema.

Conceptualmente:

```text
value
status
evidence
source_type
source_location
```

La evidencia sirve para:

- trazabilidad;
- revisión humana;
- análisis de errores;
- uso futuro por curadores.

No se calculará por ahora un `evidence recall` automático contra el gold, porque no existe una anotación curatorial equivalente completa.

Puede realizarse posteriormente una evaluación manual sobre una muestra.

---

# 25. Source type de la evidencia del sistema

Cuando sea posible, la salida puede clasificar su evidencia como:

```text
body_text
table
figure_caption
figure_reference
figure_associated_text
other
```

Esto permitirá analizar, por ejemplo, qué proporción de los registros curatoriales `imagen_only` fueron recuperados desde captions o texto asociado a figuras.

---

# 26. Abstención

El sistema debe conservar la capacidad de abstenerse mediante estados como:

```text
NOT_FOUND
INSUFFICIENT_EVIDENCE
UNSUPPORTED_MODALITY
AMBIGUOUS
```

Sin embargo, en una fila con target positivo del benchmark, una abstención implica que el valor no fue recuperado y por tanto contribuye como FN al recall de valor.

Esto no significa que la abstención sea conceptualmente incorrecta: puede ser el comportamiento responsable dadas las limitaciones de la representación disponible.

Por ello, el análisis de errores deberá distinguir entre:

- valor perdido pese a evidencia textual disponible;
- información originalmente visual no recuperada desde TEI/TXT;
- evidencia incompleta;
- asociación ambigua;
- otras limitaciones documentales.

---

# 27. Split experimental

Los conjuntos de desarrollo y prueba deben separarse a nivel de paper.

Nunca deben existir filas del mismo PMID en ambos conjuntos.

```text
paper A -> development o test, nunca ambos
```

Todos los ajustes de:

- prompts;
- normalización;
- parsing de múltiples valores;
- retrieval;
- reglas de matching;

deben congelarse antes de ejecutar el test final.

---

# 28. Dependencia entre filas

Varias filas pueden provenir del mismo paper.

Por ello, los intervalos de confianza y procedimientos de bootstrap deben agrupar por paper, no por fila individual.

Esto evita tratar como independientes observaciones que comparten artículo y contexto documental.

---

# 29. Casos curatoriales ambiguos

Si el gold completo contiene una fila marcada como:

```text
REQUIERE_REVISION
```

no debe formar parte del benchmark principal hasta ser adjudicada.

Puede conservarse en un conjunto de casos difíciles para análisis cualitativo.

---

# 30. Qué no se evaluará automáticamente en v0.1

Por ausencia de referencia curatorial específica, no se calcularán como métricas automáticas principales:

- exactitud de la frase de evidencia;
- recall de pasajes;
- coincidencia de ubicación de evidencia;
- exactitud de `source_type`;
- exactitud de calificadores lingüísticos;
- técnica experimental, salvo que se defina después un benchmark específico.

Estos elementos siguen siendo importantes para trazabilidad y análisis manual.

---

# 31. Salida mínima del reporte de evaluación

Ejemplo conceptual:

```text
PROPERTY: TSS
Targets: 98
TP: ...
FP: ...
FN: ...
Precision: ...
Recall: ...
F1: ...
Exact row accuracy: ...
Recall texto_explicito: ...
Recall imagen_only: ...
Exact match: ...
±1 nt recall: ...
±3 nt recall: ...
```

Para cajas y sigma se omiten las tolerancias posicionales.

---

# 32. Reglas cerradas provisionalmente

1. `GT_para_referencia` es el target operativo del subset actual.
2. La ausencia de evidencia curatorial no impide calcular recall de valores.
3. La evidencia sigue siendo obligatoria para una salida `EXTRACTED` del sistema.
4. `imagen_only` permanece como target positivo.
5. `imagen_only` no significa automáticamente inaccesible desde TEI/TXT.
6. Se reportará recall total, `texto_explicito` e `imagen_only`.
7. `ausente_en_este_paper` e `inferido_no_dato` no entran al denominador del recall positivo.
8. No se utilizará `PMID_fuente_alternativa` en el benchmark principal.
9. Las cuatro propiedades se evaluarán por separado.
10. TSS utiliza exact match como métrica primaria en el subset actual.
11. TSS ±1 y ±3 pueden reportarse como métricas secundarias.
12. Cajas se normalizan sólo tipográficamente.
13. La longitud de cajas no se usa como regla de scoring en esta versión.
14. Los múltiples valores se comparan como conjuntos.
15. Sigma utiliza inicialmente sólo normalizaciones tipográficas inequívocas.
16. Las equivalencias Rpo/sigma quedan pendientes.
17. El split y el bootstrap se realizan por paper.
18. Las predicciones se generan antes de mostrar o consultar el gold.

---

# 33. Decisiones pendientes antes de congelar el test final

1. Revisar los casos curatoriales de cajas extremadamente cortas, especialmente los valores de 2 nt observados en el subset.
2. Confirmar el parser definitivo para múltiples valores en el gold completo.
3. Revisar si existen múltiples TSS codificados de formas adicionales.
4. Definir equivalencias biológicas de sigma si aparecen formas `Rpo*`.
5. Confirmar la partición development/test por paper.
6. Definir qué versión del gold queda congelada para la evaluación final.
7. Decidir si se realizará una revisión manual de una muestra de evidencias producidas por el sistema.
8. Definir intervalos de confianza y número de réplicas de bootstrap.

---

# 34. Principio rector de evaluación

> **El sistema se evalúa contra lo que el curador determinó que puede obtenerse del paper, no contra lo que sería biológicamente plausible ni contra un valor memorizado de RegulonDB. La evaluación primaria mide recuperación correcta de valores; la evidencia generada por el sistema conserva la trazabilidad necesaria para que un humano pueda revisar la afirmación.**
