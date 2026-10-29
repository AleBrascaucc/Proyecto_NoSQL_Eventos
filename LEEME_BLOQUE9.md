# Bloque 9: I3, recaudacion bruta por mes

Instala analisis/i3_recaudacion.py y sus pruebas; actualiza el notebook, README
y docs de indicadores. Conserva I1/I2 y no reemplaza sus archivos de resultados.
El instalador respalda codigo anterior. No ejecuta analisis, Docker, MongoDB,
notebook, instalacion de dependencias ni Git commit.

## Ejecucion real pendiente

Dejar Docker funcionando y, desde la raiz del proyecto reorganizado, ejecutar:

```powershell
.\.venv\Scripts\python.exe .\analisis\i3_recaudacion.py
```

No requiere nuevas dependencias: utiliza el entorno de analisis de I1/I2.
Compartir tabla y CORTE para comprobar la ejecucion. Solo lee MongoDB y escribe
localmente en analisis/resultados/I3_<fecha_UTC>/:

- i3_recaudacion.csv: meses, bruto, conteos y componente de inscripciones canceladas.
- corte.json: fecha, base, totales y reglas del indicador.
- i3_interpretacion.md: interpretacion calculada desde el resultado real.
- i3_recaudacion.png e i3_recaudacion.svg: dos formatos de la MISMA figura de lineas.

Puede ejecutarse tambien la seccion I3 del notebook, despues de las celdas de
conexion. Las celdas no tienen salidas precargadas ni se ejecutan al instalar.

## Definicion e interpretacion

Suma importe_abonado por mes UTC de fecha_inscripcion, con todos los estados.
Se incluyen canceladas: el componente monetario de estas es informativo y NO se
resta. No hay registro de devoluciones, comisiones, impuestos o costos, por lo
que no se informa ganancia ni ingreso neto. No se convierte moneda.

Los importes se mantienen en Decimal128/Decimal durante los calculos y solo se
convierten a float para dibujar. El script rechaza datos invalidos para evitar
que $sum ignore importes de tipo incorrecto y se presente un total parcial.

Los meses intermedios sin registros se rellenan con cero y se marcan en la tabla.
Un mes con registros gratuitos puede tener importe cero y no se confunde con un
mes ausente. La linea une totales mensuales observados; no es una prediccion.

## Referencias locales (no salida de MongoDB)

El generador inicial produce agosto 234000; septiembre 0; octubre 555000.
Total bruto: 789000. La base actual conserva una inscripcion gratuita y cancelada
de demo; si nada cambio se esperan 55/1/145 registros por mes (201 en total) y
49 canceladas, con el mismo bruto y 144000 registrados en canceladas.

Los resultados reales quedan pendientes hasta ejecutar I3. Cada indicador toma
su propia instantanea snapshot y documenta su corte; comparar solo si no hubo
cambios entre ejecuciones. El codigo no recarga ni filtra por titulos de demo.

## Validacion local

17 pruebas aprobadas: orden mensual, cero con registros frente a mes ausente,
precision decimal, datos invalidos, duplicados, resultado vacio, exportacion sin
sobrescribir, pipeline sin escrituras y sesion de lectura consistente. Grafico
revisado visualmente con el poblado local de prueba, no con una nueva lectura real.

Pruebas opcionales, con pytest ya instalado como dependencia de desarrollo:

```powershell
.\.venv\Scripts\python.exe -m pytest .\tests\test_i3_recaudacion.py -q -p no:cacheprovider
```

Despues de comprobar I3 y el PNG real, falta cerrar resultados/documentacion,
revisar/guardar los cambios de analisis en Git y preparar la presentacion.
