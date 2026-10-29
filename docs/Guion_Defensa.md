# Guion de defensa y demostracion

Exposicion sugerida: 10 a 12 minutos y demo de 3 a 5 minutos. La presentacion
contiene 15 diapositivas con notas del orador. Ajustar el tiempo a la consigna oral
del profesor. Cada integrante debe poder explicar modelo, consulta, indice y repositorio.

## Recorrido oral

1. Problema: administrar eventos con cronogramas heterogeneos, inscripciones y cupos.
2. Modelo: sede/actividades embebidas por lectura conjunta; inscripciones separadas
   por crecimiento y actualizacion independiente. evento_id referencia el evento.
3. Identidad: DNI es el identificador del usuario; _id identifica la inscripcion.
   usuario es embebido y no existe una coleccion de usuarios.
4. Consistencia: reserva con filtro atomico, validacion e insercion dentro de una
   transaccion. Un error aborta tambien el descuento de cupo. Cancelacion idempotente.
5. Consultas e indices: doce preguntas del dominio, tres comparaciones con hint.
   Explicar que menos documentos examinados no demuestra por si solo menor tiempo.
6. Indicadores: I1 cuenta selecciones, I2 porcentajes de reservas, I3 importes brutos.
   No confundir seleccion con asistencia ni bruto con ganancia.
7. Limites: poblado ficticio; sin prueba de concurrencia/recuperacion; replica de un
   nodo sin redundancia; sin pagos reales ni autenticacion.

## Preparacion de demo

Desde proyecto-eventos-reorganizado:

```powershell
docker compose -p proyecto-eventos up -d
docker compose -p proyecto-eventos ps
Invoke-RestMethod 'http://localhost:8000/estado'
```

Abrir Postman y la coleccion importada. base_url=http://localhost:8000.
No ejecutar recarga ni borrar volumenes para preparar la defensa.
Abrir tambien el informe PDF, notebook ejecutado y los dos PNG reales por si
no hay conexion a internet. La API local necesita Docker; los archivos se leen offline.

## Demo corta en Postman

Enviar peticiones en orden porque guardan IDs automaticamente. Usar evento nuevo:
- 01: estado inicial. Anotar totales actuales, sin exigir siempre 22/201.
- 02, 03 y 04: crear borrador, consultar y publicar.
- 05 y 06: consulta filtrada y una vacante disponible.
- 07: conocimientos insuficientes; 409 e indica docker.
- 08: misma vacante en 1; evidencia de rollback del descuento.
- 09 y 10: inscripcion valida 201; cupo baja a 0.
- 11: otro DNI en evento lleno recibe 409.
- 12, 13 y 14: consultar, cancelar y repetir cancelacion.
- 15: vacante en 1, nunca 2.
- 16 y 17: mismo DNI rechazado aun con cupo; vacante se mantiene.
- 18: cancelar evento conservando historial.
- 19 y 20: 404 inexistente y 422 formato invalido (ambos esperados).
- 21: 422 rango invalido.
- 22, 23 y 24: crear otro borrador, eliminar con 204 y comprobar 404.

Para una demo muy corta, explicar el resto con las evidencias ya guardadas; no
alterar el orden de las peticiones necesarias para obtener los IDs. Cada recorrido
completo agrega un evento y una inscripcion cancelados; cambia los totales de
historial aunque no los importes. No pulsar dos veces una peticion de creacion.

## Cierre de consistencia

```powershell
docker compose -p proyecto-eventos exec -T mongo mongosh --quiet --file /scripts/04_verificaciones.js
```

Los nueve controles deben ser cero. Los totales pueden crecer con nuevas demos.
Si Docker o la API falla, mostrar archivos reales del anexo y explicar que son
la evidencia previa; no presentar una captura como ejecucion en vivo.

## Preguntas probables

- Por que no embebieron todas las inscripciones: crecen y se modifican individualmente.
- Por que el DNI es string: preserva ceros y no es una cantidad para calcular.
- Que pasa si cambia el titulo del evento: la referencia permite consultar lo actual;
  evento_resumen conserva las condiciones historicas de la inscripcion.
- Por que un duplicado devuelve409: es conflicto de negocio; la estructura puede ser valida.
- Es transaccional la recarga completa: solo la insercion; el drop previo no se revierte.
- Como se evita sobreventa: filtro por vacantes positivas y $inc, junto a transaccion.
- Cancelar dos veces: no incrementa cupo nuevamente.
- El indice multikey optimiza setIsSubset: no se demostro; se midio igualdad puntual.
- Por que I1 tiene152 confirmadas e I2 usa143: I2 excluye9 del evento cancelado original.
- 20,97% versus25,12%: global ponderado frente a promedio simple de eventos.
- Septiembre0 implica ninguna inscripcion: no; hay una de importe cero.
- 789000 es ganancia: no; bruto registrado sin descontar canceladas/devoluciones/costos.

## Material entregable

Informe Word editable y PDF, presentacion PPTX, notebook con salidas, scripts,
repositorios/API, Compose, coleccion Postman y evidencias. Los nombres de los
integrantes no se inventaron: agregarlos a portada y diapositiva inicial si el
docente exige identificacion del grupo.
