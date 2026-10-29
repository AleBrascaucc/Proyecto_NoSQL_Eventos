# 2. Consultas del dominio

En scripts/03_consultas.js cada consulta imprime enunciado, requisito cubierto y
resultado esperado. Todas son de solo lectura. La evidencia real esta en
anexo/consultas_modelo.txt (regenerada tras corregir la agrupacion de la consulta 7).

| N.º | Pregunta | Herramienta principal | Resultado inicial verificado |
|---:|---|---|---|
| 1 | Eventos con precio entre 4000 y 8000 | $gte, $lte, proyeccion, sort | 9 eventos |
| 2 | Eventos de noviembre de 2026 | Rango ISODate | 15 eventos |
| 3 | Publicados con vacantes, gratuitos o de Tecnologia | AND implicito, $or | 4 eventos |
| 4 | Eventos en Cordoba | Notacion sede.ciudad | 5 eventos |
| 5 | Eventos con taller intermedio | $elemMatch | 10 eventos |
| 6 | Proximos cinco publicados | Fecha actual, sort, limit | 5 en la fecha de prueba; depende del dia |
| 7 | Confirmadas que seleccionan cada actividad de cada evento | $match, $unwind, $group | 35 pares evento/actividad |
| 8 | Recaudacion bruta mensual por fecha de inscripcion | $dateTrunc, $sum | Agosto: 234000; septiembre: 0; octubre: 555000 |
| 9 | Promedio, minimo y maximo de precios por categoria | $avg, $min, $max | 4 categorias, 5 eventos por categoria |
| 10 | Confirmadas y ocupacion por evento | $lookup y porcentaje | 20 eventos; Emprendimientos 3 al 100% |
| 11 | Publicados compatibles con javascript y git | $expr, $setIsSubset | 5 eventos, incluidos requisitos vacios |
| 12 | Conocimientos mas frecuentes en confirmadas | $unwind, $group | 8 conocimientos; excel primero con 72 |

Los valores de esta tabla corresponden al poblado inicial de 20/200, no al estado
posterior de 22/201. La demo aporta eventos y una inscripcion cancelada y puede
alterar conteos de eventos/precios. No se recalcularon todos los indicadores luego
de la demo. La consulta 10 incluye todos los estados como control; I2 del analisis
excluira borradores y cancelados.

ACT-01/ACT-02 son codigos locales a cada evento, no identificadores globales de
actividades. Por eso I1 agrupa por evento_id y codigo, no solamente por codigo.
Las frecuencias de conocimientos cuentan inscripciones, no personas distintas
entre eventos, y cada inscripcion puede aportar a varios conocimientos.
