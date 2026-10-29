// Indices y comparacion controlada de la MISMA consulta, filtro y orden.
// hint({$natural:1}) simula el recorrido sin indice sin borrarlo ni perder unicidad.
// hint(nombre) fuerza el indice candidato: no demuestra que el optimizador lo elija.
// Con solo 20/200 documentos no se promete una mejora de tiempo de ejecucion.
(async function () {
  const base = db.getSiblingDB("gestion_eventos");
  if (await base.inscripciones.countDocuments({participante: {$exists: true}}))
    throw new Error("Modelo antiguo: ejecutar la recarga autorizada antes de los indices.");
  if (!(await base.eventos.countDocuments({})) || !(await base.inscripciones.countDocuments({})))
    throw new Error("Se requieren datos cargados para comparar y probar duplicados.");

  // Igualdad en estado y ciudad, despues rango/orden por fecha (indice compuesto).
  // Costo: almacenamiento y mantenimiento de claves al cambiar estado, ciudad o fecha.
  await base.eventos.createIndex(
    {estado: 1, "sede.ciudad": 1, fecha_inicio: 1}, {name: "estado_ciudad_fecha"});
  // Integridad: un DNI no puede repetirse en un evento, incluso estando cancelado.
  // Costo: espacio, mantenimiento por escritura y comprobacion de unicidad.
  await base.inscripciones.createIndex(
    {evento_id: 1, "usuario.dni": 1}, {unique: true, name: "evento_usuario_dni_unico"});
  // Multikey: indexa cada elemento del array. Ayuda a buscar un requisito puntual.
  // Costo: varias claves por evento y mantenimiento al modificar el array.
  // No se afirma que optimice el $setIsSubset de la consulta de elegibilidad.
  await base.eventos.createIndex(
    {conocimientos_requeridos: 1}, {name: "conocimientos_requeridos_multikey"});

  function etapas(objeto, resultado = new Set()) {
    if (!objeto || typeof objeto !== "object") return resultado;
    if (objeto.stage) resultado.add(objeto.stage);
    for (const valor of Object.values(objeto)) etapas(valor, resultado);
    return resultado;
  }
  function resumen(explain) {
    return {
      etapas: [...etapas(explain.queryPlanner.winningPlan)],
      totalKeysExamined: explain.executionStats.totalKeysExamined,
      totalDocsExamined: explain.executionStats.totalDocsExamined,
      nReturned: explain.executionStats.nReturned,
      plan_ganador: explain.queryPlanner.winningPlan
    };
  }
  async function comparar(coleccion, filtro, orden, indice, motivo, costo) {
    print("\nINDICE: " + indice);
    print("Justificacion: " + motivo);
    print("Costo: " + costo);
    print("Consulta identica en ambas ejecuciones:"); printjson({filtro, orden});
    const construir = () => orden ? coleccion.find(filtro).sort(orden) : coleccion.find(filtro);
    const sin = resumen(await construir().hint({$natural: 1}).explain("executionStats"));
    const con = resumen(await construir().hint(indice).explain("executionStats"));
    print("SIN INDICE (recorrido natural forzado):"); printjson(sin);
    print("CON INDICE (indice forzado):"); printjson(con);
    if (sin.nReturned !== con.nReturned) throw new Error("La cantidad de resultados difiere.");
    if (!sin.etapas.includes("COLLSCAN") || !con.etapas.includes("IXSCAN"))
      throw new Error("No se observaron las etapas COLLSCAN/IXSCAN esperadas.");
    print("Interpretacion: se comparan documentos y claves examinados para devolver los mismos " + con.nReturned + " resultados.");
  }
  await comparar(base.eventos,
    {estado: "publicado", "sede.ciudad": "Córdoba", fecha_inicio: {$gte: ISODate("2026-11-01T00:00:00Z"), $lt: ISODate("2026-12-01T00:00:00Z")}},
    {fecha_inicio: 1}, "estado_ciudad_fecha", "filtra estado/ciudad y ordena por fecha", "una clave por evento; costo en cada escritura relevante");
  const original = await base.inscripciones.findOne({"usuario.dni": {$exists: true}});
  await comparar(base.inscripciones,
    {evento_id: original.evento_id, "usuario.dni": original.usuario.dni},
    null, "evento_usuario_dni_unico", "consulta exacta e integridad evento/DNI", "una clave por inscripcion y validacion de unicidad");
  await comparar(base.eventos, {conocimientos_requeridos: "javascript"},
    null, "conocimientos_requeridos_multikey", "busca eventos que exigen javascript", "una clave por elemento del array (multikey)");

  print("\nPRUEBA DE DNI DUPLICADO (debe ser rechazado con 11000)");
  const antes = await base.inscripciones.countDocuments({});
  const sesion = db.getMongo().startSession();
  let rechazado = false;
  try {
    await sesion.withTransaction(async () => {
      const copia = {...original, _id: ObjectId()};
      await sesion.getDatabase("gestion_eventos").inscripciones.insertOne(copia);
      // Si el indice estuviera mal, abortar sin dejar el documento de prueba.
      throw new Error("El indice no rechazo el DNI duplicado.");
    }, {writeConcern: {w: "majority"}, readPreference: "primary"});
  } catch (error) {
    const patron = error.keyPattern || error.errorResponse?.keyPattern;
    if (error.code !== 11000 || !patron || !patron["usuario.dni"] || !patron.evento_id) throw error;
    rechazado = true;
    print("Rechazado correctamente: codigo " + error.code + ", indice evento_usuario_dni_unico.");
  } finally {
    await sesion.endSession();
  }
  const despues = await base.inscripciones.countDocuments({});
  if (!rechazado || antes !== despues) throw new Error("Fallo la prueba de duplicado o cambio el total.");
  print("Inscripciones antes/despues: " + antes + "/" + despues + ". No se dejaron datos de prueba.");
})().catch(error => {print("ERROR: " + error.message); quit(1);});
