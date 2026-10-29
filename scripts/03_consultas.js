// Consultas del dominio: solo lectura. Los resultados esperados corresponden a la recarga inicial.
// Los indices y explain se ejecutan exclusivamente en 02_indices.js.
(async function () {
const base = db.getSiblingDB("gestion_eventos");
function consulta(numero, enunciado, requisito, esperado) {
  print("\nCONSULTA " + numero);
  print("Enunciado: " + enunciado);
  print("Requisito: " + requisito);
  print("Resultado esperado: " + esperado);
}

// Enunciado: ¿Que eventos cuestan entre 4000 y 8000 inclusive?
// Requisito: Filtros de comparacion ($gte, $lte), proyeccion y orden.
// Esperado: 9 eventos en el poblado inicial.
consulta(1, '¿Que eventos cuestan entre 4000 y 8000 inclusive?', 'Filtros de comparacion ($gte, $lte), proyeccion y orden.', '9 eventos en el poblado inicial.');
await base.eventos.find(
  { precio_entrada: { $gte: NumberDecimal("4000.00"), $lte: NumberDecimal("8000.00") } },
  { titulo: 1, categoria: 1, precio_entrada: 1, _id: 0 }
).sort({ precio_entrada: 1 }).forEach(doc => printjson(doc));

// Enunciado: ¿Que eventos comienzan durante noviembre de 2026?
// Requisito: Rango de fechas ISODate, proyeccion y sort.
// Esperado: 15 eventos, incluyendo borradores y cancelado.
consulta(2, '¿Que eventos comienzan durante noviembre de 2026?', 'Rango de fechas ISODate, proyeccion y sort.', '15 eventos, incluyendo borradores y cancelado.');
await base.eventos.find(
  { fecha_inicio: { $gte: ISODate("2026-11-01T00:00:00Z"), $lt: ISODate("2026-12-01T00:00:00Z") } },
  { titulo: 1, fecha_inicio: 1, _id: 0 }
).sort({ fecha_inicio: 1 }).forEach(doc => printjson(doc));

// Enunciado: ¿Que publicados tienen vacantes y son gratuitos o de Tecnologia?
// Requisito: Combinacion de condiciones AND implicito y $or.
// Esperado: 4 eventos publicados con lugares disponibles.
consulta(3, '¿Que publicados tienen vacantes y son gratuitos o de Tecnologia?', 'Combinacion de condiciones AND implicito y $or.', '4 eventos publicados con lugares disponibles.');
await base.eventos.find({
  estado: "publicado",
  vacantes_disponibles: { $gt: 0 },
  $or: [
    { precio_entrada: NumberDecimal("0.00") },
    { categoria: "Tecnología" }
  ]
}, { titulo: 1, categoria: 1, precio_entrada: 1, vacantes_disponibles: 1, _id: 0 })
.sort({ fecha_inicio: 1 }).forEach(doc => printjson(doc));

// Enunciado: ¿Que eventos se realizan en Cordoba?
// Requisito: Consulta de documento embebido por notacion de punto.
// Esperado: 5 eventos con sede.ciudad Cordoba.
consulta(4, '¿Que eventos se realizan en Cordoba?', 'Consulta de documento embebido por notacion de punto.', '5 eventos con sede.ciudad Cordoba.');
await base.eventos.find(
  { "sede.ciudad": "Córdoba" },
  { titulo: 1, "sede.ciudad": 1, fecha_inicio: 1, _id: 0 }
).sort({ fecha_inicio: 1 }).forEach(doc => printjson(doc));

// Enunciado: ¿Que eventos incluyen un taller intermedio?
// Requisito: Consulta sobre array de subdocumentos con $elemMatch.
// Esperado: 10 eventos; ambas condiciones deben cumplirse en la misma actividad.
consulta(5, '¿Que eventos incluyen un taller intermedio?', 'Consulta sobre array de subdocumentos con $elemMatch.', '10 eventos; ambas condiciones deben cumplirse en la misma actividad.');
await base.eventos.find({ actividades: { $elemMatch: {
  tipo: "taller",
  "detalles_especificos.nivel": "intermedio"
} } }, { titulo: 1, actividades: 1, _id: 0 }).forEach(doc => printjson(doc));

// Enunciado: ¿Cuales son los proximos cinco eventos publicados?
// Requisito: Fecha actual, sort y limit.
// Esperado: Hasta 5 eventos futuros; depende del dia de ejecucion. Al 29/10/2026 devuelve 5.
consulta(6, '¿Cuales son los proximos cinco eventos publicados?', 'Fecha actual, sort y limit.', 'Hasta 5 eventos futuros; depende del dia de ejecucion. Al 29/10/2026 devuelve 5.');
await base.eventos.find(
  { estado: "publicado", fecha_inicio: { $gte: new Date() } },
  { titulo: 1, fecha_inicio: 1, categoria: 1, _id: 0 }
).sort({ fecha_inicio: 1 }).limit(5).forEach(doc => printjson(doc));

// Enunciado: ¿Cuantas inscripciones confirmadas seleccionaron cada actividad de cada evento?
// Requisito: Pipeline con $match, $unwind, $group y $sort (I1).
// Esperado: 35 pares evento/actividad en el poblado inicial; no contar canceladas ni arrays vacios.
consulta(7, '¿Cuantas inscripciones confirmadas seleccionaron cada actividad de cada evento?', 'Pipeline con $match, $unwind, $group y $sort (I1).', '35 pares evento/actividad en el poblado inicial; no contar canceladas ni arrays vacios.');
await base.inscripciones.aggregate([
  { $match: { estado_inscripcion: "confirmada" } },
  { $unwind: "$actividades_seleccionadas" },
  { $group: { _id: { evento_id: "$evento_id", actividad: "$actividades_seleccionadas" }, veces_seleccionada: { $sum: 1 } } },
  { $sort: { veces_seleccionada: -1, "_id.evento_id": 1, "_id.actividad": 1 } }
]).forEach(doc => printjson(doc));

// Enunciado: ¿Cual es la recaudacion bruta registrada por mes de inscripcion?
// Requisito: Pipeline con fechas ($dateTrunc), $sum y $group (I3).
// Esperado: 3 meses: agosto, septiembre y octubre de 2026. Incluye canceladas; no es ingreso neto ni descuenta devoluciones.
consulta(8, '¿Cual es la recaudacion bruta registrada por mes de inscripcion?', 'Pipeline con fechas ($dateTrunc), $sum y $group (I3).', '3 meses: agosto, septiembre y octubre de 2026. Incluye canceladas; no es ingreso neto ni descuenta devoluciones.');
await base.inscripciones.aggregate([
  { $group: {
    _id: { $dateTrunc: { date: "$fecha_inscripcion", unit: "month" } },
    total_recaudado: { $sum: "$importe_abonado" },
    cantidad_inscripciones: { $sum: 1 }
  } },
  { $sort: { _id: 1 } }
]).forEach(doc => printjson(doc));

// Enunciado: ¿Cual es el precio promedio, minimo y maximo por categoria?
// Requisito: Agregacion con $avg, $min, $max y $sum.
// Esperado: 4 categorias; 5 eventos por categoria.
consulta(9, '¿Cual es el precio promedio, minimo y maximo por categoria?', 'Agregacion con $avg, $min, $max y $sum.', '4 categorias; 5 eventos por categoria.');
await base.eventos.aggregate([
  { $group: {
    _id: "$categoria",
    precio_promedio: { $avg: "$precio_entrada" },
    precio_minimo: { $min: "$precio_entrada" },
    precio_maximo: { $max: "$precio_entrada" },
    cantidad_eventos: { $sum: 1 }
  } },
  { $sort: { _id: 1 } }
]).forEach(doc => printjson(doc));

// Enunciado: ¿Cuantas confirmadas tiene cada evento y que porcentaje de su capacidad ocupan?
// Requisito: Relacion entre colecciones ($lookup), conteo y porcentaje (base de I2).
// Esperado: 20 eventos; Emprendimientos 3 tiene ocupacion del 100%. Incluye todos los estados para control; I2 excluira borradores y cancelados.
consulta(10, '¿Cuantas confirmadas tiene cada evento y que porcentaje de su capacidad ocupan?', 'Relacion entre colecciones ($lookup), conteo y porcentaje (base de I2).', '20 eventos; Emprendimientos 3 tiene ocupacion del 100%. Incluye todos los estados para control; I2 excluira borradores y cancelados.');
await base.eventos.aggregate([
  { $lookup: {
    from: "inscripciones",
    let: { idEvento: "$_id" },
    pipeline: [
      { $match: { $expr: { $and: [
        { $eq: ["$evento_id", "$$idEvento"] },
        { $eq: ["$estado_inscripcion", "confirmada"] }
      ] } } },
      { $count: "cantidad" }
    ],
    as: "conteo_confirmadas"
  } },
  { $addFields: {
    inscripciones_confirmadas: { $ifNull: [ { $arrayElemAt: ["$conteo_confirmadas.cantidad", 0] }, 0 ] },
  } },
  { $addFields: {
    porcentaje_ocupacion: { $round: [
      { $multiply: [ { $divide: ["$inscripciones_confirmadas", "$capacidad_total"] }, 100 ] },
      2
    ] }
  } },
  { $project: {
    titulo: 1,
    estado: 1,
    capacidad_total: 1,
    vacantes_disponibles: 1,
    inscripciones_confirmadas: 1,
    porcentaje_ocupacion: 1
  } },
  { $sort: { inscripciones_confirmadas: -1, titulo: 1 } }
]).forEach(doc => printjson(doc));


// Enunciado: ¿A que publicados puede inscribirse alguien que sabe javascript y git, segun sus conocimientos?
// Requisito: comparacion de conjuntos con $expr y $setIsSubset.
// Esperado: 5 eventos; se incluyen eventos sin requisitos (conjunto vacio).
consulta(11, "¿Que publicados cumplen los conocimientos de alguien que sabe javascript y git?",
  "$expr + $setIsSubset; sin requisitos tambien cumple", "5 eventos; no asegura cupo, fecha futura ni ausencia de DNI duplicado.");
await base.eventos.find({estado: "publicado", $expr: {
  $setIsSubset: ["$conocimientos_requeridos", {$literal: ["javascript", "git"]}]
}}, {_id: 0, titulo: 1, conocimientos_requeridos: 1, vacantes_disponibles: 1})
  .sort({fecha_inicio: 1, _id: 1}).forEach(doc => printjson(doc));

// Enunciado: ¿Que conocimientos aparecen mas entre las inscripciones confirmadas?
// Requisito: pipeline $match + $unwind + $group + $sort.
// Esperado: 8 conocimientos; excel encabeza con 72 inscripciones confirmadas.
// Se cuentan inscripciones, no personas unicas entre distintos eventos.
consulta(12, "¿Que conocimientos son mas comunes entre las inscripciones confirmadas?",
  "$unwind + $group sobre usuario.conocimientos", "8 conocimientos; excel: 72. Cada inscripcion puede aportar a varios conocimientos.");
await base.inscripciones.aggregate([
  {$match: {estado_inscripcion: "confirmada"}},
  {$unwind: "$usuario.conocimientos"},
  {$group: {_id: "$usuario.conocimientos", inscripciones_confirmadas: {$sum: 1}}},
  {$sort: {inscripciones_confirmadas: -1, _id: 1}}
]).forEach(doc => printjson(doc));
})().catch(error => {print("ERROR: " + error.message); quit(1);});
