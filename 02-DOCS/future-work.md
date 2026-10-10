# promoter-ai-extraction — Propuesta de ampliación incremental

**Estado:** propuesta de trabajo futuro, posterior a la integración de la aplicación inicial en `main` (PR #4).  
**Propósito:** evolucionar el prototipo de extracción trazable de información sobre promotores bacterianos hasta convertirlo en una herramienta evaluada científicamente, aplicable a colecciones documentales y útil para la curación.  
**Alcance actual:** extracción de TSS, caja −10, caja −35 y factor sigma de artículos asociados a promotores conocidos, con evidencia, validación, persistencia y modalidades guiada/agente.  
**Principio de desarrollo:** cada incremento debe ofrecer un resultado verificable y proporcionar evidencia para decidir el siguiente. No modificar los contratos científicos vigentes sin revisión y autorización explícitas.

## 1. Principios transversales

1. **Separar extracción y evaluación.** El extractor nunca recibe valores de referencia del gold set. Primero se generan y persisten predicciones; después se compara con el gold en un proceso separado.
2. **Preservar la trazabilidad.** Cada valor debe conservar artículo, promotor, fragmento o región de evidencia, ubicación, valor original, normalización y justificación.
3. **Distinguir los estados.** `NOT_FOUND` científico no equivale a un fallo técnico; un candidato inválido es un diagnóstico, no una predicción positiva.
4. **Mantener la unidad de análisis.** Extracción por artículo × promotor; evaluación por artículo × promotor × propiedad. Al consolidar literatura, conservar el origen de cada observación.
5. **No inventar certeza.** La ausencia de una propiedad en el gold no es automáticamente un negativo verificado. Evitar presentar tasas de pruebas unitarias como métricas de precisión científica.
6. **No sobreadaptar el sistema.** Empezar por defectos observados y mediciones. No diseñar reglas por organismo o intervenciones multimodales antes de comprobar su necesidad.
7. **Preservar resultados y confidencialidad.** Predicciones originales inmutables; credenciales, artículos privados, gold y resultados locales fuera del repositorio público.
8. **Control humano del desarrollo.** Definir alcance y criterios antes de implementar cada incremento, ejecutar verificaciones y revisar cambios antes de commits, PR y merge.

## 2. Secuencia de incrementos

| Orden | Incremento | Entregable principal | Depende de |
|---|---|---|---|
| **I1** | Corregir y verificar la normalización del TSS | Conversión con anclas explícitas y regresiones probadas | Sistema actual |
| **I2** | Ejecutar extracción por lotes | Predicciones independientes y persistidas para varios artículos/promotores | I1 |
| **I3** | Ejecutar benchmark contra el gold | Métricas científicas y reporte reproducible | I2 |
| **I4** | Analizar errores | Taxonomía y evidencia de fallos por propiedad | I3 |
| **I5** | Aplicar mejoras dirigidas y reevaluar | Nueva comparación contra el baseline congelado | I4 |
| **I6** | Probar transferencia a organismos cercanos | Piloto multiorganismo sin exigir gold | I5 como línea base; piloto exploratorio posible antes |
| **I7** | Incorporar flujo de revisión curatorial | Revisión de candidatos y registro de decisiones humanas | I2/I6 según caso de uso |
| **I8** | Incorporar extracción multimodal desde PDF | Evidencia de figuras/tablas con ubicación y revisión | I4 e I7 recomendados |
| **I9** | Comparar con bases de datos y preparar integración | Detección de novedades/discrepancias con validación curatorial | I7; I8 según cobertura |

Las dependencias reflejan el orden recomendado, no una prohibición absoluta de realizar prototipos exploratorios en paralelo.

## I1. Corrección y verificación de la normalización del TSS

**Motivación.** En la extracción exploratoria del PMID `1372899`, promotor `glpFp`, se recuperó la frase equivalente a «71 base pairs upstream from the translation start codon», pero no quedó normalizada como **−71**. Hay que localizar la causa real (identificación de ancla, interpretación, validación o normalización), sin asumir que el problema se soluciona cambiando solo el prompt.

**Alcance propuesto.**

- Reconocer distancias upstream/downstream respecto al inicio de traducción o codón de inicio **cuando exista un ancla explícita válida**.
- Normalizar upstream como negativo y downstream como positivo, conservando el valor textual sin alterarlo.
- No convertir posiciones `+1` ni distancias referidas únicamente a TSS u otras anclas que no permitan establecer la posición relativa al inicio de traducción.
- Rechazar o abstenerse ante ambigüedad sin inventar coordenadas.
- Agregar pruebas sintéticas de casos válidos, inválidos y límites; utilizar el caso real como comprobación controlada sin versionar el artículo ni el gold.

**Entregables.** Diagnóstico de la causa; corrección acotada; pruebas de regresión; evidencia del resultado en la ejecución controlada.

**Criterio de aceptación.** Una evidencia correctamente anclada que indique «71 bp upstream of the translation start codon» produce `−71`; los casos sin ancla válida siguen sin normalizarse. La regresión existente continúa aprobando.

## I2. Procesamiento por lotes de artículos y promotores

**Objetivo.** Pasar de ejecuciones unitarias a procesar colecciones con entradas definidas por artículo, promotor conocido y alias opcionales, sin exponer el gold al extractor.

**Alcance propuesto.**

- Aceptar un manifiesto de trabajo para múltiples pares artículo × promotor, con origen del documento (TEI/TXT) y metadatos mínimos.
- Utilizar las modalidades existentes sin alterar su contrato científico; conservar resultados individualizados por artículo y promotor.
- Registrar estado de ejecución, errores técnicos, abstenciones, versión de configuración/modelo y consumo si el proveedor lo informa.
- Poder retomar trabajo sin sobrescribir predicciones ya persistidas y sin duplicar llamadas pagadas accidentalmente.
- Definir límites de concurrencia, presupuesto y políticas explícitas de ejecución; la primera implementación puede ser secuencial.

**Entregables.** Ejecutor de lotes, manifiesto de entradas, índice/reporte de ejecución y predicciones persistidas individualmente.

**Criterio de aceptación.** Un lote controlado produce resultados independientes y trazables; una falla individual no destruye las demás predicciones; repetir un lote no sobrescribe archivos existentes.

## I3. Benchmark científico reproducible contra el gold

**Objetivo.** Medir el desempeño real del extractor sobre la referencia curada de *E. coli*, una vez corregido el defecto conocido del TSS y habilitada la ejecución por lotes.

**Protocolo propuesto.**

- Congelar versión de código, prompts, modelo, configuración, entradas y reglas de comparación antes de ejecutar.
- Generar y persistir todas las predicciones **antes** de cargar los valores gold en la etapa de evaluación.
- Evaluar por **artículo × promotor × propiedad**: TSS, −10, −35 y sigma, con normalizaciones definidas en el contrato de evaluación.
- Reportar TP, FP, FN, precisión, recall y F1 según el contrato. Cuando se predice un valor incorrecto para un valor gold positivo, documentar tanto el falso positivo como el valor omitido (falso negativo) según el esquema aplicable.
- Separar errores técnicos, candidatos inválidos y abstenciones científicas; los errores técnicos para casos positivos deben reflejarse en el desempeño extremo a extremo, no desaparecer del denominador.
- No inferir TN automáticamente a partir de celdas vacías o datos no curados.
- Reportar cobertura, costos, tiempos y resultados por modalidad; distinguir pruebas de software de calidad científica.

**Entregables.** Dataset de predicciones congeladas, reporte de métricas reproducible, resumen por propiedad/modalidad y referencias a la configuración y a los artefactos locales de evaluación.

**Criterio de aceptación.** El benchmark puede repetirse con las mismas entradas y versión; las métricas y denominadores son auditables y ningún valor gold se filtra a inferencia.

## I4. Diagnóstico científico y técnico de errores

**Objetivo.** Explicar *por qué* falla cada propiedad antes de modificar el sistema.

**Categorías iniciales de análisis:** evidencia no recuperada por RAG; información en párrafos separados; ancla TSS ausente o mal interpretada; diferencia entre extracción y normalización; ambigüedad en nombre de promotor/gen; factores sigma con nomenclatura variable; discrepancia texto–figura; información solo en tablas/figuras; errores de formato o del proveedor; anotación gold no comparable o incompleta.

**Entregables.** Taxonomía de errores, casos representativos con evidencia, distribución por propiedad y lista priorizada de intervenciones justificadas.

**Criterio de aceptación.** Cada mejora candidata señala fallos observados y cómo se medirá si fueron resueltos.

## I5. Mejoras dirigidas y nueva evaluación

**Objetivo.** Mejorar el sistema de forma controlada, no mediante cambios simultáneos difíciles de atribuir.

**Alcance propuesto.** Según el diagnóstico: mejorar búsqueda y selección de evidencia, interpretación de anclas, validaciones, prompts, herramientas del agente, manejo de alias o normalización de sigma/cajas. Mantener pruebas de regresión para casos previamente correctos. Comparar en condiciones equivalentes con el baseline congelado.

**Entregables.** Mejoras delimitadas, pruebas y reporte comparativo antes/después por propiedad y modalidad.

**Criterio de aceptación.** Las mejoras presentan evidencia verificable y no introducen regresiones científicas o técnicas no justificadas.

## I6. Transferencia a organismos bacterianos cercanos a *E. coli*

**Objetivo.** Evaluar qué tan bien se generalizan prompts, reglas, RAG y agente a organismos filogenéticamente próximos a *E. coli*, **sin requerir un gold set previo**.

**Estrategia: transferencia primero, adaptación después.**

1. Seleccionar un conjunto pequeño y diverso de artículos de organismos objetivo, con promotores conocidos e identificación de especie/cepa cuando esté disponible.
2. Ejecutar inicialmente el extractor existente **sin cambiar prompts ni reglas**; el procesamiento inicial puede ser documento por documento si aún no se requiere un lote.
3. Registrar evidencia y predicción por artículo/promotor/organismo, sin interpretar automáticamente que una extracción validada estructuralmente está confirmada por un curador.
4. Realizar revisión científica manual de una muestra, incluso sin gold, y cuantificar los hallazgos revisados sin presentarlos como benchmark completo.
5. Identificar nomenclaturas y reglas que necesitan adaptación reproducible, especialmente sigma y elementos promotores; adaptar solo después de observar los fallos.

**Entregables.** Piloto documentado de transferencia, hallazgos por propiedad y organismo, y necesidades de adaptación concretas. Las revisiones aceptadas podrían formar posteriormente un conjunto de referencia independiente.

**Criterio de aceptación.** Se conoce qué casos funcionan con las reglas actuales y dónde dejan de ser aplicables; las conclusiones no extrapolan más allá de la muestra.

**Decisión científica.** El organismo actúa inicialmente como contexto y metadato de procedencia, no como motivo automático para rechazar una extracción. **No se incluye descubrimiento de promotores nuevos** a partir de secuencias genómicas.

## I7. Flujo de revisión curatorial sin dependencia del gold

**Objetivo.** Permitir que los curadores examinen y validen extracciones en artículos para los que no hay referencia previa.

**Alcance propuesto.** Presentar valores raw y normalizados, evidencia, ubicación, procedencia y estado; registrar decisiones humanas (aceptar, corregir, rechazar, pendiente) junto con motivos y referencia a la predicción original inmutable. Manejar múltiples artículos y discrepancias sin fusionar evidencia automáticamente. Distinguir claramente **predicción automática**, **resultado revisado** y **anotación aceptada para una base de datos**.

**Entregables.** Modelo de decisiones curatoriales, interfaz o reporte de revisión y exportación controlada de resultados revisados.

**Criterio de aceptación.** Una decisión humana no modifica ni borra la predicción fuente y mantiene auditable quién decidió qué y con base en cuál evidencia.

## I8. Extracción multimodal a partir de PDF

**Objetivo.** Incorporar TSS, cajas −10/−35 y sigma reportados en figuras, alineamientos, tablas o imágenes que no estén adecuadamente representados en TEI/TXT.

**Decisión de entrada.** **El PDF original es suficiente como entrada. No se exige una colección previa de imágenes descargadas.** Según el proveedor y el caso, el sistema puede enviar el PDF a un modelo con capacidad visual o renderizar automáticamente las páginas/recortes pertinentes.

**Estrategia incremental recomendada.**

1. Mantener la extracción textual existente como primera pasada.
2. Detectar faltantes, ambigüedades y referencias a figuras/tablas a partir de texto y leyendas.
3. Probar análisis visual selectivo de páginas relevantes, ya sea con PDF directo o con renderización automática a imagen.
4. Relacionar cada valor con PDF, página, figura/tabla y región cuando sea posible; conservar el recorte y la leyenda como evidencia auditable.
5. Comparar lo obtenido del texto y de la imagen **sin asumir que uno siempre es correcto**; enviar discrepancias a revisión curatorial.
6. Solo si aporta valor, automatizar extracción individual de figuras y almacenamiento de recortes a escala.

**Precauciones.** La lectura de nucleótidos a partir de imágenes puede confundir bases o posiciones; no aceptar silenciosamente secuencias visuales contradictorias. Considerar límites de tamaño, costos, derechos de acceso a PDFs y variabilidad de proveedores multimodales.

**Entregables.** Piloto PDF multimodal, evidencias visuales localizadas y análisis comparativo texto/imagen.

**Criterio de aceptación.** Al menos un conjunto controlado de casos de figura/tabla puede revisarse y rastrearse hasta su fuente exacta, sin perder resultados textuales originales.

## I9. Comparación con bases de datos e integración curatorial

**Objetivo.** Pasar de extraer evidencia de publicaciones a detectar información que merezca revisión para su eventual incorporación a una base de conocimiento, como RegulonDB u otras bases pertinentes.

**Alcance propuesto.** Comparar resultados curatorialmente revisados contra registros existentes, con identificadores estables de organismo, cepa, gen y promotor. Clasificar hallazgos en coincidencia, discrepancia, posible novedad e insuficiencia de evidencia, evitando declarar automáticamente que una propiedad ausente en una base es biológicamente nueva. Generar propuestas de anotación con trazabilidad y aprobación humana.

**Entregables.** Reporte de diferencias, mecanismo de revisión y formato de propuesta de anotación.

**Criterio de aceptación.** Ninguna extracción automática se incorpora a la base sin revisión y autorización del flujo curatorial correspondiente.

## 3. Actividades transversales

**Calidad y reproducibilidad.** Tests unitarios e integrados, registros de configuraciones, congelación de versiones, separación entre datos de prueba sintéticos y documentos reales, métricas por modalidad y criterios de aceptación de cada incremento.

**Costos y rendimiento.** Medir llamadas, tokens, latencia y costo especialmente desde I2; establecer presupuestos y evitar ejecuciones pagadas no autorizadas. Comparar modelos o agentes cuando se disponga de una línea base reproducible, no como sustituto de la evaluación científica.

**Gobierno de datos y operación.** Privacidad y permisos de documentos, acceso a PDFs, manejo seguro de claves, retención de evidencia, no sobrescritura de predicciones y control humano sobre Git y despliegues.

**Documentación y mantenimiento.** Distinguir capacidades implementadas de propuestas. Registrar decisiones relevantes en notas breves y referenciar commits/PR en lugar de archivar indiscriminadamente todas las conversaciones con agentes.

## 4. Puertas de decisión entre incrementos

- **I1 → I2:** conversión de TSS verificada y reglas de abstención preservadas.
- **I2 → I3:** lote reproducible, errores técnicos visibles y resultados guardados antes de evaluar.
- **I3 → I4:** métricas calculadas con denominadores y definiciones auditables.
- **I4 → I5:** errores priorizados con causas y casos de regresión.
- **I5 → I6:** línea base conocida; no se exige alcanzar una cifra arbitraria, sí comprender sus límites.
- **I6 → I7:** necesidades curatoriales y metadatos de otros organismos identificados; I7 también puede avanzar si existen necesidades inmediatas de revisión.
- **I7 → I8:** flujo disponible para resolver discrepancias visuales; se permite un piloto técnico previo si se controla manualmente la evidencia.
- **I8 → I9:** evidencia multimodal auditada cuando sea relevante; I9 puede empezar con resultados solo textuales revisados.

## 5. Primer trabajo a iniciar

**Definir formalmente I1 como una corrección delimitada**, con reproducción del caso de `1372899/glpFp`, diagnóstico de la etapa que falla, pruebas positivas y negativas de anclaje, corrección sin alterar contratos científicos y regresión completa. El caso del artículo se usa como evidencia científica local y no como fixture versionado ni como dato proporcionado a inferencia desde el gold.

Tras aprobar I1, definir I2 junto con el protocolo de I3 para que el diseño de lotes capture desde el principio los identificadores, estados y metadatos necesarios para un benchmark auditable. No abrir ahora una implementación simultánea de I6–I9.

## 6. Fuera de alcance actual y decisiones pendientes

- Identificación automática de **promotores desconocidos** sin nombre/identidad de partida.
- Modificación de los seis contratos científicos raíz sin revisión formal.
- Suposición de que un resultado sin gold es incorrecto, o que una extracción automática constituye una anotación curada.
- Elección anticipada de organismos específicos, modelos multimodales, arquitectura de despliegue o presupuestos: deberán definirse cuando el incremento correspondiente lo requiera.

---

*Documento de planificación. No representa funcionalidades ya implementadas ni resultados de evaluación científica obtenidos. La versión inicial del software está integrada; las iniciativas I1–I9 son propuestas sujetas a especificación y aprobación incremental.*
