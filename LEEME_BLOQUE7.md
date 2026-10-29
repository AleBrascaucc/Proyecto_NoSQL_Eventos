# Bloque 7: I1, demanda por actividad

El instalador reemplaza el notebook inicial y actualiza README/docs de indicadores.
Agrega i1_demanda.py y sus pruebas. Guarda una copia de los archivos reemplazados.
No instala dependencias ni ejecuta Docker, MongoDB, notebook, analisis o Git commit.
No incluye resultados precargados ni las imagenes generadas para pruebas locales.

## Preparar herramientas y ejecutar (PC del usuario)

Con Docker funcionando, desde proyecto-eventos-reorganizado:

```powershell
& "$HOME\proyecto-eventos\.venv\Scripts\python.exe" -m venv .venv
if ($LASTEXITCODE -ne 0) { throw "No se pudo crear el entorno de analisis." }
.\.venv\Scripts\python.exe -m pip install -r .\analisis\requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Fallo la instalacion de dependencias." }
.\.venv\Scripts\python.exe .\analisis\i1_demanda.py
```

El primer comando usa el Python que ya existe en la carpeta original para crear
un entorno separado en el proyecto reorganizado. No modifica el entorno anterior.
No instalar paquetes dentro del contenedor de la API ni recargar datos.

La ejecucion de I1 lee la base y escribe solo en analisis/resultados/I1_<fecha>/.
Se imprime tabla, corte y carpeta de salida. Revisar y compartir la salida y el
PNG para verificar los resultados reales. No se asume que se ejecutaron por el
solo hecho de instalar este bloque.

## Alternativa en Jupyter

```powershell
.\.venv\Scripts\python.exe -m jupyterlab .\analisis\analisis.ipynb
```

Ejecutar las celdas de conexion y la seccion I1. La celda I1 obtiene su propio
corte consistente, muestra tabla, grafico e interpretacion y exporta la evidencia.
I2 e I3 permanecen pendientes. Cada ejecucion completa crea una carpeta nueva;
no se sobrescriben resultados anteriores.

## Resultados esperables, sujetos a comprobacion real

El analisis toma la base ACTUAL (ultimo estado informado: 22 eventos y 201
inscripciones). Cuenta solo confirmadas, por evento y codigo de actividad.
La demo tiene una inscripcion cancelada: no aporta a I1; tampoco los borradores.
Los eventos cancelados del poblado con inscripciones confirmadas SI aportan
su demanda historica, porque I1 no filtra estado del evento.

El generador de prueba dio 152 confirmadas: 52 sin actividades y 100 que eligieron
alguna. Esas 100 aportan 147 selecciones en 35 pares evento/actividad. El maximo
fue Emprendimientos 3 / ACT-01, con 8. Son referencias del poblado y de las consultas
anteriores; el script no fija estos valores ni inventa salidas si la base cambia.

Una inscripcion puede seleccionar mas de una actividad. Demanda no es asistencia
real, cantidad de personas unicas ni ocupacion; esas unidades no se intercambian.
El CSV conserva los nombres completos de actividades y el estado del evento;
el grafico usa titulo del evento y codigo para que las 35 barras se lean.

## Validacion local

12 pruebas aprobadas: agrupacion por par, orden, errores de referencias/conteos,
resultado vacio, exportacion sin sobrescribir, interpretacion y propagacion de
sesion snapshot. Se reviso visualmente el grafico con el poblado generado local.
No se conecto a MongoDB del usuario desde este entorno.

Para repetir pruebas, instalar las dependencias de desarrollo ya existentes:

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\tests\requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest .\tests\test_i1_demanda.py -q -p no:cacheprovider
```

## Siguiente paso

Verificar el resultado real de I1 y despues avanzar a I2, con confirmacion del
nuevo bloque. Este instalador no cambia la API, los scripts de carga ni la base.
