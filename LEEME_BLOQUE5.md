# Bloque 5: API en Docker y demo de Postman

## Instalacion

El instalador SOLO copia archivos y respalda el Compose previo. No ejecuta Docker,
no inicia servicios, no toca .env, no escribe en MongoDB y no publica cambios en Git.
Conserva api/requirements.txt y el codigo de los bloques anteriores.

Archivos: docker-compose.yml, api/Dockerfile, api/.dockerignore,
postman/gestion_eventos.postman_collection.json y esta guia.

## Volumen y replica set existentes

Compose fija el proyecto proyecto-eventos y monta scripts/ en /scripts (solo lectura).
Usa el volumen EXTERNO proyecto-eventos_mongo_datos. No lo crea: si falta, falla.
Permite indicar otro nombre mediante MONGO_VOLUME_NAME en un .env local.
Antes de arrancar, hay que inspeccionar el contenedor original y confirmar el
nombre real del volumen montado en /data/db. No se supone que se verifico todavia.

Este Compose es para continuar con el volumen existente y su replica set rs0.
No inicializa ni reconfigura el replica set y no carga datos automaticamente.
Es valido hacer down/up SIN -v conservando dicho volumen; no hay que borrar
volumenes ni ejecutar ambas configuraciones Compose en paralelo.

La API espera a que MongoDB informe primario de rs0. Dentro de Docker usa
mongodb://mongo:27017/?replicaSet=rs0&directConnection=true, NO localhost.
La conexion directa permite usar este replica set de UN nodo aunque su miembro
anuncie otro hostname en la configuracion previa. No es una configuracion de
alta disponibilidad ni se recomienda para un replica set de varios nodos.

Puertos locales: MongoDB 127.0.0.1:27018 y API 127.0.0.1:8000.
El Dockerfile copia unicamente app/ y requirements.txt, usa Python 3.12 y ejecuta
Uvicorn como usuario sin privilegios. .dockerignore excluye .env y caches.
Compose provee las variables de conexion sin credenciales; .env local no se copia.

## Arranque pendiente

Una vez confirmado este bloque instalado, se inspeccionara el volumen original,
se detendra cualquier Uvicorn local y se levantara Compose desde la carpeta
proyecto-eventos-reorganizado. No levantarlo desde la carpeta anterior.

No se incluyen comandos de arranque automatico en el instalador: todavia no
se construyo la imagen ni se comprobo la API contra el Docker del usuario.

## Demo de Postman (pendiente de ejecutar)

Importar postman/gestion_eventos.postman_collection.json en Postman Desktop.
Usar la variable de coleccion base_url = http://localhost:8000.
No crear variables de entorno con los mismos nombres: prevalecerian sobre las
variables que guarda la coleccion y podrian hacer que se usen IDs anteriores.

Ejecutar las 24 peticiones EN ORDEN; pueden enviarse una por una o con Runner
usando una iteracion y la secuencia completa. Los scripts guardan IDs y generan
fechas a 30 dias del momento de ejecucion; no dependen del poblado de noviembre.

El evento de prueba tiene capacidad 1, entrada gratis y requiere mongodb/docker:
- Se crea borrador y se publica.
- Un usuario con solo mongodb recibe 409 indicando docker.
- La siguiente consulta comprueba que la vacante sigue en 1 (rollback).
- El usuario que sabe ambos obtiene 201; la vacante baja a 0.
- Un DNI diferente en el evento completo obtiene 409.
- Cancelar la inscripcion restituye cupo; repetir la cancelacion mantiene 1.
- El DNI original, incluso cancelado, sigue reservado para ese evento y obtiene
  409 por duplicado, comprobado DESPUES de restituir cupo para aislar la regla.
- Se cancela el evento conservando historial.
- Se prueban IDs inexistente/mal formado y rango de precios invalido.
- Se crea otro borrador, se elimina con 204 y se comprueba 404.

Las peticiones cubren todos los endpoints solicitados mas /estado y el listado
de inscripciones. Los tests HTTP y de contenido aparecen en Test Results.
Se conservan un evento cancelado y una inscripcion cancelada por recorrido
completo: si se parte de 20/200, al terminar quedan 21/201. No altera el poblado
original ni lo reinicia. Repetir la secuencia agrega otro historial de demo.
No ejecutar otras escrituras en paralelo al comparar los cupos.

## Validacion realizada

Se valido la estructura YAML, el puerto y volumen declarados, el montaje scripts/,
la conexion interna por mongo, las 24 peticiones y la sintaxis JavaScript de sus
scripts. Los cuerpos de ejemplo de evento e inscripcion se validaron con los
modelos Pydantic de la API. No hay .env ni credenciales en el paquete.

No se construyo la imagen Docker en este entorno (Docker no esta disponible),
ni se ejecuto Postman contra la API real. Las comprobaciones de atomicidad y
el resultado de Test Results siguen pendientes en la computadora del usuario.

## Referencias

https://docs.docker.com/reference/compose-file/volumes/
https://docs.docker.com/compose/how-tos/startup-order/
https://learning.postman.com/docs/tests-and-scripts/write-scripts/postman-sandbox-reference/pm-variables/
