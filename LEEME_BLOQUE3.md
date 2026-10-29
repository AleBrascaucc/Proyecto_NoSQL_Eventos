# Bloque 3: API con usuario, conocimientos y transacciones

Este paquete modifica codigo. El instalador no inicia la API, no ejecuta Docker,
no conecta a MongoDB y no crea indices ni recarga datos.

## Aplicacion en Windows

1. Extraer el ZIP completo (no ejecutar desde el visor de ZIP).
2. Ejecutar aplicar_bloque3.ps1. Por defecto aplica en
   C:\Users\<usuario>\proyecto-eventos-reorganizado.
3. Enviar la salida de Git para revisar antes de avanzar al siguiente bloque.

El instalador comprueba la rama, los archivos esperados del bloque 2 y la
integridad del paquete. Se detiene si encuentra cambios distintos de la base
esperada. Guarda una copia de los archivos reemplazados en backups/bloque3_...
antes de copiarlos. No copia .env ni toca la carpeta original del proyecto.
No crea commits ni publica cambios.

## Cambios de la API

- app/main.py solo construye FastAPI e incluye el router.
- app/routes/http.py recibe solicitudes, valida IDs, serializa BSON y traduce errores.
- app/db.py configura la conexion desde el .env de la raiz del proyecto y gestiona
  sesiones. No consulta colecciones.
- app/schemas/modelos.py conserva las validaciones anteriores de fechas, capacidad,
  actividades, entradas y filtros. Reemplaza participante por usuario; el usuario
  contiene dni, nombre_completo, email, institucion opcional y conocimientos.
  Se elimina telefono del esquema para ajustarse al nuevo modelo solicitado.
- Los conocimientos se pasan a minuscula y se recortan. Se rechazan valores
  vacios o no textuales y se eliminan repetidos conservando su orden.
- conocimientos_requeridos se admite al crear y actualizar eventos. Por defecto
  es []; conocimiento en GET /eventos busca eventos que exijan ese conocimiento
  concreto. No significa que ese unico conocimiento alcance para inscribirse.
- Solo repositories/ consulta o modifica colecciones. services/ orquesta las reglas.

## Inscripcion

1. Comprobar (solo lectura) que exista el indice unico completo
   evento_usuario_dni_unico sobre evento_id y usuario.dni.
2. Iniciar transaccion con snapshot, majority y lectura del primario.
3. Descontar una vacante mediante find_one_and_update filtrando publicado,
   fecha futura y vacantes > 0; recuperar el documento actualizado.
4. Con la MISMA sesion validar duplicados, actividades, todos los conocimientos
   requeridos y pago; insertar la inscripcion con el importe calculado por servidor.
5. Confirmar. Cualquier excepcion aborta la transaccion; no se necesita una
   compensacion manual para recuperar el cupo.

Los conocimientos faltantes devuelven 409 con detail.mensaje y
 detail.conocimientos_faltantes. DuplicateKeyError se captura fuera de la
transaccion, despues del aborto. El indice asegura unicidad incluso con solicitudes
concurrentes; el prechequeo de DNI mejora el mensaje pero no reemplaza el indice.

## Cancelacion y edicion

Cancelar una inscripcion marca su estado y restituye cupo en una transaccion.
Repetirla devuelve 200 con la misma inscripcion cancelada sin sumar vacantes.
Si falla la restitucion, tambien se revierte el cambio de estado.

Crear, editar, borrar y cancelar eventos tambien usan transacciones. La edicion
de requisitos comprueba que todas las inscripciones confirmadas los cumplan;
se rechazan cambios que invalidarian inscripciones existentes. La escritura del
evento comparte el documento que modifica la reserva: los conflictos de escritura
se delegan al manejo de transacciones del driver. No hay efectos externos en el
callback que puedan duplicarse al reintentarlo.

Cancelar un evento conserva sus inscripciones como historial, igual que antes.
No cancela automaticamente las inscripciones ni registra devoluciones de dinero.

## Estado actual y siguientes pasos

La base de Windows todavia usa participante. Este paquete NO realiza la migracion.
La API bloqueara las inscripciones y sus cancelaciones con 503 mientras no este
el indice del nuevo modelo. No iniciar las pruebas de escritura en la base actual.

Falta preparar/aplicar la recarga de 20 eventos y 200 inscripciones, los scripts
con usuario, los indices, Compose con API, Postman y la documentacion final.
El archivo .env.example es una plantilla sin secretos; no reemplaza un .env local.
El arranque futuro (una vez preparada la base), desde la raiz, sera:

```powershell
& "$HOME\proyecto-eventos\.venv\Scripts\python.exe" -m uvicorn app.main:app --app-dir .\api --reload
```

## Verificacion realizada

35 pruebas automatizadas aprobadas: normalizacion y validacion de entradas,
reglas de inscripcion, errores HTTP 404/409/422, creacion 201, cancelacion repetida,
propagacion de sesion y opciones de transaccion, filtro de conocimiento y limites
entre rutas y repositorios. Detalle en tests/test_api_bloque3.py.

Las pruebas de rollback usan un doble transaccional en memoria. Comprueban que
la API deja propagar los fallos a la transaccion; NO prueban la atomicidad de
MongoDB, las elecciones del replica set ni carreras concurrentes reales.
No se ejecutaron pruebas contra el Docker del usuario ni mediante Postman.

Entorno usado: FastAPI 0.162.0, Pydantic 2.14.2 y PyMongo 4.19.0.
requirements.txt del usuario no se reemplaza (declara Pydantic 2.14.1).

Para repetir las pruebas sin MongoDB, desde la raiz del proyecto:

```powershell
& "$HOME\proyecto-eventos\.venv\Scripts\python.exe" -m pip install -r .\tests\requirements-dev.txt
$env:PYTHONPATH = (Join-Path (Get-Location) 'api')
& "$HOME\proyecto-eventos\.venv\Scripts\python.exe" -m pytest .\tests\test_api_bloque3.py -q -p no:cacheprovider
Remove-Item Env:\PYTHONPATH
```

## Referencia tecnica

- https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/transactions/
- https://pymongo.readthedocs.io/en/4.19.0/api/pymongo/client_session.html
