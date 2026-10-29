# 5. Indicadores: definicion y trabajo pendiente

analisis/analisis.ipynb es un ESQUELETO sin resultados ni graficos ejecutados.
La conexion se realiza desde la PC anfitriona a localhost:27018; la API dentro
de Docker usa mongo:27017. No intercambiar estos hostnames.

| Indicador | Unidad | Poblacion / regla | Salida prevista |
|---|---|---|---|
| I1. Demanda por actividad | Cantidad de selecciones | Inscripciones confirmadas; agrupar por evento_id y codigo de actividad | Tabla y grafico de barras |
| I2. Ocupacion por evento | Porcentaje | Confirmadas/capacidad_total * 100; excluir borradores y cancelados | Tabla e interpretacion |
| I3. Recaudacion bruta mensual | Importe monetario | Sumar importe_abonado por mes UTC de fecha_inscripcion; incluir canceladas | Tabla y grafico de lineas |

I1 no cuenta personas que solo se inscribieron sin seleccionar actividades. Una
inscripcion puede elegir varias actividades. No sumar ACT-01 de distintos eventos
como si fuera una misma actividad. Debe aclararse si el grafico muestra todas las
actividades o una seleccion de las mas demandadas.

I2 incluye publicados y finalizados; la capacidad es el denominador, no las
vacantes. La ocupacion de eventos finalizados se interpreta como registro final,
no como disponibilidad para inscribirse. Los eventos sin confirmadas tienen 0%.

I3 es recaudacion BRUTA registrada, no ganancia ni ingreso neto; no registra
reembolsos. Los importes son Decimal128. Mantener Decimal durante las sumas y
convertir a float solo para graficar. El resultado inicial de consultas fue
234000 en agosto, 0 en septiembre y 555000 en octubre de 2026; estos resultados
no sustituyen la futura ejecucion del notebook.

Antes del analisis decidir y documentar el corte: poblado inicial 20/200 o estado
posterior a la demo 22/201. No mezclar tablas o graficos de cortes diferentes.
La base actual conserva los datos de demo; no se recarga desde el notebook.
