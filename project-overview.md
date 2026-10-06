# `promoter-ai-extraction`
## Documento formal del proyecto

**Versión:** 0.2  
**Fecha:** 6 de octubre de 2026  
**Estado:** definición científica y de producto en consolidación  
**Dominio:** regulación transcripcional bacteriana  
**Caso inicial:** promotores de *Escherichia coli* asociados a RegulonDB  
**Contexto:** Proyecto Final de AI Engineering y necesidad real de curación de RegulonDB

---

## 1. Resumen ejecutivo

`promoter-ai-extraction` es un proyecto de inteligencia artificial orientado a apoyar la curación de literatura científica sobre regulación transcripcional bacteriana.

RegulonDB contiene promotores con propiedades curatoriales como TSS, caja -10, caja -35 y factor sigma, además de uno o más artículos científicos asociados. Sin embargo, históricamente la asociación entre un promotor y sus publicaciones no conserva necesariamente la procedencia explícita a nivel de cada propiedad. Por ello, no siempre puede determinarse directamente qué paper sustenta cada valor anotado.

Actualmente, un curador experto debe regresar a los artículos asociados y determinar qué información sobre el promotor está realmente sustentada por cada paper. Este trabajo implica localizar valores, interpretar representaciones heterogéneas, distinguir información textual de información originalmente visual y decidir cuándo una propiedad no puede establecerse a partir del documento evaluado.

El proyecto busca automatizar parte de este proceso mediante un sistema capaz de realizar **extracción guiada, estructurada, trazable y con abstención explícita**.

La primera versión evaluable recibirá:

```text
paper + identidad/contexto de un promotor
```

y deberá producir, de forma independiente para cada propiedad:

```text
TSS
caja -10
caja -35
factor sigma
```

junto con:

```text
valor(es) + evidencia encontrada + localización + estado
```

cuando la información pueda sustentarse en la representación documental disponible.

El benchmark histórico utilizará los valores determinados por el curador. La evidencia textual exacta usada originalmente por el curador no está disponible de forma sistemática y **no será un requisito del gold**. El sistema, sin embargo, sí deberá devolver evidencia para facilitar la verificación humana de sus resultados.

El objetivo de largo plazo no es únicamente reproducir anotaciones históricas, sino desarrollar una capacidad que pueda generalizar a literatura reciente y asistir el flujo continuo de curación de RegulonDB.

---

## 2. Contexto científico y curatorial

### 2.1 RegulonDB

RegulonDB es una base de datos especializada en regulación transcripcional bacteriana.

Entre otros tipos de información, integra:

- genes;
- promotores;
- unidades transcripcionales;
- factores sigma;
- interacciones regulatorias;
- evidencias;
- publicaciones científicas.

Para un promotor pueden existir propiedades como:

- TSS;
- caja -10;
- caja -35;
- factor sigma;
- evidencia experimental;
- publicaciones asociadas.

### 2.2 Problema histórico de procedencia

La estructura histórica puede representarse de forma simplificada como:

```text
Promotor
├── TSS
├── caja -10
├── caja -35
├── sigma
└── papers asociados
    ├── PMID A
    ├── PMID B
    └── PMID C
```

pero no siempre existe una relación explícita del tipo:

```text
TSS       <- PMID A
caja -10  <- PMID B
caja -35  <- PMID B
sigma     <- PMID C
```

La relación:

> **propiedad ↔ fuente documental**

puede necesitar reconstruirse mediante revisión de la literatura.

### 2.3 Trabajo actual del curador

Para un promotor y sus papers asociados, el curador revisa las fuentes y determina, para cada propiedad:

1. si existe información utilizable en el paper;
2. qué valor reporta;
3. si el valor coincide o no con la anotación existente;
4. si el dato se encuentra en texto o fue identificado visualmente;
5. si la información es insuficiente o ambigua;
6. qué interpretación científica es necesaria para representar el valor.

El proyecto parte de ese trabajo real de curación.

---

## 3. Flujo real de curación continua

RegulonDB mantiene una curación periódica de literatura reciente.

De manera simplificada:

```text
papers recientes sobre regulación transcripcional
                    |
                    v
clasificación curatorial del contenido
                    |
        +-----------+-----------+
        |           |           |
        v           v           v
   promotores      TUs    interacciones / otros
        |
        v
identificación de promotores
        |
        v
¿promotor ya conocido o nuevo?
        |
        v
extracción y curación de propiedades
        |
        v
RegulonDB
```

En ese flujo no se conoce necesariamente de antemano si los promotores reportados son nuevos o ya existen en la base de datos.

La primera parte del proyecto no intentará automatizar todo este flujo.

---

## 4. Definición del problema

RegulonDB posee propiedades de promotores asociadas a una o más publicaciones, pero la relación entre una propiedad específica y la fuente que la sustenta no siempre quedó registrada de manera explícita.

Como consecuencia, un curador debe revisar los artículos para determinar qué información sobre TSS, cajas -10/-35 y factores sigma está realmente sustentada por cada paper.

`promoter-ai-extraction` busca automatizar parte de esta tarea mediante **extracción guiada y trazable de propiedades de promotores**.

La tarea inicial se formula como:

> **Dado un paper, una representación documental disponible de ese paper y la identidad de un promotor de interés, determinar qué valores de TSS, caja -10, caja -35 y factor sigma pueden extraerse de forma responsable para ese promotor.**

Cuando exista un valor suficientemente sustentado, el sistema deberá extraerlo y devolver evidencia. Cuando no pueda establecerlo, deberá abstenerse o marcar la situación correspondiente, sin completar información por plausibilidad biológica ni por conocimiento previo de RegulonDB.

El corpus histórico revisado por curadores se utilizará como referencia de evaluación. La finalidad posterior es generalizar esta capacidad a literatura reciente.

---

## 5. Pregunta principal

> **¿Puede un sistema de IA identificar y extraer automática, estructurada y trazablemente las propiedades de un promotor bacteriano que un curador experto determinó a partir de un artículo científico?**

Preguntas secundarias:

1. ¿Qué propiedades se recuperan con mayor o menor recall?
2. ¿Qué tipo de representación documental produce más errores?
3. ¿Qué fracción de los datos originalmente identificados visualmente por el curador puede recuperarse desde TEI/TXT?
4. ¿Cuándo el sistema debe abstenerse?
5. ¿Qué errores corresponden a recuperación de contexto y cuáles a interpretación?
6. ¿Qué información requiere realmente un LLM y qué parte podría resolverse con métodos deterministas?
7. ¿La capacidad desarrollada sobre literatura histórica generaliza a papers recientes no utilizados durante el desarrollo?

---

## 6. Objetivo general

Desarrollar y evaluar un sistema de IA capaz de identificar, extraer y presentar de forma estructurada y trazable propiedades de promotores bacterianos a partir de literatura científica, utilizando valores revisados por curadores como referencia de evaluación y con la finalidad posterior de asistir la curación continua de RegulonDB.

---

## 7. Objetivos específicos

1. Definir un contrato científico reproducible para la extracción.
2. Extraer inicialmente TSS, caja -10, caja -35 y factor sigma.
3. Asociar cada valor producido por el sistema con evidencia recuperada de la entrada documental.
4. Conservar la formulación original y una representación normalizada cuando corresponda.
5. Permitir múltiples valores cuando el paper los asocie al mismo promotor.
6. Diferenciar valor extraíble de mención insuficiente de una propiedad.
7. Incorporar abstención explícita como comportamiento válido.
8. Evitar inferencias basadas únicamente en plausibilidad biológica o conocimiento externo.
9. Evaluar los valores extraídos contra el conjunto curado disponible.
10. Evaluar cada propiedad de manera independiente.
11. Analizar el desempeño por modalidad curatorial (`texto_explicito` e `imagen_only`).
12. Separar recuperación, extracción, normalización y evaluación.
13. Mantener una separación estricta entre entradas del extractor y targets de evaluación.
14. Analizar errores para justificar decisiones posteriores de arquitectura.
15. Evaluar posteriormente la generalización a literatura nueva.

---

## 8. Usuario principal y caso de uso

El usuario principal es:

> **un curador experto de regulación transcripcional bacteriana**.

El curador necesita reducir el tiempo destinado a localizar e interpretar información relevante sin perder:

- trazabilidad;
- contexto documental;
- control científico;
- posibilidad de revisar la salida del sistema.

El sistema debe **asistir**, no sustituir, la decisión científica final del curador.

---

## 9. Alcance de la Parte 1 — Proyecto Final de AI Engineering

La primera parte tendrá como flujo principal:

```text
paper + promotor identificado
            |
            v
   TEI/XML y/o TXT disponible
            |
            v
      extracción de:
      - TSS
      - caja -10
      - caja -35
      - factor sigma
            |
            v
 valor(es) + evidencia + trazabilidad + abstención
```

### 9.1 Incluido

- papers científicos reales;
- identidad/contexto de un promotor previamente identificado;
- TEI/XML generado previamente mediante GROBID;
- TXT derivado del TEI/XML;
- extracción independiente de las cuatro propiedades;
- evidencia recuperada por el sistema;
- localización de evidencia cuando sea posible;
- normalización controlada;
- múltiples valores;
- abstención;
- casos ambiguos;
- resultados estructurados;
- evaluación contra referencia curatorial;
- análisis por propiedad;
- análisis por modalidad curatorial;
- comparación de componentes cuando corresponda;
- análisis de errores;
- reproducibilidad;
- demostración o despliegue conforme a los requisitos del proyecto final.

### 9.2 Fuera del alcance obligatorio de la Parte 1

- descubrir automáticamente todos los promotores presentes en un paper;
- decidir automáticamente si un promotor es nuevo o ya existe en RegulonDB;
- automatizar la clasificación completa de papers en promotores, TUs, interacciones y otros objetos;
- actualizar RegulonDB automáticamente;
- procesar directamente imágenes originales de figuras en la versión inicial;
- recuperar materiales suplementarios no disponibles;
- reconstruir predicciones históricas desde archivos ausentes;
- resolver exhaustivamente todos los aliases históricos;
- ampliar automáticamente el sistema a otras bacterias;
- sustituir la revisión científica final del curador.

---

## 10. Parte 2 — Continuación para RegulonDB

La evolución posterior puede integrar el sistema al flujo curatorial real:

```text
papers recientes
      |
      v
clasificación de contenido
      |
      v
detección de promotores
      |
      v
resolución de entidad
      |
      v
¿nuevo o existente?
      |
      v
promoter-ai-extraction
      |
      v
propiedades + evidencia
      |
      v
revisión del curador
      |
      v
RegulonDB
```

Podrá incluir:

- descubrimiento de promotores;
- resolución de entidades;
- identificación nuevo/existente;
- procesamiento multimodal real de figuras;
- nuevas propiedades;
- integración al flujo periódico de curación;
- evaluación prospectiva sobre literatura recién publicada.

Esta segunda parte no es necesaria para considerar completa la primera entrega del Proyecto Final de AI Engineering.

---

## 11. Relación con el Proyecto Final de AI Engineering

El proyecto es apropiado para el curso porque:

- aborda una necesidad científica real;
- utiliza datos reales;
- integra modelos de IA en un sistema funcional;
- dispone de una referencia curatorial para evaluación objetiva;
- permite comparar componentes y comportamiento end-to-end;
- admite evolución desde un baseline sencillo hacia mecanismos de recuperación y verificación más complejos;
- puede desplegarse o demostrarse de forma reproducible.

Las decisiones técnicas se definirán después de congelar el contrato científico y de evaluación.

No se asumirá que una arquitectura más compleja es mejor. Cada componente deberá justificar su existencia mediante una necesidad real, un error observado o una mejora medible.

---

## 12. Fuentes documentales disponibles

### 12.1 PDF

Los papers originales existen en formato PDF.

Sin embargo, para la primera evaluación el núcleo de entrada disponible para extracción será principalmente TEI/XML y TXT derivados mediante GROBID.

### 12.2 TEI/XML

Existe una representación TEI/XML de los papers generada previamente mediante GROBID.

### 12.3 TXT estructurado

Existe una representación TXT derivada del TEI/XML que conserva, cuando es posible, estructura documental como:

- TITLE;
- ABSTRACT;
- METHODS;
- RESULTS;
- DISCUSSION;
- captions;
- referencias a figuras;
- contenido tabular o asociado a figuras cuando GROBID logra representarlo.

La conversión PDF -> GROBID -> TEI/TXT no forma parte inicialmente del problema de extracción.

### 12.4 Imágenes

Las imágenes originales de las figuras **no están disponibles como entrada del sistema en esta etapa**.

No obstante, parte del contenido asociado a figuras puede sobrevivir en TEI/TXT mediante:

- leyendas;
- referencias desde el cuerpo del artículo;
- texto asociado a figuras;
- etiquetas o texto recuperado durante la extracción documental.

Por ello, un caso clasificado por el curador como `imagen_only` no debe considerarse automáticamente inaccesible para el sistema.

### 12.5 Material suplementario

No se dispone sistemáticamente de archivos suplementarios.

Por tanto:

> **el material suplementario no disponible queda fuera del universo documental evaluado en esta etapa.**

---

## 13. Snapshot del subset curado disponible

El archivo de trabajo actual `SUBSET_GOLD` contiene:

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

Distribución por modalidad curatorial:

| `Modalidad_origen` | Registros |
|---|---:|
| `texto_explicito` | 133 |
| `imagen_only` | 196 |

Los 329 registros cuentan con un `GT_para_referencia` derivable. En 121 filas existe `Valor_verificado_manualmente`; en el resto el valor de referencia operativo utiliza `Valor_RegulonDB` según la regla vigente del archivo.

La columna `Evidencia` está actualmente vacía y **no se requerirá completarla para poder utilizar este subset en la evaluación de valores**.

Este subset es una referencia operativa mientras continúa la curación del conjunto completo.

---

## 14. Función de cada fuente de información

### Paper / TEI / TXT

Fuente documental que recibe el extractor.

### RegulonDB

Referencia histórica y fuente de contexto no objetivo cuando sea necesario.

### Revisión curatorial

Referencia humana para determinar el valor objetivo de evaluación.

### Salida del sistema

Predicción independiente que se compara posteriormente contra el valor curado.

Estas funciones no deben mezclarse.

---

## 15. Unidades metodológicas

### 15.1 Unidad de muestreo

> **paper**

Las observaciones derivadas de un mismo paper no deben tratarse como completamente independientes.

### 15.2 Unidad natural de inferencia

> **paper × promotor**

Una ejecución puede producir resultados para las cuatro propiedades.

### 15.3 Unidad de extracción y evaluación

> **paper × promotor × propiedad**

Cada propiedad produce una conclusión independiente.

### 15.4 Unidad de evidencia del sistema

> uno o más fragmentos localizables de la representación TEI/TXT que permitan justificar una salida.

### 15.5 Unidad para partición y bootstrap

> **paper**

Todos los registros del mismo paper deben permanecer juntos en una misma partición.

---

## 16. Propiedades iniciales

### 16.1 TSS

El sistema deberá poder representar, según corresponda:

- posición relativa;
- dirección upstream/downstream;
- ancla;
- coordenada genómica absoluta;
- designación `+1`;
- nucleótido de inicio;
- múltiples TSS;
- técnica experimental como metadato complementario cuando pueda asociarse correctamente.

### 16.2 Caja -10

El sistema deberá extraer una o más secuencias cuando el contenido documental permita asociarlas con la caja -10 del promotor objetivo.

### 16.3 Caja -35

Se aplican las mismas reglas generales de asociación, evidencia y secuencia que para caja -10.

### 16.4 Factor sigma

El sistema deberá identificar denominaciones de sigma asociadas al promotor o a su evento de transcripción.

---

## 17. Contrato común de extracción

El contrato especializado se mantiene en un documento independiente.

Principios principales:

1. una propiedad puede tener cero, uno o múltiples valores;
2. todo valor producido por el sistema debe incluir evidencia;
3. la evidencia debe permitir asociar valor + propiedad + promotor;
4. `value_raw` y `value_normalized` son conceptos diferentes;
5. una normalización reproducible no equivale a inferencia biológica;
6. el sistema puede y debe abstenerse;
7. los candidatos ambiguos no deben mezclarse con valores aceptados;
8. los estados del sistema no equivalen a las modalidades curatoriales del gold.

---

## 18. Estados conceptuales del extractor

Estados provisionales:

```text
EXTRACTED
NOT_FOUND
INSUFFICIENT_EVIDENCE
UNSUPPORTED_MODALITY
AMBIGUOUS
INVALID_CANDIDATE
```

### `EXTRACTED`

Existe evidencia suficiente en la entrada para aceptar uno o más valores.

### `NOT_FOUND`

El sistema no localizó evidencia suficiente para establecer un valor.

No significa necesariamente que la propiedad no exista.

### `INSUFFICIENT_EVIDENCE`

El sistema localizó información relevante, pero no suficiente para establecer el valor solicitado.

### `UNSUPPORTED_MODALITY`

Existe un indicio explícito de que la información necesaria está en una representación no disponible para el sistema.

Este estado **no se asigna automáticamente a todos los casos `imagen_only`**.

### `AMBIGUOUS`

Existen candidatos o interpretaciones plausibles, pero no puede resolverse responsablemente la asociación correcta.

### `INVALID_CANDIDATE`

Estado provisional para un candidato que no satisface una regla científica o formal vigente.

---

## 19. Modalidad curatorial del gold

La modalidad describe **cómo el curador identificó originalmente el dato**, no necesariamente qué puede recuperar el sistema desde TEI/TXT.

### `texto_explicito`

El curador estableció el valor a partir de contenido textual del paper.

### `imagen_only`

El curador estableció el valor mediante una figura u otra representación visual.

Importante:

> `imagen_only` no implica automáticamente que el sistema text-only no pueda recuperar el valor.

La información puede sobrevivir parcialmente en TEI/TXT mediante captions, referencias, texto asociado a figuras u otros elementos extraídos.

### `ausente_en_este_paper`

Si el valor no está sustentado en el paper evaluado, **no será target de extracción para ese paper**.

No se buscará un PMID alternativo para convertir ese caso en positivo.

### `inferido_no_dato`

Si no existe un valor documental recuperable en el paper, no será target normal de extracción.

No se intentará reconstruir retrospectivamente si el valor provino de predicción, criterio experto, suplemento ausente u otra fuente no disponible.

---

## 20. Reglas científicas transversales

### 20.1 Asociación con el promotor

Todo valor extraído debe poder asociarse de forma justificable con el promotor objetivo.

Encontrar un valor correcto en el artículo no basta.

### 20.2 Múltiples promotores

Un paper puede reportar varios promotores.

No se asignarán valores por:

- cercanía textual;
- orden de aparición;
- plausibilidad biológica;
- coincidencia con RegulonDB.

Si la asociación no puede resolverse:

```text
AMBIGUOUS
```

### 20.3 Múltiples valores

Un mismo promotor puede tener más de un valor para una propiedad.

Si el paper sustenta varios valores para el mismo promotor, todos pueden considerarse correctos.

### 20.4 Mención no equivale a valor

Por ejemplo:

```text
P1 contains a typical -10 region.
```

menciona la propiedad pero no proporciona necesariamente la secuencia.

### 20.5 No guessing

El sistema no debe completar información por plausibilidad biológica.

Ejemplos prohibidos:

- inferir TATAAT porque parece consenso -10;
- completar una caja -35 porque el promotor es sigma70;
- reconstruir una caja usando el genoma;
- utilizar un valor memorizado de RegulonDB sin apoyo documental en la entrada.

---

## 21. Reglas iniciales de TSS

### 21.1 Anclas equivalentes para normalización

Cuando el contexto sea inequívoco, se consideran variantes de una misma referencia:

```text
translation start
translational start
start codon
initiation codon
ATG
gene start
```

Normalización conceptual:

```text
anchor_normalized = translation_start
```

Debe conservarse también la formulación original.

### 21.2 Signo

Con ancla válida:

```text
upstream   -> negativo
downstream -> positivo
```

### 21.3 Falta de ancla

Una expresión como:

```text
42 bp upstream
```

no debe convertirse automáticamente a `-42` relativo al inicio de traducción si la referencia no está establecida.

### 21.4 `+1`

`+1` puede designar convencionalmente el propio sitio de inicio de transcripción.

No debe convertirse automáticamente en una distancia `+1` respecto del inicio de traducción.

### 21.5 Coordenada genómica absoluta

Una coordenada absoluta reportada por el paper constituye un TSS válido aunque no pueda convertirse a posición relativa usando sólo el artículo.

No se utilizará información externa para forzar esa conversión durante la extracción documental.

### 21.6 Técnica experimental

Puede conservarse cuando sea identificable y esté asociada al TSS/promotor.

No es requisito obligatorio para aceptar un valor TSS suficientemente sustentado.

---

## 22. Reglas iniciales de cajas -10 y -35

### 22.1 Valor principal

El valor principal es la secuencia nucleotídica que el paper asocia documentalmente con la caja correspondiente del promotor.

### 22.2 Longitud

Se han observado representaciones muy cortas en el material curado, incluso por debajo del rango inicialmente supuesto.

Por tanto, **no se congelará todavía un mínimo definitivo de longitud como criterio excluyente**.

La longitud deberá revisarse contra el gold completo antes de establecer una regla final.

En todos los casos:

> la longitud por sí sola no demuestra que una secuencia sea una caja -10 o -35.

### 22.3 Normalización

Se permiten transformaciones inequívocamente tipográficas, por ejemplo:

```text
tataat  -> TATAAT
TAT AAT -> TATAAT
TAT-AAT -> TATAAT
```

No se permite corregir bases por similitud con un consenso.

### 22.4 Consenso

Una secuencia de consenso general no puede asignarse automáticamente como caja del promotor objetivo.

### 22.5 Calificadores

Expresiones como:

```text
putative
predicted
possible
-10-like
-35-like
```

pueden conservarse cuando el propio artículo asocia la secuencia con el promotor.

El sistema debe preservar el calificativo y no aumentar la fuerza de la afirmación.

---

## 23. Reglas iniciales de factor sigma

### 23.1 Asociación

La aparición de un factor sigma en el artículo no basta.

Debe existir evidencia que lo relacione con el promotor objetivo o con su evento de transcripción.

### 23.2 Variantes tipográficas claras

Por ahora se normalizarán únicamente equivalencias inequívocas como:

```text
σ32
σ 32
sigma32
sigma 32
Sigma32
Sigma 32
SIGMA32
```

hacia una representación común como:

```text
sigma32
```

De manera análoga:

```text
σ54 / Sigma54 / sigma 54 -> sigma54
σF / SigmaF / sigma F    -> sigmaF
```

### 23.3 Equivalencias biológicas pendientes

No se aplicarán todavía automáticamente equivalencias como:

```text
RpoS <-> sigmaS <-> sigma38
RpoH <-> sigma32
RpoN <-> sigma54
```

Se revisarán más adelante contra los valores reales del gold completo.

---

## 24. Trazabilidad del sistema

Aunque el gold histórico no contenga la evidencia exacta usada por el curador, **el sistema sí deberá proporcionar evidencia** para toda extracción aceptada.

Cuando sea posible, deberá conservar:

- fragmento;
- sección;
- página si está disponible;
- tabla;
- caption;
- referencia a figura;
- otro identificador de localización disponible.

No se requiere almacenar chain-of-thought.

La trazabilidad del producto se basa en:

> **evidencia observable + localización + derivación explícita cuando sea necesaria**.

---

## 25. Gold set operativo

### 25.1 Qué representa

El gold responde principalmente:

> **¿Qué valor determinó el curador que corresponde a esta propiedad de este promotor en este paper?**

No responde necesariamente:

> ¿Cuál fue la oración exacta que utilizó el curador para determinarlo?

### 25.2 La evidencia curatorial no es obligatoria

La frase o fragmento utilizado originalmente por el curador no está disponible de manera sistemática.

Por ello:

> **la evidencia curatorial no será requisito para que una fila pueda utilizarse en la evaluación del valor.**

Esto evita repetir una segunda curación completa de los papers únicamente para reconstruir pasajes de evidencia.

### 25.3 Valor objetivo operativo

Para el subset actual se utilizará `GT_para_referencia` como target operativo, con la regla existente:

```text
si Valor_verificado_manualmente existe:
    GT_para_referencia = Valor_verificado_manualmente
si no:
    GT_para_referencia = Valor_RegulonDB
```

Esta regla se utiliza bajo el supuesto de que las filas incluidas corresponden a casos ya revisados por el curador en el proceso que originó el subset.

### 25.4 `PMID_fuente_alternativa`

No se utilizará.

Si una propiedad no está en el paper evaluado, no se convertirá en target positivo mediante información de otro paper.

---

## 26. Fila curada y fila evaluable

### 26.1 Fila curada

Una fila se considera curada cuando el curador revisó la combinación:

```text
paper × promotor × propiedad
```

y estableció el valor correspondiente o determinó la modalidad/ausencia pertinente según el protocolo disponible.

### 26.2 Fila evaluable para extracción de valor

Una fila es evaluable cuando:

1. existe un target curatorial operativo;
2. el target corresponde al paper evaluado;
3. la propiedad está dentro del alcance actual;
4. el caso no está pendiente de adjudicación curatorial.

No se exige una frase de evidencia curatorial.

### 26.3 Casos sin target documental

Los casos `ausente_en_este_paper` e `inferido_no_dato` no forman parte del denominador del recall de valores.

Podrán utilizarse posteriormente para analizar abstención o falsas afirmaciones, si están disponibles de manera confiable en el conjunto completo.

---

## 27. Anti-leakage

El extractor puede recibir:

- TEI/XML o TXT del paper;
- ID del paper;
- identidad del promotor;
- nombre del promotor;
- sinónimo utilizado en el paper cuando exista;
- propiedad, si se ejecuta una propiedad por llamada.

El extractor no debe recibir:

- `Valor_RegulonDB` cuando constituye el target;
- `Valor_verificado_manualmente`;
- `GT_para_referencia`;
- `Modalidad_origen`;
- resultado TP/FP/FN;
- etiquetas del evaluador que revelen la respuesta;
- salidas anteriores utilizadas como target.

Estas restricciones deben mantenerse también si posteriormente se incorpora RAG, una base de conocimiento o consultas externas.

---

## 28. Separación desarrollo / prueba

La partición debe realizarse por paper.

Nunca deben quedar registros del mismo PMID simultáneamente en desarrollo y prueba.

Las iteraciones de:

- prompt;
- reglas de normalización;
- retrieval;
- parámetros ajustables;
- tablas de equivalencias;

se realizarán utilizando únicamente desarrollo.

El test final deberá permanecer congelado después de cerrar las reglas.

---

## 29. Validación

Validación significa comprobar que una salida cumple el contrato científico y estructural.

No equivale a compararla contra el gold.

La validación deberá comprobar, entre otros aspectos:

- consistencia entre estado y valores;
- presencia de evidencia del sistema cuando existe un valor;
- asociación entre valor, propiedad y promotor;
- cumplimiento de reglas específicas;
- representación de múltiples valores;
- ausencia de valores aceptados cuando el estado implica abstención;
- normalizaciones permitidas.

---

## 30. Evaluación

Evaluación significa comparar la salida del sistema con el valor curatorial de referencia.

La ausencia de evidencia anotada en el gold **no impide calcular recall, precision ni exactitud de valores**.

Sí impide medir automáticamente, de manera completa, si el pasaje de evidencia generado por el sistema coincide con el pasaje que utilizó originalmente el curador.

---

## 31. Evaluación principal: valor extraído

La comparación principal será:

```text
valor(es) del sistema
        vs.
valor(es) determinados por el curador
```

para cada unidad:

```text
paper × promotor × propiedad
```

Esto permite calcular métricas de recuperación sin disponer de la frase curatorial original.

---

## 32. Recall

Para una propiedad dada:

```text
Recall = valores gold correctamente recuperados
         --------------------------------------
         valores gold que debían recuperarse
```

El recall se calculará por propiedad.

Ejemplo conceptual:

```text
80 TSS en el gold
60 recuperados correctamente

Recall_TSS = 60 / 80 = 0.75
```

La evidencia curatorial original no es necesaria para esta métrica.

---

## 33. Recall total y análisis por modalidad

Dado que el sistema recibe TEI/TXT pero no las imágenes originales, se reportarán al menos tres vistas:

### 33.1 Recall total bajo la entrada disponible

Incluye todos los targets curatoriales evaluables del benchmark, independientemente de la modalidad en la que el curador los identificó.

Pregunta:

> ¿Qué proporción del trabajo curatorial puede recuperar el sistema usando realmente TEI/TXT?

### 33.2 Recall en `texto_explicito`

Pregunta:

> Cuando el curador encontró el valor en texto, ¿qué proporción recupera el sistema?

### 33.3 Recall en `imagen_only`

Pregunta:

> ¿Qué fracción de la información originalmente visual sigue siendo recuperable indirectamente desde TEI/TXT?

Esta métrica es relevante porque captions, referencias y texto asociado a figuras pueden conservar parte de la información visual original.

No se utilizará por ahora la etiqueta `reachable recall` a menos que posteriormente se anote de manera explícita qué casos son realmente alcanzables desde la representación TEI/TXT.

---

## 34. Evidencia del sistema y evaluación de grounding

La evidencia generada por el sistema sigue siendo un requisito del producto, aunque no exista evidencia gold anotada.

Por tanto, se distinguen dos cosas:

### Evaluación automática principal

Puede medir:

- valor correcto;
- valor incorrecto;
- omisión;
- múltiples valores;
- abstención;
- comportamiento por modalidad.

### Evaluación de evidencia

No podrá medirse exhaustivamente contra un pasaje gold inexistente.

Opciones futuras:

- revisión humana de una muestra estratificada;
- anotación específica de evidencia para un subset pequeño;
- evaluación de si la evidencia citada realmente sustenta la salida.

Esto deberá reportarse como evaluación humana o secundaria, no confundirse con las métricas automáticas del valor.

---

## 35. Métricas candidatas

Las métricas finales se congelarán después de revisar el gold completo.

Entre las candidatas:

### Por valor

- exact match;
- normalized exact match;
- comparación de conjuntos para múltiples valores;
- tolerancia posicional secundaria para TSS.

### Por extracción

- precision;
- recall;
- F1;
- cobertura;
- false assertion rate cuando existan negativos documentales utilizables.

### Por modalidad

- resultados totales;
- resultados en `texto_explicito`;
- resultados en `imagen_only`.

### Agregación

- métricas por propiedad;
- micro cuando sea apropiado;
- macro cuando sea apropiado;
- intervalos de confianza agrupados por paper.

---

## 36. Casos límite importantes

El proyecto debe contemplar al menos:

1. múltiples promotores en un mismo paper;
2. múltiples TSS del mismo promotor;
3. múltiples cajas correctamente asociadas;
4. valores distribuidos entre varias frases;
5. nombres históricos o sinónimos;
6. `+1` transcripcional;
7. posiciones upstream/downstream sin ancla;
8. coordenadas genómicas absolutas;
9. caja mencionada sin secuencia;
10. secuencia candidata no asociable al promotor;
11. consenso general confundido con un valor específico;
12. sigma presente en el paper pero no asociado al promotor;
13. múltiples sigmas;
14. información originalmente visual cuyo caption sí sobrevive en TEI/TXT;
15. información visual cuyo valor no sobrevive en TEI/TXT;
16. valores con normalización tipográfica;
17. múltiples valores codificados en una misma celda del gold;
18. representaciones de cajas muy cortas que requieren revisión antes de definir un mínimo formal;
19. discordancias entre revisión actual y RegulonDB;
20. casos irresolubles para el propio curador.

---

## 37. Manejo de incertidumbre

La incertidumbre no debe ocultarse detrás de un valor forzado.

Se utilizarán:

- `AMBIGUOUS`;
- `INSUFFICIENT_EVIDENCE`;
- `UNSUPPORTED_MODALITY`;
- revisión humana cuando sea necesario.

Los casos que el curador no pueda adjudicar de forma estable no deberán formar parte del benchmark principal hasta ser resueltos.

No se exige por ahora un `confidence_score` numérico del modelo.

---

## 38. Restricciones

1. El sistema sólo puede utilizar la representación documental que se le proporcione.
2. Las imágenes originales no forman parte de la entrada inicial.
3. Parte del contenido de figuras puede aparecer indirectamente en TEI/TXT.
4. No se dispone sistemáticamente de material suplementario.
5. La evidencia exacta usada históricamente por el curador no está anotada.
6. El corpus histórico puede contener anotaciones cuya procedencia completa no pueda reconstruirse.
7. Un mismo paper puede producir varias filas dependientes.
8. RegulonDB es público y existe riesgo de memorización por parte de modelos.
9. La evaluación final depende de congelar el gold y las reglas antes del test.
10. Las reglas no deben ajustarse utilizando los resultados del conjunto de prueba final.

---

## 39. Supuestos

1. El paper proporcionado corresponde al documento que se desea revisar.
2. En la Parte 1, la identidad del promotor ya ha sido establecida.
3. El sinónimo histórico puede proporcionarse cuando sea necesario.
4. El extractor no conoce el valor objetivo.
5. El valor determinado por el curador constituye la referencia principal para la tarea de extracción documental.
6. La falta de evidencia curatorial anotada no invalida la evaluación del valor.
7. El sistema deberá producir su propia evidencia para permitir verificación humana.
8. Las reglas de normalización se congelarán antes del test final.
9. El sistema final se utilizará como apoyo a curación, no como sustituto automático del curador.

---

## 40. Riesgos metodológicos y mitigaciones

### 40.1 Leakage de valores

**Riesgo:** el modelo recibe directa o indirectamente el target.  
**Mitigación:** mantener targets y metadatos de evaluación fuera del contexto del extractor.

### 40.2 Memorización de RegulonDB

**Riesgo:** un modelo puede conocer datos públicos de RegulonDB.  
**Mitigación:** exigir evidencia atribuible al paper y considerar diagnósticos closed-book cuando sean útiles.

### 40.3 Ausencia de evidencia gold

**Riesgo:** no puede medirse automáticamente si el sistema recuperó el mismo pasaje que utilizó el curador.  
**Mitigación:** separar evaluación de valor de evaluación de grounding; realizar auditoría humana de evidencia en una muestra si se necesita.

### 40.4 Sobreinterpretar `imagen_only`

**Riesgo:** asumir que todos esos casos son inalcanzables para TEI/TXT.  
**Mitigación:** conservarlos en el benchmark y reportarlos como estrato separado.

### 40.5 Sobreajuste al subset actual

**Riesgo:** convertir peculiaridades de 329 filas en reglas universales.  
**Mitigación:** considerar las reglas provisionales y revisarlas antes de congelar el gold completo.

### 40.6 Arquitectura artificialmente compleja

**Riesgo:** introducir RAG, agentes u otros componentes sólo para cumplir una etiqueta.  
**Mitigación:** justificar cada componente mediante necesidad, error o mejora medible.

### 40.7 Dependencia entre observaciones

**Riesgo:** tratar múltiples filas del mismo paper como independientes.  
**Mitigación:** split y bootstrap agrupados por paper.

---

## 41. Criterios de éxito de la Parte 1

El proyecto no se considerará exitoso sólo porque el modelo genere respuestas plausibles.

Debe demostrar que:

1. produce resultados estructurados;
2. las propiedades extraídas incluyen evidencia generada por el sistema;
3. puede abstenerse;
4. no recibe los valores objetivo;
5. maneja múltiples valores;
6. permite evaluar TSS, -10, -35 y sigma por separado;
7. permite calcular recall y otras métricas contra los valores curatoriales disponibles;
8. permite analizar resultados por `texto_explicito` e `imagen_only`;
9. maneja explícitamente los casos ambiguos;
10. sus resultados son reproducibles;
11. documenta sus limitaciones;
12. puede demostrarse o probarse conforme a los requisitos del curso;
13. las decisiones técnicas se justifican mediante evidencia experimental.

---

## 42. Evaluación prospectiva futura

Una continuación especialmente valiosa será congelar una versión del sistema y evaluarla sobre papers recientes que no hayan participado en:

- desarrollo del prompt;
- definición de reglas;
- construcción del benchmark histórico.

Conceptualmente:

```text
papers nuevos
      |
 +----+----+
 |         |
 v         v
sistema   curación humana
 |         |
 +----+----+
      |
      v
comparación posterior
```

Esta evaluación permitirá responder:

> **¿El sistema generaliza a literatura científica nueva y puede ayudar realmente al flujo periódico de curación?**

---

## 43. Decisiones cerradas provisionalmente

- nombre del proyecto: `promoter-ai-extraction`;
- problema científico central;
- separación Parte 1 / Parte 2;
- cuatro propiedades iniciales;
- paper como unidad de muestreo;
- paper × promotor como unidad natural de inferencia;
- paper × promotor × propiedad como unidad de evaluación;
- TEI/XML y TXT como representación principal disponible;
- imágenes originales fuera de la entrada inicial;
- `imagen_only` como modalidad curatorial, no como sinónimo de inaccesible;
- evidencia del sistema obligatoria para valores extraídos;
- evidencia curatorial no obligatoria para evaluar valores;
- `PMID_fuente_alternativa` fuera del contrato;
- si una propiedad no está en el paper, no se cuenta como target positivo para ese paper;
- múltiples valores permitidos si corresponden al mismo promotor;
- TSS relativo y coordenada absoluta válidos como representaciones distintas;
- equivalencia de anclas de inicio de traducción acordada;
- `+1` no convertido automáticamente a posición relativa al gen;
- no congelar todavía un mínimo definitivo de longitud para cajas;
- normalización tipográfica clara de sigma;
- equivalencias RpoS/RpoH/RpoN diferidas;
- targets de RegulonDB invisibles al extractor;
- material suplementario no disponible fuera del alcance actual;
- recall calculable a partir de valores curatoriales aunque no exista evidencia anotada;
- resultados estratificados por `texto_explicito` e `imagen_only`.

---

## 44. Decisiones todavía abiertas

1. definición final del target normalizado por propiedad;
2. representación definitiva de múltiples valores en el gold;
3. tratamiento de valores curatoriales muy cortos en cajas -10/-35;
4. equivalencias biológicas de sigma;
5. métricas primarias y secundarias definitivas por propiedad;
6. tolerancias de TSS que se reportarán de manera secundaria;
7. reglas exactas para precision/F1 cuando existan múltiples valores;
8. uso de negativos documentales para medir falsas afirmaciones;
9. evaluación humana de evidencia del sistema;
10. particiones definitivas de desarrollo y prueba;
11. tamaño final del gold;
12. arquitectura técnica;
13. diseño de retrieval;
14. uso y función específica de agentes;
15. despliegue final.

---

## 45. Documentos relacionados

Este documento funciona como descripción formal de alto nivel del proyecto.

El contrato especializado de extracción debe mantenerse separado, por ejemplo:

```text
docs/extraction-contract.md
```

Posteriormente deberán consolidarse documentos específicos para:

```text
docs/gold-set-contract.md
docs/evaluation-contract.md
docs/project-requirements.md
```

cuando las decisiones correspondientes queden congeladas.

---

## 46. Principio rector

> **El objetivo de `promoter-ai-extraction` no es producir el valor biológicamente más plausible ni reproducir automáticamente RegulonDB. Su objetivo es determinar qué valor puede recuperarse responsablemente para un promotor a partir de la representación documental disponible de un paper, mostrar la evidencia que sustenta la extracción y abstenerse cuando la información no permita establecer una conclusión confiable.**

