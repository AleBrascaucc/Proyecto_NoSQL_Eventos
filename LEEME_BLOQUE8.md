# Bloque 8: I2, ocupacion por evento

Instala analisis/i2_ocupacion.py y sus pruebas; actualiza notebook, README y docs
de indicadores, conservando I1. Respalda archivos anteriores y no reemplaza los
resultados exportados de I1. No ejecuta Docker, MongoDB, el notebook ni Git commit.

## Ejecucion en la PC

Dejar Docker funcionando. Desde proyecto-eventos-reorganizado, usar el entorno
de analisis creado para I1; no hace falta instalar nuevas dependencias:

```powershell
.\.venv\Scripts\python.exe .\analisis\i2_ocupacion.py
```

Compartir la tabla y el bloque CORTE de la salida para verificar los datos reales.
Exporta tabla CSV, interpretacion Markdown y corte JSON en una carpeta nueva
analisis/resultados/I2_<fecha_UTC>/. No modifica la base ni sobrescribe I1.

En Jupyter tambien puede ejecutarse la celda I2 luego de preparar la conexion:

```powershell
.\.venv\Scripts\python.exe -m jupyterlab .\analisis\analisis.ipynb
```

El notebook no tiene salidas precargadas; la evidencia real previa de I1 esta en
su carpeta de resultados y no se vuelve a generar al instalar este bloque.

## Definicion

Para cada evento publicado/finalizado:

    ocupacion (%) = 100 * confirmadas / capacidad_total

Se excluyen borradores/cancelados; las inscripciones canceladas tampoco cuentan.
La ocupacion cero se conserva. Se validan cupos y capacidad antes de calcular.
En los finalizados es un registro de reservas finales, no asistencia comprobada.

El resumen distingue:
- Global ponderado por capacidad = 100 * suma(confirmadas) / suma(capacidades).
- Promedio simple = media de porcentajes individuales sin ponderar por capacidad.

Los calculos usan Decimal y redondeo half-even a dos decimales (como MongoDB $round).
La tabla ordena de mayor a menor porcentaje mostrado, con desempate por titulo/ID.
El resumen se calcula antes de redondear cada fila.

## Referencia local, pendiente de confirmar en MongoDB

En el poblado generado: 17 eventos elegibles, 682 lugares, 143 confirmadas,
539 vacantes; ocupacion global 20,97% y promedio simple 25,12%.
Emprendimientos 3 esta al 100% (12/12). Las 9 confirmadas del evento cancelado
original no entran en I2, aunque si aportan a I1.

Con la base actual de 22 eventos, se esperan 5 excluidos si no cambiaron sus
estados: los 3 originales (2 borradores, 1 cancelado) y los 2 eventos de demo
(1 borrador, 1 cancelado). El codigo no fija esos resultados: los consulta.

La fecha guardada es la hora UTC de ejecucion, no el timestamp interno del snapshot.
Los conteos y la agregacion comparten una transaccion de solo lectura con snapshot.
I1 e I2 tienen cortes independientes; comprobar que no hubo cambios entre ambos
antes de compararlos. No se eliminan datos ni se recarga para igualar resultados.

## Validacion local

16 pruebas aprobadas: formula, orden, capacidad/cupos, cero confirmadas, duplicados,
exclusion de estados, ausencia de eventos, redondeo, media simple frente a global,
exportacion sin sobrescribir y sesion consistente de lectura. No se ejecuto el
script contra la base del usuario desde este entorno.

Pruebas opcionales (requieren pytest de tests/requirements-dev.txt):

```powershell
.\.venv\Scripts\python.exe -m pytest .\tests\test_i2_ocupacion.py -q -p no:cacheprovider
```

I2 no agrega un grafico: se mantiene el plan de dos figuras, barras I1 y lineas I3.
Despues de verificar I2, el siguiente bloque sera I3 y requerira confirmacion.
