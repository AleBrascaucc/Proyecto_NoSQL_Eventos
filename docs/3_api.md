# 3. API y demo en Postman

## Arquitectura

main.py construye la aplicacion; routes/http.py maneja HTTP y serializacion;
schemas/modelos.py valida entradas; services aplica reglas y orquesta transacciones;
repositories es el unico lugar que consulta o escribe colecciones. db.py gestiona
conexion y sesiones. Uvicorn sirve FastAPI; /docs es Swagger UI generado por FastAPI.

Dockerfile usa Python 3.12, instala api/requirements.txt y ejecuta Uvicorn sin
privilegios. Compose conecta la API a mongo:27017 y espera un primario saludable.
El volumen externo existente conserva los datos al recrear contenedores.

## Endpoints

| Metodo | Ruta | Exito |
|---|---|---:|
| GET | /estado | 200 |
| GET | /eventos | 200 |
| GET | /eventos/{id} | 200 |
| POST | /eventos | 201 |
| PATCH | /eventos/{id} | 200 |
| DELETE | /eventos/{id} | 204, sin cuerpo |
| PATCH | /eventos/{id}/cancelacion | 200 |
| POST | /eventos/{id}/inscripciones | 201 |
| GET | /eventos/{id}/inscripciones | 200 |
| PATCH | /inscripciones/{id}/cancelacion | 200 |

GET /eventos admite categoria, ciudad, estado, fecha_desde, fecha_hasta,
precio_minimo, precio_maximo, conocimiento, etiqueta, con_vacantes y limite.
conocimiento busca eventos que EXIGEN ese conocimiento puntual; no comprueba por
si solo si una persona cumple TODOS los requisitos.

Errores: 404 inexistente; 409 conflicto de negocio; 422 entrada o ID invalido;
503 fallo de acceso a base o indice del nuevo modelo ausente. Las fechas se
reciben con zona horaria. La API calcula importe y cupos; no confia esos valores
al cliente.

## Pruebas manuales del 29/10/2026

La coleccion postman/gestion_eventos.postman_collection.json tiene 24 peticiones
ordenadas. Guarda IDs y construye fechas futuras. La ejecucion fue realizada
manualmente por el usuario, quien informo coincidencia con los resultados esperados.
Se observaron capturas de 404 y 422; esos errores eran casos intencionales.
No se dispone de una exportacion consolidada de los resultados de tests de Postman.

Casos principales: 409 por conocimientos faltantes con cupo conservado; 201 por
inscripcion valida y descuento; 409 por cupo agotado; cancelacion y repeticion sin
sumar dos veces; 409 por DNI duplicado con cupo disponible; borrado de borrador,
404 posterior y 422 por rango invalido. La verificacion final en MongoDB dio cero
en los nueve controles, con 22 eventos y 201 inscripciones.

La demo conservo un evento cancelado y su inscripcion cancelada, mas un borrador
extra. No se identifica la causa exacta del borrador extra con la evidencia actual;
se documento en lugar de borrarlo. No hay inscripciones asociadas a borradores.

Esto valida el comportamiento secuencial observado. No se realizaron pruebas de
carga concurrente, caida de servidor ni eleccion de un nuevo primario. El replica
set de un nodo habilita transacciones pero no aporta redundancia.

## Preparar la defensa

Mostrar /estado, una consulta filtrada, el 409 por conocimientos faltantes y las
consultas de cupo antes/despues; contrastar con la inscripcion valida. Mostrar
la evidencia de indices y los nueve controles finales. Un 404/409/422 esperado
es un resultado correcto, aunque Postman lo coloree en rojo.
