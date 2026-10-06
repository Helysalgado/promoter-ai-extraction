# Extraction Contract — `promoter-ai-extraction`

**Versión:** 0.2  
**Estado:** contrato científico consolidado para implementación  
**Proyecto:** `promoter-ai-extraction`  
**Unidad de extracción:** `paper × promotor × propiedad`

---

## 1. Propósito

Este documento define el contrato científico común que debe cumplir el extractor de `promoter-ai-extraction`.

El contrato establece:

- qué recibe conceptualmente el sistema;
- qué debe producir para cada propiedad;
- cuándo una extracción puede considerarse válida;
- cuándo debe abstenerse;
- cómo representar múltiples valores;
- qué normalizaciones están permitidas;
- qué evidencia debe conservar;
- qué reglas específicas aplican a TSS, caja -10, caja -35 y factor sigma.

Este documento **no** define todavía:

- arquitectura;
- proveedor de LLM;
- RAG;
- agentes;
- API;
- base de datos;
- framework de frontend;
- formato técnico definitivo del JSON.

---

# 2. Tarea de extracción

La tarea principal es:

> **Dado un artículo científico en una representación disponible y un promotor identificado, determinar qué valores de TSS, caja -10, caja -35 y factor sigma pueden sustentarse con la información disponible en ese artículo.**

El sistema debe:

1. encontrar evidencia relevante;
2. asociarla con el promotor objetivo;
3. asociarla con la propiedad correcta;
4. extraer uno o más valores cuando corresponda;
5. conservar la formulación original;
6. normalizar sólo mediante reglas previamente permitidas;
7. mostrar la evidencia;
8. abstenerse cuando el valor no pueda establecerse responsablemente.

---

# 3. Unidad de extracción

La unidad conceptual es:

```text
paper × promotor × propiedad
```

donde:

```text
propiedad ∈ {
    TSS,
    caja_-10,
    caja_-35,
    factor_sigma
}
```

Una ejecución puede procesar simultáneamente las cuatro propiedades, pero cada una debe producir una conclusión independiente.

Ejemplo:

```text
TSS       -> EXTRACTED
-10       -> EXTRACTED
-35       -> NOT_FOUND
sigma     -> INSUFFICIENT_EVIDENCE
```

---

# 4. Entradas conceptuales permitidas

El extractor puede recibir:

```text
paper / TEI / TXT
ID_paper / PMID
ID_promotor
Nombre_promotor
Sinonimo_gen_en_este_paper, cuando exista
Propiedad, cuando la ejecución sea por propiedad
```

El sinónimo histórico puede utilizarse para localizar correctamente el promotor dentro del artículo.

---

# 5. Información prohibida durante la extracción

El extractor no debe recibir:

```text
Valor_RegulonDB
Valor_verificado_manualmente
GT_para_referencia
Modalidad_origen
Resultado de evaluación
TP / FP / FN
otras respuestas esperadas de la fila
```

Estas restricciones también se aplican a información recuperada indirectamente mediante mecanismos futuros.

La extracción debe ser independiente del target.

---

# 6. Estructura conceptual de salida

Cada propiedad debe producir conceptualmente:

```text
ExtractionResult
|
|-- identity
|   |-- paper
|   |-- promoter
|   `-- property
|
|-- status
|
|-- values[]
|   |-- value_raw
|   |-- value_normalized
|   |-- qualifier
|   |-- derivation_note
|   |-- evidence_refs[]
|   `-- property_specific_details
|
|-- candidate_values[]              [si aplica]
|
|-- evidence_items[]
|   |-- fragment
|   |-- source_type
|   `-- source_location
|
`-- abstention_or_ambiguity_reason  [si aplica]
```

Esta estructura es conceptual. El schema técnico definitivo podrá adaptarla sin cambiar su significado científico.

---

# 7. Estados del extractor

Los estados iniciales son:

```text
EXTRACTED
NOT_FOUND
INSUFFICIENT_EVIDENCE
UNSUPPORTED_MODALITY
AMBIGUOUS
INVALID_CANDIDATE
```

`INVALID_CANDIDATE` permanece provisional y puede convertirse después en una bandera diagnóstica en lugar de estado final.

---

# 8. `EXTRACTED`

Se utiliza únicamente cuando existe evidencia suficiente para establecer uno o más valores.

Una extracción válida debe satisfacer simultáneamente:

```text
valor
+
propiedad correcta
+
promotor correcto
+
evidencia suficiente
```

No basta encontrar en el paper:

- un número;
- una secuencia;
- un factor sigma;
- una coordenada;
- una expresión biológicamente plausible.

La evidencia debe permitir justificar que el valor corresponde a **esa propiedad del promotor objetivo**.

---

# 9. `NOT_FOUND`

Significa:

> El sistema no localizó evidencia suficiente para establecer un valor en la representación que recibió.

No significa:

> La propiedad no existe.

Tampoco significa necesariamente:

> La propiedad no está en el paper.

`NOT_FOUND` es un resultado del extractor, no una conclusión biológica.

---

# 10. `INSUFFICIENT_EVIDENCE`

Se utiliza cuando se encontró información relevante sobre la propiedad, pero no es suficiente para establecer responsablemente el valor solicitado.

Ejemplo:

```text
Promoter P1 contains a typical -10 region.
```

Hay mención de la propiedad, pero no una secuencia de caja -10.

Resultado:

```text
status = INSUFFICIENT_EVIDENCE
values = []
```

Otro ejemplo:

```text
Primer extension confirmed transcription from P1.
```

Esto apoya que existe inicio de transcripción, pero no necesariamente proporciona la posición del TSS.

---

# 11. `UNSUPPORTED_MODALITY`

Se utiliza cuando la representación disponible indica razonablemente que la información necesaria depende de una modalidad que el sistema actual no puede resolver.

Ejemplo:

```text
The transcription start sites are indicated in Fig. 2.
```

si el TEI/TXT no conserva los valores.

No debe asignarse automáticamente porque el gold tenga:

```text
Modalidad_origen = imagen_only
```

Un caso curatorial `imagen_only` puede ser `EXTRACTED` si la leyenda, texto asociado o contenido recuperado en TEI/TXT permite establecer el valor.

---

# 12. `AMBIGUOUS`

Se utiliza cuando existen candidatos o evidencia relevante, pero no puede resolverse responsablemente la asociación o interpretación correcta.

Ejemplo:

```text
P1 and P2 were analyzed.
Transcription started at -42 and -61.
```

si no puede establecerse cuál TSS corresponde a cada promotor.

Resultado:

```text
status = AMBIGUOUS
values = []
candidate_values = [-42, -61]
```

Los candidatos ambiguos no deben presentarse como valores aceptados.

---

# 13. `INVALID_CANDIDATE`

Estado provisional para candidatos que violan una regla científica o formal vigente.

No debe utilizarse para “corregir” al paper.

Si la revisión del gold demuestra que una regla vigente era demasiado restrictiva, debe corregirse el contrato antes de congelar la evaluación final.

---

# 14. Cero, uno o múltiples valores

Una propiedad puede tener:

- cero valores;
- un valor;
- múltiples valores.

El contrato no asume:

```text
una propiedad = un único valor
```

Los múltiples valores son válidos únicamente cuando todos pueden asociarse con el mismo promotor objetivo y con la misma propiedad.

Si el paper contiene múltiples promotores y múltiples valores pero la correspondencia no puede resolverse:

```text
AMBIGUOUS
```

---

# 15. `value_raw`

Representa la forma original relevante en la que el valor aparece en el paper.

Ejemplos:

```text
42 bp upstream of the ATG
Sigma32
TAT AAT
```

Debe conservarse cuando exista una forma documental identificable.

---

# 16. `value_normalized`

Representa una forma reproducible para comparación o procesamiento.

Ejemplos:

```text
42 bp upstream of the ATG -> -42
Sigma32                   -> sigma32
TAT AAT                   -> TATAAT
```

La normalización debe:

- utilizar reglas previamente definidas;
- ser independiente del target;
- no corregir silenciosamente el valor;
- no introducir conocimiento biológico externo no expresado en el paper.

---

# 17. `qualifier`

Campo opcional que conserva el grado de certeza o naturaleza lingüística de la afirmación del paper.

Ejemplos:

```text
putative
predicted
possible
-like
appears to be
```

El sistema no debe convertir una afirmación débil en una afirmación categórica.

Ejemplo:

```text
A putative -10 box, TATGAT, was identified for P1.
```

puede producir:

```text
value = TATGAT
qualifier = putative
```

---

# 18. `derivation_note`

Se utiliza cuando es necesario explicar cómo se obtuvo una forma normalizada a partir de la expresión documental.

Ejemplo:

```text
value_raw:
42 bp upstream of the ATG

value_normalized:
-42

derivation_note:
ATG se interpretó como inicio de traducción;
upstream se representa con signo negativo.
```

Una derivación documental reproducible no equivale a una inferencia biológica.

---

# 19. Evidencia

Todo valor aceptado debe incluir evidencia producida por el sistema.

Conceptualmente:

```text
evidence_items = [...]
```

La evidencia puede ser:

- una oración;
- varias oraciones;
- contenido de tabla;
- caption;
- referencia a figura;
- texto asociado a figura;
- combinación de fragmentos.

La evidencia debe sustentar simultáneamente:

1. la propiedad;
2. el valor;
3. el promotor objetivo.

---

# 20. Relación valor-evidencia

Cuando existan múltiples valores, el sistema debe permitir determinar qué evidencia sustenta cada uno.

Conceptualmente:

```text
value_1
    -> evidence_A

value_2
    -> evidence_B
    -> evidence_C
```

No debe asumirse que todo fragmento sustenta automáticamente todos los valores.

---

# 21. `source_type`

Tipos iniciales:

```text
body_text
table
figure_caption
figure_reference
figure_associated_text
other
```

`source_type` describe la representación documental utilizada por el sistema.

No debe confundirse con `Modalidad_origen`, que pertenece al gold curatorial.

---

# 22. `source_location`

Debe conservar tanta localización como permita razonablemente la representación disponible.

Puede incluir:

```text
section
page
paragraph
table
figure
chunk_id
```

No todos son obligatorios.

No debe inventarse precisión inexistente.

---

# 23. Regla transversal: asociación con el promotor

Toda extracción positiva debe poder vincularse con el promotor objetivo.

En papers con varios promotores, no se permite asignar valores por:

- proximidad textual;
- orden de aparición;
- plausibilidad;
- similitud con RegulonDB;
- conocimiento previo del modelo.

---

# 24. Regla transversal: mención no equivale a valor

La existencia de una mención de la propiedad no implica que el paper proporcione el valor evaluado.

Ejemplo:

```text
P1 contains a typical -10 region.
```

puede justificar que se habla de una caja -10, pero no proporciona necesariamente su secuencia.

---

# 25. Regla transversal: no inferencia por conocimiento externo

No se permite completar valores mediante:

- genoma externo;
- RegulonDB;
- consenso;
- conocimiento biológico general;
- una propiedad relacionada;
- memoria paramétrica;
- otras fuentes no incluidas en la entrada.

---

# 26. Reglas específicas de TSS

## TSS-01 — Representaciones válidas

Un TSS puede estar representado mediante:

```text
relative_position
genomic_coordinate
designation
nucleotide
```

o una combinación de ellas.

---

## TSS-02 — Ancla normalizada de inicio de traducción

Cuando el contexto sea inequívoco, pueden tratarse como variantes de una misma referencia:

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

Debe conservarse:

```text
anchor_raw
```

`ATG` aislado no basta si el contexto no demuestra que corresponde al codón de inicio relevante.

---

## TSS-03 — Signo

Cuando existe un ancla válida:

```text
upstream   -> negativo
downstream -> positivo
```

Ejemplo:

```text
42 bp upstream of the ATG -> -42
```

---

## TSS-04 — Falta de ancla

Ejemplo:

```text
The TSS is 42 bp upstream.
```

Puede conservarse:

```text
distance = 42
direction = upstream
anchor = unknown
```

pero no debe producirse automáticamente:

```text
relative_position = -42
```

respecto al inicio de traducción.

---

## TSS-05 — `+1`

Una expresión como:

```text
The transcription start site (+1)...
```

puede utilizar `+1` como designación convencional del inicio de transcripción.

No debe convertirse automáticamente a:

```text
relative_position = +1
```

respecto al inicio de traducción.

---

## TSS-06 — Coordenada genómica absoluta

Una coordenada genómica absoluta reportada por el paper constituye una representación válida de TSS.

Ejemplo:

```text
The transcription start site is located at nucleotide 1234567.
```

puede producir:

```text
genomic_coordinate = 1234567
```

No debe transformarse a posición relativa utilizando información externa durante la extracción.

---

## TSS-07 — Múltiples TSS

Si varios TSS están inequívocamente asociados al mismo promotor, todos pueden extraerse.

Si la asociación no puede resolverse:

```text
AMBIGUOUS
```

---

## TSS-08 — Nucleótido del TSS

Si el paper proporciona explícitamente el nucleótido de inicio, puede conservarse.

Ejemplo:

```text
nucleotide = A
```

No debe reconstruirse consultando el genoma.

---

## TSS-09 — Técnica experimental

Puede conservarse cuando pueda asociarse correctamente al TSS/promotor.

Ejemplos:

```text
primer extension
S1 mapping
RACE
```

La técnica no es condición obligatoria para aceptar un valor de TSS suficientemente sustentado.

---

# 27. Reglas específicas de cajas -10 y -35

## BOX-01 — Valor principal

El valor principal es la secuencia nucleotídica que el paper asocia con la caja correspondiente del promotor.

---

## BOX-02 — Asociación obligatoria

Una secuencia sólo puede extraerse como caja -10/-35 si existe evidencia suficiente para asociarla:

1. con la propiedad correcta;
2. con el promotor objetivo.

---

## BOX-03 — Consenso general no es valor específico

Ejemplo:

```text
The consensus -10 sequence for sigma70 promoters is TATAAT.
```

no autoriza:

```text
P1 -10 = TATAAT
```

si el paper no realiza esa asociación.

---

## BOX-04 — Calificadores

Expresiones como:

```text
putative
predicted
possible
-10-like
-35-like
```

pueden conservarse si el paper asocia el valor con el promotor.

El calificativo debe mantenerse.

---

## BOX-05 — Longitud

**No existe todavía un mínimo definitivo de longitud para aceptar o puntuar una caja.**

El conjunto curatorial contiene casos muy cortos que requieren revisión antes de convertir la longitud en una regla excluyente.

Por tanto:

> La longitud puede utilizarse como señal descriptiva o diagnóstica, pero no debe invalidar automáticamente un valor durante esta fase.

Esta decisión reemplaza reglas provisionales anteriores de 3–20 nt o 6–20 nt.

---

## BOX-06 — Normalización permitida

Se permiten transformaciones tipográficas inequívocas:

```text
tataat  -> TATAAT
TAT AAT -> TATAAT
TAT-AAT -> TATAAT
```

sólo cuando espacios o separadores son claramente de presentación.

---

## BOX-07 — Normalización prohibida

No se permite:

```text
TATAAC -> TATAAT
```

por similitud con un consenso.

Tampoco se permite:

- corregir nucleótidos;
- completar secuencias;
- reconstruir desde el genoma;
- inferir desde TSS;
- inferir desde sigma;
- reemplazar por un consenso.

---

## BOX-08 — Múltiples cajas

Si el paper reporta varias secuencias válidas para la misma caja del mismo promotor, todas pueden conservarse.

Si no puede resolverse qué secuencia pertenece a qué promotor:

```text
AMBIGUOUS
```

---

## BOX-09 — Posición sin secuencia

Ejemplo:

```text
The -10 element is located from -12 to -7.
```

Esto aporta información documental sobre la caja, pero si el valor evaluado es la secuencia:

```text
status = INSUFFICIENT_EVIDENCE
```

No se debe reconstruir la secuencia externamente.

---

# 28. Reglas específicas de factor sigma

## SIG-01 — Asociación obligatoria

La presencia de un factor sigma en el paper no basta.

Debe existir evidencia suficiente para asociarlo con:

- el promotor objetivo;
- o su evento de transcripción.

---

## SIG-02 — Variantes tipográficas claras

Se permiten normalizaciones como:

```text
σ32
σ 32
sigma32
sigma 32
Sigma32
Sigma 32
SIGMA32
```

a:

```text
sigma32
```

Análogamente:

```text
σ54 / Sigma54 / sigma 54 -> sigma54
σF / SigmaF / sigma F    -> sigmaF
```

Siempre deben conservarse:

```text
value_raw
value_normalized
```

---

## SIG-03 — Equivalencias biológicas diferidas

No deben normalizarse automáticamente, por ahora:

```text
RpoS <-> sigmaS <-> sigma38
RpoH <-> sigma32
RpoN <-> sigma54
```

Aunque puedan representar equivalencias biológicas conocidas, esas conversiones requieren una tabla explícita, global y versionada antes de utilizarse en evaluación.

---

## SIG-04 — Múltiples factores sigma

Si el mismo promotor está inequívocamente asociado con más de un factor sigma, todos pueden extraerse.

---

# 29. Consistencia mínima entre `status`, valores y evidencia

| Status | Valores aceptados | Evidencia |
|---|---:|---|
| `EXTRACTED` | uno o más | obligatoria |
| `NOT_FOUND` | cero | normalmente vacía |
| `INSUFFICIENT_EVIDENCE` | cero | obligatoria |
| `UNSUPPORTED_MODALITY` | cero | evidencia o puntero documental requerido |
| `AMBIGUOUS` | cero valores aceptados; candidatos opcionales | obligatoria |
| `INVALID_CANDIDATE` | cero valores aceptados; candidato opcional | recomendable |

---

# 30. Evidencia curatorial vs. evidencia del sistema

El gold histórico no contiene sistemáticamente la frase o fragmento utilizado por el curador.

Esto **no elimina** el requisito de evidencia para el extractor.

La separación es:

```text
GOLD
├── valor curatorial
└── modalidad curatorial

SYSTEM
├── valor
├── evidencia
├── localización
└── status
```

La evidencia del sistema se utiliza para trazabilidad y revisión humana.

No se exige coincidencia automática contra una frase gold inexistente.

---

# 31. `imagen_only`

`Modalidad_origen = imagen_only` describe cómo el curador encontró originalmente el valor.

No determina por sí sola la capacidad del extractor.

Un registro `imagen_only` puede ser extraído desde TEI/TXT cuando éstos conserven:

- caption;
- texto asociado a figura;
- referencias con valor;
- contenido extraído de la figura.

Por tanto:

```text
gold modality = imagen_only
system status = EXTRACTED
```

es perfectamente válido.

---

# 32. Información ausente del paper

Si un valor histórico proviene de otro paper o no puede establecerse en el paper evaluado, el extractor no debe intentar reproducirlo por conocimiento externo.

La tarea es:

> **¿qué puede sustentarse en este paper?**

No se utiliza `PMID_fuente_alternativa` en el contrato actual.

---

# 33. Criterios de validez de una extracción positiva

Una extracción positiva es científicamente válida cuando:

1. corresponde al paper analizado;
2. corresponde al promotor objetivo;
3. corresponde a la propiedad correcta;
4. contiene al menos un valor;
5. contiene evidencia;
6. no requiere conocimiento externo para completar el valor;
7. respeta las reglas de normalización vigentes;
8. conserva incertidumbre expresada por el paper;
9. no utiliza targets del gold o RegulonDB.

---

# 34. Criterios de aceptación del extractor

El extractor cumple el contrato cuando:

- produce un resultado independiente por propiedad;
- soporta cero, uno o múltiples valores;
- todo `EXTRACTED` contiene evidencia;
- diferencia `value_raw` y `value_normalized`;
- conserva calificadores;
- puede abstenerse;
- puede marcar ambigüedad;
- no fuerza valores en casos insuficientes;
- no utiliza valores objetivo;
- no reconstruye información mediante conocimiento externo;
- mantiene asociación con el promotor;
- produce una salida validable programáticamente.

---

# 35. Decisiones abiertas

Antes de congelar la versión final deberán revisarse:

1. tratamiento definitivo de cajas extremadamente cortas;
2. representación técnica final de múltiples valores;
3. vocabulario técnico definitivo de TSS;
4. equivalencias biológicas adicionales de sigma;
5. tratamiento final de `INVALID_CANDIDATE`;
6. estructura técnica definitiva de evidencia y localización;
7. normalizaciones finales utilizadas para scoring.

---

# 36. Principio rector

> **El extractor no debe producir el valor biológicamente más plausible ni el valor que espera RegulonDB. Debe producir únicamente aquello que pueda sustentarse en la representación disponible del artículo para el promotor y la propiedad evaluados, mostrando la evidencia que justifica la conclusión y absteniéndose cuando esa conclusión no pueda establecerse de forma responsable.**
