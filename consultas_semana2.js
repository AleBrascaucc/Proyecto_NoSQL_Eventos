// Consultas de la semana 2 para gestion_eventos.
// Ejecutar desde PowerShell: docker compose exec mongo mongosh --quiet --file /scripts/consultas_semana2.js
const base = db.getSiblingDB("gestion_eventos");

function encabezado(n, texto) {
  print("\n===== CONSULTA " + n + " — " + texto + " =====");
}

encabezado(1, "Eventos dentro de un intervalo de precios");
base.eventos.find(
  { precio_entrada: { $gte: NumberDecimal("4000.00"), $lte: NumberDecimal("8000.00") } },
  { titulo: 1, categoria: 1, precio_entrada: 1, _id: 0 }
).sort({ precio_entrada: 1 }).forEach(printjson);

encabezado(2, "Eventos que comienzan durante noviembre de 2026");
base.eventos.find(
  { fecha_inicio: { $gte: ISODate("2026-11-01T00:00:00Z"), $lt: ISODate("2026-12-01T00:00:00Z") } },
  { titulo: 1, fecha_inicio: 1, _id: 0 }
).sort({ fecha_inicio: 1 }).forEach(printjson);

encabezado(3, "Publicados con vacantes y gratuitos o de Tecnología");
base.eventos.find({
  estado: "publicado",
  vacantes_disponibles: { $gt: 0 },
  $or: [
    { precio_entrada: NumberDecimal("0.00") },
    { categoria: "Tecnología" }
  ]
}, { titulo: 1, categoria: 1, precio_entrada: 1, vacantes_disponibles: 1, _id: 0 })
.sort({ fecha_inicio: 1 }).forEach(printjson);

encabezado(4, "Eventos de Córdoba");
base.eventos.find(
  { "sede.ciudad": "Córdoba" },
  { titulo: 1, "sede.ciudad": 1, fecha_inicio: 1, _id: 0 }
).sort({ fecha_inicio: 1 }).forEach(printjson);

encabezado(5, "Eventos con taller de nivel intermedio");
base.eventos.find({ actividades: { $elemMatch: {
  tipo: "taller",
  "detalles_especificos.nivel": "intermedio"
} } }, { titulo: 1, actividades: 1, _id: 0 }).forEach(printjson);

encabezado(6, "Próximos cinco eventos publicados");
base.eventos.find(
  { estado: "publicado", fecha_inicio: { $gte: new Date() } },
  { titulo: 1, fecha_inicio: 1, categoria: 1, _id: 0 }
).sort({ fecha_inicio: 1 }).limit(5).forEach(printjson);

encabezado(7, "Inscripciones confirmadas agrupadas por actividad");
base.inscripciones.aggregate([
  { $match: { estado_inscripcion: "confirmada" } },
  { $unwind: "$actividades_seleccionadas" },
  { $group: { _id: "$actividades_seleccionadas", veces_seleccionada: { $sum: 1 } } },
  { $sort: { veces_seleccionada: -1 } }
]).forEach(printjson);

encabezado(8, "Recaudación registrada por mes de inscripción");
base.inscripciones.aggregate([
  { $group: {
    _id: { $dateTrunc: { date: "$fecha_inscripcion", unit: "month" } },
    total_recaudado: { $sum: "$importe_abonado" },
    cantidad_inscripciones: { $sum: 1 }
  } },
  { $sort: { _id: 1 } }
]).forEach(printjson);

encabezado(9, "Promedio, mínimo y máximo de precio por categoría");
base.eventos.aggregate([
  { $group: {
    _id: "$categoria",
    precio_promedio: { $avg: "$precio_entrada" },
    precio_minimo: { $min: "$precio_entrada" },
    precio_maximo: { $max: "$precio_entrada" },
    cantidad_eventos: { $sum: 1 }
  } },
  { $sort: { _id: 1 } }
]).forEach(printjson);

encabezado(10, "Inscripciones confirmadas y ocupación por evento");
base.eventos.aggregate([
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
]).forEach(printjson);

encabezado("ÍNDICE", "Índice candidato para estado, ciudad y fecha");
print("Índice encontrado/creado: " + base.eventos.createIndex(
  { estado: 1, "sede.ciudad": 1, fecha_inicio: 1 },
  { name: "estado_ciudad_fecha" }
));
const plan = base.eventos.find(
  { estado: "publicado", "sede.ciudad": "Córdoba" }
).sort({ fecha_inicio: 1 }).hint("estado_ciudad_fecha").explain("executionStats");
printjson({
  indice: plan.queryPlanner.winningPlan,
  documentos_revisados: plan.executionStats.totalDocsExamined,
  claves_revisadas: plan.executionStats.totalKeysExamined
});
