# 6. Resultados y conclusiones

## Corte y evidencia

Los tres indicadores se ejecutaron mediante scripts de solo lectura el 29/10/2026.
Las tres ejecuciones informaron la misma base gestion_eventos, con 22 eventos y
201 inscripciones. Tienen instantaneas independientes, no un unico snapshot
compartido. No se reportaron escrituras entre esas ejecuciones; los totales
coinciden, aunque su igualdad por si sola no demuestra que no hubo modificaciones.

| Indicador | Hora UTC de ejecucion | Carpeta bajo analisis/resultados/ |
|---|---|---|
| I1 | 21:27:27 | I1_20261029T212727_657083Z |
| I2 | 21:33:39 | I2_20261029T213339_071414Z |
| I3 | 21:42:34 | I3_20261029T214234_750726Z |

Las carpetas contienen tablas CSV, interpretaciones y corte.json. I1 e I3 incluyen
PNG y SVG (dos formatos de una misma figura). Los dos PNG reales se revisaron en
la conversacion. Del I2 se reviso el resumen CORTE compartido por el usuario.
No se atribuyen salidas ejecutadas al notebook hasta que este se ejecute y guarde.

## I1. Demanda por actividad

152 inscripciones confirmadas; 52 no seleccionaron actividades. Las otras 100
aportaron 147 selecciones distribuidas en 35 pares evento/actividad. La actividad
con mas selecciones fue Emprendimientos 3 / ACT-01, con 8.

La unidad es una seleccion de actividad en una inscripcion confirmada; no un
asistente efectivo ni una persona unica entre eventos. Cada inscripcion puede
elegir varias actividades. ACT-01 es local al evento, por lo que se agrupa con
evento_id. Los grupos sin selecciones no aparecen en el grafico. Se conservan
confirmadas de eventos cancelados como demanda historica.

## I2. Ocupacion

Se incluyeron 17 eventos publicados/finalizados y se excluyeron 5 borradores o
cancelados. Los incluidos tienen 682 lugares, 143 confirmadas y 539 vacantes.

| Medida | Calculo | Resultado |
|---|---|---:|
| Ocupacion global ponderada | 100 * 143 / 682 | 20,97% |
| Promedio simple por evento | Media de porcentajes individuales sin ponderar | 25,12% |

El promedio simple da igual peso a eventos de diferente capacidad. No debe
confundirse con el global. La diferencia de 9 confirmadas respecto a I1 proviene
del evento cancelado original, excluido de I2. En finalizados, el porcentaje es
registro final de reservas; no disponibilidad actual ni asistencia comprobada.

## I3. Recaudacion bruta registrada

| Mes UTC de inscripcion | Importe bruto | Inscripciones | Canceladas | Importe de canceladas incluido |
|---|---:|---:|---:|---:|
| 2026-08 | 234000,00 | 55 | 15 | 52000,00 |
| 2026-09 | 0,00 | 1 | 0 | 0,00 |
| 2026-10 | 555000,00 | 145 | 34 | 92000,00 |
| Total | 789000,00 | 201 | 49 | 144000,00 |

Octubre concentra el mayor importe. Septiembre contiene una inscripcion de
importe cero; cero recaudado no equivale a cero inscripciones. Se agrupa por
fecha de inscripcion, no por fecha del evento. Las 49 canceladas se incluyen;
sus 144000 no se restan. No hay devoluciones registradas que permitan calcular
un neto. Tampoco se deducen costos, impuestos o comisiones.

Los valores son unidades monetarias del dataset, sin conversion de moneda.
La linea une totales mensuales observados; no representa valores diarios ni
una proyeccion. Los calculos conservan Decimal; float se usa solo al graficar.

## Conclusiones del proyecto

El modelo mixto permite consultar sede/actividades junto al evento y mantener
inscripciones independientes. El indice unico por evento y DNI protege la
unicidad, y las transacciones vinculan cambios de inscripcion y cupo. La demo
manual mostro el rechazo por conocimientos faltantes sin descontar cupo y la
cancelacion repetida sin restituir dos veces. El control final dio nueve ceros.

Las comparaciones de indices conservaron nReturned y redujeron documentos
examinados: 20 a 4, 200 a 1 y 20 a 4. Fueron planes forzados con hint; no se
midio una mejora temporal ni se afirma que el optimizador los elija siempre.

Demanda, ocupacion e importe son dimensiones diferentes. Una actividad puede
recibir varias selecciones por evento y un evento gratuito puede tener cupos
ocupados sin recaudar. Estos indicadores apoyan descripcion, no causalidad.

## Limites y pendientes

Datos ficticios y poblacion pequena. No se probaron carga concurrente, caidas de
servidor, restauracion del backup ni elecciones de un nuevo primario. Un replica
set de un nodo habilita transacciones pero no aporta redundancia. No hay
cobros reales, reembolsos ni autenticacion de actores.

El commit previo 3cb55a7 guarda la etapa de API y estructura. El analisis posterior
requiere revision y nuevo commit. Faltan guardar/revisar la ejecucion del notebook,
preparar la presentacion y publicar la rama. Las pruebas manuales de Postman no
se presentan como un reporte consolidado exportado del Runner.


## Notebook ejecutado y comprobado

El 29/10/2026 se ejecuto el notebook completo: 6 celdas de codigo ejecutadas y 0 errores guardados. Contiene las salidas reales de I1, I2 e I3. Las referencias anteriores a ejecucion pendiente describen etapas previas. Quedan pendientes guardar el commit del analisis, la presentacion y la publicacion de la rama.
