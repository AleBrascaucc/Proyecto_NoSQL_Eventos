// Comprobaciones iniciales de consistencia para gestion_eventos.
// Ejecutar desde PowerShell: docker compose exec mongo mongosh --quiet --file /scripts/verificaciones.js
const base = db.getSiblingDB("gestion_eventos");

print("Eventos: " + base.eventos.countDocuments({}));
print("Inscripciones: " + base.inscripciones.countDocuments({}));

const inscripcionesHuerfanas = base.inscripciones.aggregate([
  { $lookup: { from: "eventos", localField: "evento_id", foreignField: "_id", as: "evento" } },
  { $match: { evento: { $size: 0 } } },
  { $count: "cantidad" }
]).toArray();
print("Inscripciones sin evento: " + (inscripcionesHuerfanas[0]?.cantidad ?? 0));

const duplicados = base.inscripciones.aggregate([
  { $group: {
    _id: { evento_id: "$evento_id", dni: "$participante.dni" },
    cantidad: { $sum: 1 }
  } },
  { $match: { cantidad: { $gt: 1 } } }
]).toArray();
print("Combinaciones evento+DNI duplicadas: " + duplicados.length);
if (duplicados.length) printjson(duplicados);

const cuposInconsistentes = base.eventos.aggregate([
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
    as: "conteo"
  } },
  { $addFields: {
    confirmadas: { $ifNull: [ { $arrayElemAt: ["$conteo.cantidad", 0] }, 0 ] }
  } },
  { $match: { $expr: { $or: [
    { $lt: ["$vacantes_disponibles", 0] },
    { $gt: ["$vacantes_disponibles", "$capacidad_total"] },
    { $ne: [ { $add: ["$vacantes_disponibles", "$confirmadas"] }, "$capacidad_total" ] }
  ] } } },
  { $project: { titulo: 1, capacidad_total: 1, vacantes_disponibles: 1, confirmadas: 1 } }
]).toArray();
print("Eventos con cupos inconsistentes: " + cuposInconsistentes.length);
if (cuposInconsistentes.length) printjson(cuposInconsistentes);

print("\nÍndices de eventos:");
printjson(base.eventos.getIndexes());
print("Índices de inscripciones:");
printjson(base.inscripciones.getIndexes());
