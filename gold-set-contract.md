# Gold Set Contract - `promoter-ai-extraction`

**Versión:** 0.1  
**Estado:** contrato metodológico en revisión  
**Dataset de trabajo actual:** `SUBSET_GOLD(2).xlsx`  
**Unidad de evaluación:** `paper x promotor x propiedad`

---

# 1. Propósito

Este documento define cómo se interpretará y utilizará el conjunto curado de referencia de `promoter-ai-extraction` para evaluar la extracción de propiedades de promotores bacterianos desde literatura científica.

El contrato se diseña a partir de los datos que existen realmente en el proceso curatorial. No exige reconstruir evidencia textual que el curador no conservó durante la revisión original.

El gold debe permitir responder principalmente:

> **Dado un paper y un promotor, ¿el sistema recupera correctamente los valores que el curador determinó que pueden obtenerse de ese paper para TSS, caja -10, caja -35 y factor sigma?**

La evaluación del valor extraído y la evaluación de la evidencia producida por el sistema son dimensiones diferentes.

---

# 2. Principios del contrato

1. La referencia principal es la **revisión realizada por el curador sobre el paper**.
2. RegulonDB se conserva como referencia histórica y de comparación, pero no debe proporcionarse al extractor como respuesta objetivo.
3. No se exigirá evidencia textual retrospectiva al curador si esa evidencia no fue almacenada durante la revisión.
4. El sistema sí debe producir evidencia y localización cuando afirme un valor, porque la trazabilidad sigue siendo un requisito del producto.
5. La ausencia de evidencia anotada en el gold impide evaluar automáticamente el grounding contra un pasaje humano de referencia, pero **no impide calcular recall, precision ni exactitud del valor**.
6. `Modalidad_origen` describe cómo el curador identificó originalmente el dato; no determina por sí sola si el valor es recuperable desde TEI/TXT.
7. Las filas cuyo dato no se encuentra en el paper no constituyen targets positivos de extracción para ese paper.
8. Las propiedades se evalúan por separado.
9. Las particiones de desarrollo y prueba deben hacerse a nivel de paper.
10. Las reglas de normalización deben congelarse antes de evaluar el test final.

---

# 3. Fuente de datos actual

El archivo de trabajo utilizado para este contrato es:

```text
SUBSET_GOLD(2).xlsx
```

La hoja contiene un encabezado descriptivo y **329 registros curatoriales**.

Resumen actual:

| Característica | Valor |
|---|---:|
| Registros | 329 |
| Papers | 76 |
| Promotores | 130 |
| `texto_explicito` | 133 |
| `imagen_only` | 196 |

Distribución por propiedad:

| Propiedad | Registros |
|---|---:|
| Caja -10 | 101 |
| TSS | 98 |
| Caja -35 | 86 |
| Factor sigma | 44 |

Este archivo es un **subset de trabajo**, no necesariamente el gold final completo del proyecto.

---

# 4. Unidad del gold

Cada fila representa conceptualmente:

```text
paper x promotor x propiedad
```

Las propiedades iniciales son:

```text
TSS
Caja -10
Caja -35
Factor sigma
```

La identidad de una fila no debe reducirse sólo al PMID, porque un mismo paper puede contener varios promotores y un mismo promotor puede contribuir con varias propiedades.

---

# 5. Columnas actuales del Excel

El subset contiene las siguientes columnas:

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

# 6. Clasificación de columnas por función

| Columna | Papel en el proyecto | ¿Puede entrar al extractor? | ¿Se usa en evaluación? |
|---|---|---:|---:|
| `Fila_origen` | trazabilidad hacia el archivo fuente | No necesario | Sólo auditoría |
| `ID_promotor` | identidad del promotor | Sí | Sí |
| `Nombre_promotor` | identidad/contexto | Sí | Sí |
| `Sinonimo_gen_en_este_paper` | contexto para localizar la entidad | Sí, si existe | Puede usarse en análisis |
| `ID_paper` | identidad del documento | Sí | Sí |
| `Propiedad` | propiedad evaluada | Sí o implícita | Sí |
| `Valor_RegulonDB` | referencia histórica | **No** | Comparación secundaria |
| `Sin_dato_en_RegulonDB` | metadato histórico | **No** | Análisis secundario |
| `Modalidad_origen` | clasificación curatorial | **No** | Sí, para estratificar resultados |
| `Valor_verificado_manualmente` | corrección/valor curatorial | **No** | Sí |
| `GT_para_referencia` | target operativo actual | **No** | **Sí** |
| `Año_confirmado` | metadato | No | Opcional |
| `Técnica_confirmada_manualmente` | metadato científico | No como target | Análisis secundario |
| `Evidencia` | evidencia curatorial opcional | No | No requerida para la evaluación principal |

---

# 7. Definición operativa del target

En el subset actual, `GT_para_referencia` se construyó mediante la regla:

```text
si Valor_verificado_manualmente tiene valor:
    GT_para_referencia = Valor_verificado_manualmente
si no:
    GT_para_referencia = Valor_RegulonDB
```

En los datos actuales:

```text
121 filas -> Valor_verificado_manualmente disponible
208 filas -> fallback a Valor_RegulonDB
329 filas -> GT_para_referencia no vacío
```

Este fallback sólo es metodológicamente válido bajo la siguiente interpretación del proceso curatorial:

> **Las filas incluidas en el subset ya fueron revisadas por el curador; cuando `Valor_verificado_manualmente` está vacío, el curador no requirió sustituir el valor de RegulonDB para esa fila.**

Por tanto, para este subset:

```text
GT_para_referencia
```

se utilizará como **target curatorial operativo** para la evaluación del valor.

No debe describirse como un valor extraído automáticamente de RegulonDB ni como evidencia documental por sí mismo.

---

# 8. Evidencia curatorial

La columna `Evidencia` está actualmente vacía en las 329 filas del subset.

Esto **no invalida el gold para evaluar los valores**.

El curador ya revisó el paper y determinó el valor y la modalidad. No se exigirá una segunda revisión de los papers sólo para reconstruir retrospectivamente la frase que sustentó cada decisión.

Por tanto:

```text
Evidencia curatorial = opcional
```

para el benchmark histórico.

---

# 9. Evidencia producida por el sistema

Aunque el gold no tenga pasajes de evidencia anotados, el sistema deberá producir evidencia cuando afirme un valor.

Ejemplo conceptual:

```text
property = TSS
value = -42
status = EXTRACTED
evidence = "...42 bp upstream of the ATG..."
source_location = RESULTS / paragraph / figure caption / etc.
```

Esta evidencia cumple una función operacional:

- permite al curador verificar la salida;
- reduce respuestas no sustentadas;
- facilita el análisis de errores;
- permite identificar de qué parte del documento provino la respuesta.

Sin embargo, debido a que no existe un pasaje gold anotado, no se calculará automáticamente como métrica principal:

```text
evidence exact match
evidence recall
passage retrieval recall contra evidencia humana
```

Una evaluación manual de evidencia sobre una muestra podrá agregarse posteriormente.

---

# 10. Modalidad de origen

Se mantienen las categorías curatoriales existentes en el corpus completo:

```text
texto_explicito
imagen_only
ausente_en_este_paper
inferido_no_dato
```

El subset actual contiene únicamente:

```text
texto_explicito
imagen_only
```

---

## 10.1 `texto_explicito`

El curador pudo determinar el valor mediante contenido textual disponible en el paper.

Estos registros constituyen un estrato natural para medir el desempeño de extracción textual.

---

## 10.2 `imagen_only`

El curador identificó originalmente el valor en una figura, gel, mapa u otra representación visual.

**No debe interpretarse automáticamente como "inalcanzable" para `promoter-ai-extraction`.**

La entrada real del sistema incluye TEI/XML y TXT derivados del paper. Ese proceso puede conservar:

- captions;
- referencias a figuras;
- texto asociado a figuras;
- etiquetas o fragmentos convertidos a texto;
- contenido estructurado que permita recuperar indirectamente el valor.

Por tanto, una fila `imagen_only` continúa siendo un target positivo si tiene valor curatorial.

Ejemplo:

```text
Gold:
Modalidad_origen = imagen_only
TSS = -42

TEI/TXT:
"Figure 2. The P1 transcription start site is located at -42."

Sistema:
TSS = -42
```

La extracción debe contarse como correcta.

---

## 10.3 `ausente_en_este_paper`

Decisión del proyecto:

> **Si el valor no está en el paper evaluado, no se utilizará como target positivo de extracción para ese paper.**

No se buscará un `PMID_fuente_alternativa` como parte del benchmark principal.

Estos registros pueden utilizarse posteriormente para evaluar abstención o falsas afirmaciones, pero no forman parte del denominador del recall de valores presentes en el paper.

---

## 10.4 `inferido_no_dato`

Si no existe un valor documental recuperable del paper, no se considerará un target positivo normal de extracción.

Puede conservarse para análisis de no-alucinación o abstención, pero queda fuera del denominador del recall de valores documentados.

---

# 11. No se utilizará `PMID_fuente_alternativa`

El proyecto no intentará reconstruir, como parte de este gold, qué otro paper asociado sustenta una propiedad ausente del paper actual.

Por tanto:

```text
PMID_fuente_alternativa
```

queda fuera del contrato obligatorio.

Esto mantiene la pregunta de evaluación en una sola unidad documental:

> **¿Qué puede extraerse de este paper para este promotor?**

---

# 12. Cuándo una fila se considera curada

Para este proyecto, una fila se considera **curada** cuando:

1. el curador revisó el paper para la combinación promotor-propiedad;
2. determinó la modalidad de origen;
3. estableció el valor cuando el paper permitía hacerlo;
4. corrigió el valor respecto a RegulonDB cuando fue necesario;
5. o determinó que no existía un valor recuperable del paper.

No se requiere como condición adicional que el curador haya almacenado la frase de evidencia.

Para el subset actual se asume que su inclusión corresponde a filas ya revisadas y clasificadas por el curador.

---

# 13. Cuándo una fila se considera evaluable para valor

Una fila es evaluable como **target positivo de extracción de valor** cuando:

```text
existe un valor curatorial operativo
+
el curador determinó que el valor pertenece a ese paper
+
la propiedad y el promotor están identificados
```

En el subset actual, las 329 filas tienen `GT_para_referencia` y pertenecen a `texto_explicito` o `imagen_only`; por ello pueden utilizarse como targets de valor, sujetos a las reglas finales de normalización por propiedad.

---

# 14. Evaluable no significa necesariamente fácilmente accesible

Una fila `imagen_only` puede ser evaluable porque el curador conoce el valor, aunque la representación TEI/TXT contenga poca o ninguna información que permita recuperarlo.

Por tanto, el benchmark debe distinguir:

```text
valor gold conocido
```

de:

```text
representación realmente disponible para el sistema
```

La dificultad de representación forma parte del desempeño end-to-end del sistema con TEI/TXT.

---

# 15. Recall

La ausencia de evidencia textual anotada **no impide calcular recall del valor**.

Para una propiedad:

```text
Recall = valores gold correctamente recuperados
         --------------------------------------
         valores gold que debían recuperarse
```

Ejemplo:

```text
80 TSS curatoriales evaluables
60 recuperados correctamente

Recall_TSS = 60 / 80 = 0.75
```

---

# 16. Recall total bajo la entrada real TEI/TXT

Debe reportarse una métrica global sobre todos los targets positivos del benchmark:

```text
Recall_total_TEI_TXT = aciertos en texto_explicito + aciertos en imagen_only
                       -----------------------------------------------
                       total texto_explicito + total imagen_only
```

Esta métrica responde:

> **De todos los valores encontrados por el curador, ¿qué proporción recupera el sistema utilizando la representación TEI/TXT que realmente recibe?**

---

# 17. Recall por modalidad

Además del recall total, se reportarán estratos separados.

## Recall `texto_explicito`

```text
correctos dentro de texto_explicito
-----------------------------------
total de targets texto_explicito
```

Responde:

> ¿Qué tan bien funciona el sistema cuando el curador encontró el dato en texto?

## Recall `imagen_only`

```text
correctos dentro de imagen_only
-------------------------------
total de targets imagen_only
```

Responde:

> ¿Cuánta información identificada originalmente de forma visual por el curador sigue siendo recuperable desde TEI/TXT?

Este segundo resultado puede ayudar posteriormente a decidir si incorporar procesamiento multimodal aporta una mejora suficiente para justificar su complejidad.

---

# 18. No se definirá todavía `reachable recall`

No se asumirá que:

```text
texto_explicito = alcanzable
imagen_only = inalcanzable
```

porque el TEI/TXT puede conservar información asociada a figuras.

Para hablar formalmente de `reachable recall` sería necesario anotar, caso por caso, si el valor es efectivamente observable en la representación entregada al sistema.

Mientras esa anotación no exista, se reportarán:

```text
Recall total TEI/TXT
Recall texto_explicito
Recall imagen_only
```

sin redefinir retrospectivamente la accesibilidad de cada fila.

---

# 19. Recall por propiedad

El recall debe reportarse por separado para:

```text
TSS
Caja -10
Caja -35
Factor sigma
```

Ejemplo de tabla futura:

| Propiedad | N gold | Recall total | Recall texto | Recall imagen_only |
|---|---:|---:|---:|---:|
| TSS | ... | ... | ... | ... |
| Caja -10 | ... | ... | ... | ... |
| Caja -35 | ... | ... | ... | ... |
| Factor sigma | ... | ... | ... | ... |

No se utilizará una única cifra global como sustituto de estos resultados por propiedad.

---

# 20. Precision y falsas afirmaciones

El gold también debe permitir evaluar si el sistema produce valores que no están respaldados por la referencia curatorial.

Conceptualmente:

```text
Precision = valores predichos correctamente
            -------------------------------
            valores afirmados por el sistema
```

Los casos `ausente_en_este_paper` e `inferido_no_dato`, cuando estén disponibles en el corpus completo, serán especialmente útiles para evaluar:

- falsas afirmaciones;
- sobreextracción;
- abstención;
- posible memorización o inferencia no documental.

La definición exacta de precision y false assertion rate se cerrará en el contrato de evaluación.

---

# 21. Comparación del valor por propiedad

El gold contract no debe asumir que todas las propiedades se comparan de la misma forma.

La comparación final se congelará por propiedad.

## TSS

Puede requerir distinguir:

- posición relativa;
- coordenada genómica;
- designación `+1`;
- múltiples TSS;
- normalización del ancla.

Exact match debe ser la referencia primaria una vez congelada la representación normalizada.

Tolerancias como +/-1 o +/-3 nt podrán reportarse como métricas secundarias, no como sustituto silencioso del exact match.

## Cajas -10 y -35

La comparación se realizará sobre secuencias normalizadas mediante reglas tipográficas previamente fijadas.

No se corregirán bases por similitud con consensos.

La longitud mínima definitiva **no se congela todavía**, porque los datos curatoriales contienen representaciones cortas que requieren revisión antes de convertir la longitud en un criterio de invalidez.

## Factor sigma

Se normalizarán inicialmente sólo variantes tipográficas inequívocas, por ejemplo:

```text
Sigma32
sigma32
sigma 32
σ32
```

Las equivalencias biológicas como `RpoS`, `sigmaS` y `sigma38` se definirán posteriormente mediante una tabla explícita si los datos lo requieren.

---

# 22. Múltiples valores

El gold debe permitir que una combinación `paper x promotor x propiedad` tenga más de un valor correcto.

Ejemplo:

```text
TSS = {-42, -39}
```

La asociación de todos los valores con el mismo promotor debe ser inequívoca.

El Excel actual puede contener más de un valor codificado dentro de una misma celda. Esa representación se conservará en el archivo fuente, pero antes de la evaluación final deberá definirse una regla reproducible para convertirla a un conjunto de valores.

La comparación de múltiples valores deberá distinguir al menos:

- conjunto exacto correcto;
- valores correctos faltantes;
- valores adicionales no sustentados.

La métrica exacta se cerrará en el contrato de evaluación.

---

# 23. Entradas permitidas al extractor

Para el benchmark principal, el extractor puede recibir:

```text
paper representado como TEI/XML o TXT
ID_paper
ID_promotor
Nombre_promotor
Sinonimo_gen_en_este_paper, si existe
Propiedad, si la ejecución es por propiedad
```

También puede recibir contexto no objetivo necesario para resolver la identidad del promotor, siempre que no revele el valor evaluado.

---

# 24. Información prohibida al extractor

El extractor no debe recibir:

```text
Valor_RegulonDB
Sin_dato_en_RegulonDB
Modalidad_origen
Valor_verificado_manualmente
GT_para_referencia
Técnica_confirmada_manualmente
resultados anteriores del sistema usados como target
clasificaciones TP / FP / FN
```

La misma restricción se aplica a información obtenida indirectamente mediante recuperación, bases de conocimiento o consultas a RegulonDB.

---

# 25. Separación entre gold y salida del sistema

Conceptualmente:

```text
                 PAPER + PROMOTOR
                        |
                        v
                    EXTRACTOR
                        |
                        v
           valor + status + evidencia
                        |
                        v
                    EVALUADOR
                  /                            v             v
          GOLD CURATORIAL    METADATOS
```

El extractor no conoce el target.

El evaluador sí puede utilizar:

- `GT_para_referencia`;
- `Modalidad_origen`;
- otros metadatos curatoriales;

para calcular y estratificar resultados.

---

# 26. Split de desarrollo y prueba

La partición se realizará siempre a nivel de `ID_paper`.

Todos los registros derivados de un mismo paper deben permanecer en la misma partición.

Esto evita que un paper contribuya simultáneamente a:

- desarrollo del prompt;
- ajuste de normalización;
- evaluación final.

No debe dividirse aleatoriamente por fila.

---

# 27. Uso del subset actual

`SUBSET_GOLD(2).xlsx` puede utilizarse ahora para:

- probar el contrato de salida;
- desarrollar el baseline;
- validar reglas de normalización;
- construir evaluaciones iniciales;
- identificar casos límite;
- diseñar el protocolo de comparación.

No debe asumirse que la distribución de este subset representa necesariamente la distribución definitiva del gold completo.

---

# 28. Qué puede evaluarse con el gold actual

Con los datos actuales se puede evaluar de forma objetiva:

- recuperación de valores;
- recall total;
- recall por propiedad;
- recall por `Modalidad_origen`;
- exactitud bajo reglas normalizadas;
- omisiones del sistema;
- comparación con RegulonDB como análisis secundario;
- diferencias entre registros con y sin corrección manual.

---

# 29. Qué no puede evaluarse automáticamente con el gold actual

Sin una anotación humana adicional de pasajes, no puede medirse automáticamente de forma fuerte:

- recall de evidencia;
- exact match del pasaje de evidencia;
- ranking de pasajes contra una lista gold de fragmentos;
- localización exacta del pasaje utilizado por el curador.

Estas dimensiones pueden estudiarse más adelante mediante una muestra anotada manualmente si aportan valor suficiente.

---

# 30. Casos de abstención

Cuando el corpus completo incluya registros `ausente_en_este_paper` o `inferido_no_dato`, no se considerarán positivos dentro del recall de valores presentes.

Servirán para responder:

> **¿El sistema evita afirmar un valor cuando el paper no ofrece un target documental?**

Su evaluación se definirá mediante métricas de abstención y falsas afirmaciones, no introduciendo artificialmente esos valores en el denominador del recall positivo.

---

# 31. RegulonDB como comparación secundaria

El proyecto conserva `Valor_RegulonDB` porque permite analizar:

```text
revisión curatorial actual <-> RegulonDB
```

pero esta comparación es diferente de:

```text
sistema <-> gold curatorial
```

Una discrepancia paper-RegulonDB no debe etiquetarse automáticamente como error de RegulonDB.

Puede deberse, entre otras causas, a:

- representaciones distintas;
- normalización;
- evidencia distribuida;
- otra publicación;
- decisiones curatoriales históricas;
- fuentes actualmente no disponibles.

---

# 32. Criterio de suficiencia del gold para el proyecto

El gold es suficiente para iniciar el desarrollo cuando permite, para cada unidad evaluada:

```text
identificar paper
identificar promotor
identificar propiedad
conocer el target curatorial operativo
conocer Modalidad_origen
```

No se requiere que cada fila tenga una cita textual gold.

---

# 33. Condiciones antes de congelar el test final

Antes de ejecutar la evaluación final deben estar cerrados:

1. el conjunto de papers de test;
2. la interpretación definitiva de `GT_para_referencia`;
3. las reglas de normalización por propiedad;
4. el tratamiento de múltiples valores;
5. las equivalencias de sigma que se utilizarán;
6. las reglas de comparación de TSS;
7. las métricas primarias y secundarias;
8. la forma de contar predicciones adicionales;
9. el tratamiento de filas ambiguas o no adjudicadas;
10. cualquier regla de exclusión.

Ninguna de estas reglas debe ajustarse mirando los resultados del test final.

---

# 34. Decisiones cerradas en esta versión

- La unidad evaluada es `paper x promotor x propiedad`.
- El gold se basa en la revisión realizada por el curador.
- No se exigirá reconstruir evidencia textual faltante.
- `Evidencia` no es obligatoria para calcular el desempeño del valor.
- El sistema sí debe producir evidencia para trazabilidad.
- `GT_para_referencia` es el target operativo del subset actual bajo la regla curatorial descrita.
- `PMID_fuente_alternativa` queda fuera.
- Si el dato no está en el paper, no es target positivo de ese paper.
- `imagen_only` continúa siendo evaluable como valor y no se supone inalcanzable desde TEI/TXT.
- Se reportará recall total y recall estratificado por modalidad.
- No se definirá todavía `reachable recall` sin anotar accesibilidad real.
- El split se realiza por paper.
- Las cuatro propiedades se reportan separadamente.
- Los targets curatoriales y de RegulonDB permanecen invisibles al extractor.

---

# 35. Decisiones abiertas

Aún deben cerrarse:

- normalización definitiva de TSS;
- tolerancias secundarias para posiciones TSS;
- interpretación de representaciones muy cortas de cajas -10/-35;
- sintaxis y parser de múltiples valores en el Excel actual;
- equivalencias biológicas de sigma;
- definición exacta de precision y false assertion rate;
- tratamiento cuantitativo de conjuntos parcialmente correctos;
- criterios de exclusión de casos curatoriales ambiguos si aparecen en el gold completo;
- tamaño y composición de los splits definitivos;
- posible evaluación manual de evidencia sobre una muestra.

---

# 36. Siguiente paso metodológico

Con este contrato, el siguiente documento debe ser el **Evaluation Contract**, donde se defina de forma operacional:

```text
Gold value + system output
           |
           v
   MATCH / MISMATCH / MISS /
   EXTRA VALUE / ABSTENTION
```

para cada propiedad.

Ese contrato especificará:

- normalización;
- comparación exacta;
- múltiples valores;
- recall;
- precision;
- F1;
- abstención;
- estratificación por modalidad;
- agregación por propiedad;
- intervalos de confianza agrupados por paper.

---

# 37. Principio rector

> **El gold de `promoter-ai-extraction` debe representar lo que el curador determinó que el paper reporta para el promotor y propiedad evaluados. No es necesario reconstruir retrospectivamente toda la evidencia humana para medir si el sistema recupera el valor. La salida del sistema, sin embargo, debe seguir siendo trazable y mostrar evidencia para que su afirmación pueda ser revisada.**
