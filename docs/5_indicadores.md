# 5. Indicadores: definicion y trabajo pendiente

I1, I2 e I3 se ejecutaron y verificaron mediante scripts contra MongoDB. El notebook conserva los tres indicadores
sin salidas precargadas.
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

## Ejecucion de I1

El script analisis/i1_demanda.py realiza conteos y agregacion sobre una misma
instantanea de lectura (read concern snapshot); no modifica colecciones. La
conexion es desde la PC a localhost:27018, usando .env local si existe.

Genera una carpeta nueva en analisis/resultados/I1_<fecha_UTC>/ con:
- i1_demanda.csv: tabla completa ordenada por cantidad descendente.
- i1_demanda.png: barras horizontales, 300 dpi, todos los pares con demanda positiva.
- i1_demanda.svg: version vectorial del mismo grafico.
- corte.json: fecha de ejecucion, base, totales, reglas y conteos.
- i1_interpretacion.md: interpretacion calculada desde los resultados obtenidos.

Las dos imagenes son dos formatos del MISMO grafico I1, no dos indicadores.
La fecha almacenada es la hora de ejecucion, no un timestamp interno de MongoDB;
los conteos y la agregacion comparten la instantanea de la transaccion de lectura.

Solo se filtran inscripciones confirmadas: los eventos cancelados del poblado
que conservan confirmadas aportan demanda historica. No se excluyen eventos por
titulo ni se recarga el poblado. La inscripcion cancelada de la demo no aporta.
Las actividades sin selecciones no aparecen como grupos.

Con los datos de prueba se verificaron 35 grupos y 147 selecciones, provenientes
de 100 de las 152 inscripciones confirmadas (52 sin actividad). Es un control
local con el generador, NO una ejecucion nueva contra la base del usuario.
El resultado real y su corte se comprobaran despues de ejecutar el script alli.

## I1: ejecucion real comprobada

El usuario ejecuto I1 el 29/10/2026, corte UTC 21:27:27, con 22 eventos y 201
inscripciones. Resultado: 152 confirmadas, 52 sin actividad, 147 selecciones en
35 pares evento/actividad. Se reviso el PNG real: Emprendimientos 3 / ACT-01
encabeza con 8. Evidencia local en analisis/resultados/I1_20261029T212727_657083Z/.

## I2: implementacion y ejecucion pendiente

analisis/i2_ocupacion.py consulta publicados y finalizados, cuenta confirmadas por
evento y calcula porcentaje con Decimal. Rechaza capacidades no positivas, cupos
inconsistentes y eventos repetidos. Incluye ocupacion cero. Las lecturas comparten
una instantanea snapshot, sin escrituras en MongoDB.

Exporta i2_ocupacion.csv, corte.json e i2_interpretacion.md en una carpeta nueva
analisis/resultados/I2_<fecha>/. El notebook conserva I1 y agrega la celda I2.
No se agrega un tercer grafico: se mantienen barras para I1 y lineas para I3.

La ocupacion global es 100 * suma(confirmadas) / suma(capacidades). El promedio
simple calcula los porcentajes por evento y luego su media sin ponderar; ambos
se muestran con dos decimales y se calculan antes de redondear las filas.

En el generador local: 17 eventos elegibles, capacidad 682, 143 confirmadas y 539
vacantes; global 20,97%, promedio simple 25,12%. Emprendimientos 3 tiene 100%.
Son referencias de prueba; no se presentan como una ejecucion real nueva de I2.
Si los estados no cambiaron, los dos eventos de demo (borrador/cancelado) no
aportan a I2. Las 9 confirmadas del evento cancelado original se excluyen: por
eso I2 puede usar 143 confirmadas mientras I1 considera 152.

## I2: resumen real comprobado

Corte UTC 29/10/2026 21:33:39: 22 eventos y 201 inscripciones; 17 eventos elegibles,
5 excluidos, capacidad 682, confirmadas incluidas 143 y vacantes 539. Global
20,97% y promedio simple 25,12%. Evidencia en
analisis/resultados/I2_20261029T213339_071414Z/. El usuario compartio el resumen CORTE.

## I3: implementacion, pendiente de ejecucion real

analisis/i3_recaudacion.py suma por mes UTC de fecha_inscripcion, sin filtrar
estado de inscripcion ni de evento. Usa Decimal128/Decimal y comprueba tipos,
importes no negativos, conteos y correspondencia con el total de inscripciones.
Las lecturas de conteos y agregacion comparten snapshot; no hay escrituras.

Exporta tabla CSV, corte.json, interpretacion Markdown y grafico de lineas en
PNG 300 dpi y SVG. Ambos formatos son la misma figura I3. Conserva los resultados
de I1 e I2 y crea una carpeta nueva I3_<fecha>/ por ejecucion.

La serie muestra todos los meses entre el primero y el ultimo observado. Los
meses intermedios sin registros se rellenan con cero y una marca explicita; no
se agregan periodos fuera del intervalo. Septiembre del poblado tiene importe
cero pero una inscripcion, por lo que no es un mes sin registros.

Control local con el generador (no una nueva lectura de MongoDB): agosto 234000,
septiembre 0 y octubre 555000; total bruto 789000. Las 48 canceladas iniciales
registran 144000, incluidos dentro del bruto, no deducidos. La demo agrega una
cancelada gratuita en octubre: si nada cambio, se esperan 201 registros en I3
(55, 1 y 145 por mes), 49 cancelados y el mismo importe bruto.

Esos valores deben confirmarse con la ejecucion real de I3 antes de cerrar el
informe. Las fechas son de inscripcion, no del evento, y la linea no implica
interpolacion diaria ni proyeccion. El importe no es beneficio ni ingreso neto.

## I3: ejecucion real comprobada

Corte UTC 29/10/2026 21:42:34: 22 eventos y 201 inscripciones; agosto 234000
(55 inscripciones), septiembre 0 (1) y octubre 555000 (145). Bruto total 789000;
49 canceladas con importe registrado 144000, incluido sin deducir. El PNG real
fue revisado. Evidencia en analisis/resultados/I3_20261029T214234_750726Z/.

Los apartados previos titulados como pendientes describen la fase de implementacion.
Este registro y docs/6_resultados.md documentan el estado real posterior. Falta
la ejecucion guardada del notebook y su revision, no el calculo mediante scripts.


## Notebook ejecutado y comprobado

El 29/10/2026 se ejecuto el notebook completo: 6 celdas de codigo ejecutadas y 0 errores guardados. Contiene las salidas reales de I1, I2 e I3. Las referencias anteriores a ejecucion pendiente describen etapas previas. Quedan pendientes guardar el commit del analisis, la presentacion y la publicacion de la rama.
