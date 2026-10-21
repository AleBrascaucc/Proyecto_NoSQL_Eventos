# Gestión de eventos e inscripciones — MongoDB

Este repositorio permite que cada integrante levante una instancia local de MongoDB con Docker Compose y reconstruya el conjunto de prueba. La base local no viaja por Git: `carga_datos.js` la vuelve a crear de forma repetible (20 eventos y 200 inscripciones). Cada integrante tendrá su propio volumen y sus propios cambios.

## Requisitos

- Docker Desktop iniciado y configurado con contenedores Linux.
- Git para clonar el repositorio.

## Inicio desde cero en Windows PowerShell

```powershell
git clone https://github.com/USUARIO/REPOSITORIO.git
cd REPOSITORIO
docker compose up -d
docker compose exec mongo mongosh --quiet --eval "rs.initiate({_id:'rs0',members:[{_id:0,host:'mongo:27017'}]})"
```

El comando `rs.initiate` se ejecuta una sola vez para un volumen nuevo. Si la réplica ya está inicializada, no lo repitas. Comprobá que haya primario:

```powershell
docker compose exec mongo mongosh --quiet --eval "print(db.hello().isWritablePrimary)"
```

Cargá los datos de prueba:

```powershell
docker compose exec mongo mongosh --quiet --file /scripts/carga_datos.js
```

La salida esperada es `Carga completada`, `Eventos: 20` e `Inscripciones: 200`. El script es idempotente: se puede volver a ejecutar sin duplicar esos registros.

## Consultas y verificaciones

Ejecutá las diez consultas de la entrega parcial 1:

```powershell
docker compose exec mongo mongosh --quiet --file /scripts/consultas_semana2.js
```

Ejecutá las comprobaciones de referencias, duplicados, vacantes e índices:

```powershell
docker compose exec mongo mongosh --quiet --file /scripts/verificaciones.js
```

Para conectarte desde Compass en la PC anfitriona, usá:

```text
mongodb://localhost:27018/?replicaSet=rs0&directConnection=true
```

## Guardar evidencia de una sesión

Para guardar comandos y salidas que ejecutes desde PowerShell, iniciá una transcripción antes de probar y detenela al terminar:

```powershell
New-Item -ItemType Directory -Force .\evidencias | Out-Null
Start-Transcript -Path .\evidencias\sesion_semana2.txt -Append
# Ejecutar aquí los comandos de Compose, consultas y verificaciones
Stop-Transcript
```

`mongosh` también conserva un historial local de comandos. En una consola interactiva podés verlo con `history()` (o `history().slice(-50)` para los últimos 50). Para exportar el historial del contenedor a un archivo local, cerrá primero las sesiones interactivas de `mongosh` y usá:

```powershell
New-Item -ItemType Directory -Force .\evidencias | Out-Null
docker compose exec mongo mongosh --quiet --eval 'print(history().join("\n"))' | Set-Content -Encoding utf8 .\evidencias\historial_mongosh.txt
```

Revisá el historial antes de compartirlo: es una bitácora local y puede contener comandos de pruebas o datos que no querés incluir. Para reproducir el trabajo, los archivos `carga_datos.js`, `consultas_semana2.js` y `verificaciones.js` son la fuente ordenada; el historial no los reemplaza.

## Datos que no se deben subir

No subas archivos de volumen, carpetas `data/`, `.env`, copias `*.bak` ni datos personales reales. El volumen `mongo_datos` queda en cada computadora y se conserva aunque se detenga el contenedor. Para empezar realmente desde cero, primero respaldá lo que necesites: `docker compose down -v` borra el volumen y todos sus datos.

Las transcripciones e historiales quedan ignorados por Git hasta que los revises. Si querés adjuntar una evidencia ya depurada, agregala explícitamente después de revisarla; evitá subir el historial bruto completo.
