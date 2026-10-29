# 0. Contexto

## Problema

Una organizacion necesita publicar eventos con sede, cupo, precio y cronograma,
registrar inscripciones y cancelaciones, y consultar demanda, ocupacion y
recaudacion. Los registros deben conservar su historial y evitar duplicados o
cupos inconsistentes.

## Actores

- Organizador: crea borradores, publica, modifica o cancela eventos y consulta inscripciones.
- Usuario: se identifica mediante DNI y aporta nombre, email y conocimientos para inscribirse.
- Analista: consulta los datos y prepara los indicadores I1, I2 e I3.

La API implementa estas operaciones de negocio; no incluye autenticacion ni
control de permisos por actor. Los actores describen responsabilidades del dominio.

## Alcance

Base documental MongoDB gestion_eventos con colecciones eventos e inscripciones;
modelo mixto con datos embebidos y referencias; FastAPI, PyMongo y Docker Compose
con un replica set rs0 de un nodo. La demo HTTP usa Postman.

Se contemplan eventos gratuitos/pagos, invitaciones, actividades de distintos
tipos, requisitos de conocimientos, cupos y cancelacion con historial.
No se implementan cobros reales, devoluciones automaticas, notificaciones,
autenticacion ni una coleccion independiente de usuarios.

Los datos son ficticios. El poblado reproducible tiene 20 eventos y 200
inscripciones. Al finalizar las pruebas manuales del 29/10/2026 hay 22 eventos y
201 inscripciones: se conservaron un evento de demo cancelado, un borrador extra
y una inscripcion cancelada. Los nueve controles de consistencia dieron cero.

## Criterio de exito

La API debe respetar reglas de negocio y atomicidad entre inscripcion/cupo y
cancelacion/restitucion. Las consultas deben responder preguntas del dominio;
los indices deben justificarse con planes y metricas; el analisis debe definir
indicadores, denominadores y tratamiento de estados antes de graficar.
