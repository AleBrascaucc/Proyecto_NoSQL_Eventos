# Gestion de eventos e inscripciones con MongoDB

Proyecto integrador de Base de Datos Aplicada: modelo documental mixto, API
FastAPI con transacciones, consultas, indices y preparacion de indicadores.

## Orden de lectura de la entrega

| Seccion | Archivo |
|---|---|
| 0. Contexto | [docs/0_contexto.md](docs/0_contexto.md) |
| 1. Diseno justificado | [docs/1_diseno.md](docs/1_diseno.md) |
| 2. Consultas con enunciados | [docs/2_consultas.md](docs/2_consultas.md), scripts/03_consultas.js |
| 3. API y demo | [docs/3_api.md](docs/3_api.md), postman/ |
| 4. Indices y planes | [docs/4_indices.md](docs/4_indices.md) |
| 5. Indicadores | [docs/5_indicadores.md](docs/5_indicadores.md), analisis/analisis.ipynb |
| Evidencias | [docs/anexo/README.md](docs/anexo/README.md) |

Resultados actuales: recarga inicial 20 eventos/200 inscripciones; 12 consultas
ejecutadas; tres indices comparados y DNI duplicado rechazado; API construida y
levantada en Docker; demo de Postman ejecutada manualmente. El estado posterior
es 22 eventos/201 inscripciones y nueve controles de consistencia en cero.

I1, I2 e I3 se ejecutaron mediante scripts contra la base real y se revisaron
los dos graficos. I1: 35 pares y 147 selecciones. I2: ocupacion global 20,97%
(143/682). I3: bruto registrado 789000, incluyendo canceladas. Ver
[docs/6_resultados.md](docs/6_resultados.md) para cortes, limites y evidencias.

El notebook esta guardado con seis celdas de codigo ejecutadas y cero errores.
El analisis esta en el commit local b881392, posterior a la implementacion 3cb55a7.

## Material para entregar y exponer

- [Informe tecnico editable](informe/Informe_Tecnico_Eventos.docx).
- [Informe tecnico PDF](informe/Informe_Tecnico_Eventos.pdf).
- [Presentacion profesional](presentacion/Presentacion_Eventos.pptx): 15 diapositivas
  con notas, tablas y graficos editables.
- [Guion de defensa y demo](docs/Guion_Defensa.md).
- [Resultados y conclusiones](docs/6_resultados.md).
- [Indice de evidencias](docs/anexo/README.md) y capturas de los casos 404 y 422.

Los documentos corresponden al trabajo ejecutado el 29/10/2026. La publicacion
remota se comprueba por separado mediante el estado de GitHub; este archivo no
se usa como comprobante de un push que todavia no se haya realizado.

## Requisitos

- Docker Desktop iniciado con contenedores Linux y Docker Compose.
- Git. La rama de trabajo es cambio-modelo-y-estructura; main no se modifica.
- Postman Desktop para la demo.
- Python 3.12 recomendado para notebook o ejecucion local; no hace falta Python
  anfitrion para usar la API en Docker. Node es opcional para pruebas de scripts.

## Estructura

- docker-compose.yml: mongo y api, con healthchecks y volumen persistente externo.
- api/app/: main.py, db.py, routes/, schemas/, services/ y repositories/.
- scripts/: 01_carga_datos.js, 02_indices.js, 03_consultas.js, 04_verificaciones.js.
- docs/: contexto, diseno, consultas, API, indices, indicadores y anexo.
- postman/: coleccion de pruebas y, si se convirtio en Postman, archivos YAML locales.
- analisis/: notebook y dependencias de analisis.
- tests/: pruebas locales de API y scripts.
- presentacion/: reservada para el futuro .pptx.

## Continuar con el volumen ya existente

Ejecutar desde la RAIZ DEL PROYECTO REORGANIZADO, no desde la carpeta anterior.
El nombre del proyecto Docker es proyecto-eventos. El volumen verificado es
proyecto-eventos_mongo_datos y se monta en /data/db. Compose lo declara externo:
no lo crea y falla si no existe. Si otra computadora usa otro volumen, configurar
MONGO_VOLUME_NAME en un .env local. No subir .env ni credenciales.

```powershell
docker compose -p proyecto-eventos config --quiet
docker compose -p proyecto-eventos up -d --build
docker compose -p proyecto-eventos ps
Invoke-RestMethod "http://localhost:8000/estado"
```

Comprobar el volumen sin plantillas de comillas de Docker:

```powershell
$contenedor = docker inspect proyecto-eventos-mongo-1 | ConvertFrom-Json
$contenedor.Mounts | Where-Object { $_.Destination -eq '/data/db' } |
    Select-Object Type, Name, Destination
```

La API usa mongo:27017 dentro de la red Docker. Desde la PC, Compass y el notebook
usan mongodb://localhost:27018/?replicaSet=rs0&directConnection=true.
La conexion directa corresponde a este replica set de UN nodo y no implica alta
disponibilidad. No reconfigurar el replica set existente.

Para recrear contenedores conservando datos:

```powershell
docker compose -p proyecto-eventos down
docker compose -p proyecto-eventos up -d --build
```

No agregar -v ni borrar volumenes. No levantar a la vez el Compose viejo y el
nuevo. Si hay Uvicorn local usando 8000, detenerlo antes de levantar el servicio.

## Solo en una computadora nueva SIN volumen ni datos

Esta seccion NO corresponde al entorno ya verificado. Primero se debe aprovisionar
un volumen vacio e inicializar rs0. Estos pasos de provisionamiento no se probaron
en la PC del usuario: alli ya existia el volumen y el replica set.

```powershell
docker volume create proyecto-eventos_mongo_datos
docker compose -p proyecto-eventos up -d mongo
docker compose -p proyecto-eventos exec mongo mongosh
```

Dentro de mongosh (no en PowerShell), ejecutar una sola vez en el volumen nuevo:

```javascript
rs.initiate({_id: "rs0", members: [{_id: 0, host: "mongo:27017"}]})
```

Salir de mongosh con exit. Esperar al primario y consultar docker compose ps.
Luego cargar datos y levantar la API. No repetir rs.initiate en una replica ya
inicializada ni usar la recarga para recuperar datos reales.

## Backup antes de cualquier recarga

La recarga reemplaza eventos e inscripciones. Detener escrituras de la API y
hacer backup con nombre NUEVO para no sobrescribir respaldos previos:

```powershell
New-Item -ItemType Directory -Force .\backups | Out-Null
$nombreBackup = 'backup_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.archive'
docker compose -p proyecto-eventos exec -T mongo mongodump --archive=/tmp/respaldo.archive
# Continuar solo si el comando anterior termino con codigo 0.
docker compose -p proyecto-eventos cp mongo:/tmp/respaldo.archive ".\backups\$nombreBackup"
Get-Item ".\backups\$nombreBackup" | Select-Object Name, Length
```

Comprobar copia externa no vacia antes de continuar. El respaldo original previo
al cambio de modelo quedo en proyecto-eventos/backups/backup_antes_cambio.archive,
112073 bytes; su existencia/tamano fueron comprobados, no una restauracion.
backups/ esta excluida de Git. No incluir backups, .env o datos privados en entregas.

## Carga y scripts (recarga destructiva SOLO con autorizacion)

No ejecutar 01 simplemente para consultar datos: reinicia las dos colecciones.
El drop y la creacion de colecciones/indice son externos a la transaccion;
la insercion de los 220 documentos es transaccional. Un aborto de insercion no
restaura el contenido anterior al drop.

Con la API detenida y el backup comprobado, el orden de ejecucion es:

```powershell
docker compose -p proyecto-eventos stop api
docker compose -p proyecto-eventos exec -T mongo mongosh --quiet --file /scripts/01_carga_datos.js
# Si hay un error, detenerse; no ejecutar los siguientes scripts automaticamente.
docker compose -p proyecto-eventos exec -T mongo mongosh --quiet --file /scripts/04_verificaciones.js
docker compose -p proyecto-eventos exec -T mongo mongosh --quiet --file /scripts/03_consultas.js
docker compose -p proyecto-eventos exec -T mongo mongosh --quiet --file /scripts/02_indices.js
docker compose -p proyecto-eventos up -d api
```

Salida inicial esperada: 20/200 y nueve controles en cero. El indice unico del
nuevo modelo se crea ANTES de insertar. Los IDs y el contenido del poblado son
reproducibles. 02 crea indices adicionales y prueba un duplicado rechazado;
03 y 04 son de solo lectura. La consulta de proximos eventos depende del dia.

Para guardar evidencia y decodificar correctamente tildes en Windows PowerShell:

```powershell
$utf8 = New-Object System.Text.UTF8Encoding($false)
[Console]::OutputEncoding = $utf8
$OutputEncoding = $utf8
New-Item -ItemType Directory -Force .\docs\anexo | Out-Null
docker compose -p proyecto-eventos exec -T mongo mongosh --quiet --file /scripts/04_verificaciones.js 2>&1 |
    Tee-Object -FilePath .\docs\anexo\verificaciones_actuales.txt
```

## API

- http://localhost:8000/estado : conexion y totales.
- http://localhost:8000/docs : documentacion interactiva Swagger UI.
- docker compose -p proyecto-eventos logs --tail 50 api : diagnostico.

Para ejecutarla fuera de Docker, instalar api/requirements.txt en un entorno
virtual y copiar .env.example a .env en la raiz, ajustando MONGO_URI y MONGO_DB.
Luego, desde la raiz, con ese entorno activado:

```powershell
python -m uvicorn app.main:app --app-dir .\api --reload
```

No ejecutar esta alternativa en paralelo con la API de Docker en el mismo puerto.

## Postman

Importar postman/gestion_eventos.postman_collection.json como COLECCION, no solo
abrirlo como archivo de texto. base_url = http://localhost:8000 es variable de
coleccion. No crear variables de entorno con los mismos nombres de IDs.

En Postman local v12 puede requerirse convertir JSON a YAML v3. Si despues solo
se ve YAML en el editor, usar Import para incorporar la coleccion a Collections.
La copia JSON original tambien esta en el ZIP de instalacion del bloque 5.
Conservar la coleccion JSON o su version YAML junto al proyecto para la entrega.

Enviar 01 a 24 EN ORDEN, una vez cada una; 02 y 22 crean eventos y no deben repetirse
por error. 404, 409 y 422 son correctos en los casos intencionales. La secuencia
comprueba conocimientos faltantes y cupo sin cambios, inscripcion valida, cupo
agotado, cancelacion repetida, duplicado, IDs y eliminacion de borrador.

Un recorrido desde 20/200 normalmente termina en 21/201. La ejecucion observada
termino en 22/201 por un borrador adicional identificado; no fue eliminado y los
nueve controles posteriores dieron cero. No confundir este estado con la carga inicial.

## Pruebas locales y analisis

Con Python del proyecto y dependencias de API instaladas:

```powershell
python -m pip install -r .\tests\requirements-dev.txt
$env:PYTHONPATH = (Join-Path (Get-Location) 'api')
python -m pytest .\tests\test_api_bloque3.py -q -p no:cacheprovider
Remove-Item Env:\PYTHONPATH
```

Con Node instalado, opcional:

```powershell
node --test .\tests\scripts_bloque4.test.cjs
```

Las pruebas locales usan dobles para transacciones; no sustituyen pruebas de
concurrencia o fallos del servidor. Las comprobaciones reales realizadas y sus
limites estan documentados en docs/3_api.md y docs/anexo/README.md.

El notebook contiene I1, I2 e I3 con sus salidas ejecutadas y guardadas.
Ver LEEME_BLOQUE7.md para ejecutar I1. Preparar un entorno separado para analisis:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\analisis\requirements.txt
.\.venv\Scripts\python.exe -m jupyterlab .\analisis\analisis.ipynb
```

No es necesario ejecutar estos comandos para instalar la documentacion. Las
celdas son de solo lectura en MongoDB; los tres indicadores exportan archivos
locales. Ver LEEME_BLOQUE9.md para I3. Tambien puede ejecutarse I1 sin Jupyter con
`.\.venv\Scripts\python.exe .\analisis\i1_demanda.py`.

## Estado de Git

Los cambios locales pertenecen a cambio-modelo-y-estructura. La integracion de GitHub de la sesion no tuvo permisos de escritura (403).
La publicacion se realiza desde la cuenta Git del propietario de la copia local;
el script publicar_rama.ps1 verifica que el SHA remoto coincida con el local. Antes de compartir, revisar git diff y git status,
comprobar exclusiones de .env/backups y agregar solo fuentes/evidencias revisadas.
