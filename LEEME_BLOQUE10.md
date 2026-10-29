# Bloque 10: cierre del analisis y ejecucion del notebook

Instala docs/6_resultados.md y actualiza README, docs/5_indicadores.md y notebook.
Respalda archivos reemplazados. No modifica scripts de indicadores ni sus resultados.
El instalador NO ejecuta notebook, Docker, MongoDB, instalacion de paquetes ni commit.

## Ejecutar y guardar el notebook en la PC

Con Docker iniciado y sin otras escrituras, desde proyecto-eventos-reorganizado:

```powershell
.\.venv\Scripts\python.exe -m ipykernel install --user --name gestion-eventos-analisis --display-name "Python - Gestion de eventos"
if ($LASTEXITCODE -ne 0) { throw "No se pudo registrar el kernel." }
.\.venv\Scripts\python.exe -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=180 --ExecutePreprocessor.kernel_name=gestion-eventos-analisis .\analisis\analisis.ipynb
if ($LASTEXITCODE -ne 0) { throw "Fallo la ejecucion del notebook. Compartir el error." }
```

El kernel registrado usa el Python del entorno de analisis, no el de la API.
La ejecucion solo lee MongoDB, agrega salidas al notebook y exporta nuevas carpetas
I1/I2/I3. No sobrescribe las ejecuciones anteriores ni recarga la base.

El instalador ya guardo copia del notebook anterior en backups/. Cerrar el notebook
en Jupyter antes de ejecutar nbconvert para evitar que la interfaz sobrescriba
las salidas desde una copia abierta anterior. Si ya tiene salidas al instalar,
el instalador se detendra por cambio de contenido: no forzarlo sin revisar.

Despues comprobar la presencia de salidas de las celdas y ausencia de errores.
Comparar los nuevos cortes con 22/201 y los resultados de referencia. Los conteos
pueden coincidir sin asegurar identidad de datos: no ejecutar otras escrituras.

## Guardado en Git, paso posterior

Revisar la lista de archivos nuevos/modificados y el tamano del notebook ejecutado.
No incluir .venv, .env, backups ni configuracion local de Postman. Las imagenes,
CSV, Markdown y JSON de analisis/resultados/ si son evidencias del analisis.
No se crea un commit automaticamente; el usuario ya autorizo el bloque de cierre,
y se daran comandos concretos tras revisar la ejecucion y lo preparado en Git.

La documentacion reporta resultados reales de scripts, no salidas fabricadas del
notebook. La presentacion y la publicacion de la rama siguen pendientes.
