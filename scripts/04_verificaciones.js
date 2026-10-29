function claveId(valor) {
  if (valor === null || valor === undefined) return "";
  if (typeof valor === "string") return valor;
  return EJSON.stringify(valor);
}
// Auditoria de consistencia. Solo lectura; todos los controles deben dar 0.
// No impone 20/200 como invariante: despues de la demo puede haber mas registros.
function auditar(eventos, inscripciones) {
  const problemas = {
    inscripciones_sin_evento: [], duplicados_evento_usuario_dni: [],
    eventos_con_cupos_inconsistentes: [], confirmadas_sin_conocimientos: [],
    actividades_seleccionadas_inexistentes: [], documentos_con_participante: [],
    conocimientos_sin_normalizar: [], usuarios_invalidos: [], borradores_con_inscripciones: []
  };
  const porId = new Map(eventos.map(e => [claveId(e._id), e]));
  const pares = new Set(), confirmadas = new Map(), inscritos = new Map();
  const normalizada = a => Array.isArray(a) && a.every(c => typeof c === "string" && c.length > 0 && c === c.trim().toLowerCase()) && new Set(a).size === a.length;
  for (const e of eventos) {
    const id = claveId(e._id);
    if (Object.hasOwn(e, "participante")) problemas.documentos_con_participante.push({coleccion: "eventos", id});
    if (!normalizada(e.conocimientos_requeridos)) problemas.conocimientos_sin_normalizar.push({coleccion: "eventos", id});
  }
  for (const i of inscripciones) {
    const id = claveId(i._id), eid = claveId(i.evento_id), e = porId.get(eid);
    if (!e) problemas.inscripciones_sin_evento.push(id);
    inscritos.set(eid, (inscritos.get(eid) || 0) + 1);
    if (i.estado_inscripcion === "confirmada") confirmadas.set(eid, (confirmadas.get(eid) || 0) + 1);
    if (Object.hasOwn(i, "participante")) problemas.documentos_con_participante.push({coleccion: "inscripciones", id});
    if (!i.usuario || typeof i.usuario.dni !== "string" || !/^[0-9]+$/.test(i.usuario.dni)
        || typeof i.usuario.nombre_completo !== "string" || !i.usuario.nombre_completo.trim()
        || typeof i.usuario.email !== "string" || !i.usuario.email.includes("@")) problemas.usuarios_invalidos.push(id);
    if (!normalizada(i.usuario?.conocimientos)) problemas.conocimientos_sin_normalizar.push({coleccion: "inscripciones", id});
    const clave = eid + ":" + i.usuario?.dni;
    if (pares.has(clave)) problemas.duplicados_evento_usuario_dni.push({evento_id: eid, dni: i.usuario?.dni, id});
    pares.add(clave);
    if (e && i.estado_inscripcion === "confirmada") {
      const requeridos = Array.isArray(e.conocimientos_requeridos) ? e.conocimientos_requeridos : [];
      const sabe = Array.isArray(i.usuario?.conocimientos) ? i.usuario.conocimientos : [];
      const faltantes = requeridos.filter(c => !sabe.includes(c));
      if (faltantes.length) problemas.confirmadas_sin_conocimientos.push({id, faltantes});
    }
    if (e) {
      const validas = new Set((Array.isArray(e.actividades) ? e.actividades : []).map(a => a.codigo_actividad));
      if (!Array.isArray(i.actividades_seleccionadas) || i.actividades_seleccionadas.some(c => !validas.has(c)))
        problemas.actividades_seleccionadas_inexistentes.push(id);
    }
  }
  for (const e of eventos) {
    const id = claveId(e._id), ocupadas = confirmadas.get(id) || 0;
    if (!Number.isInteger(e.capacidad_total) || e.capacidad_total <= 0
        || !Number.isInteger(e.vacantes_disponibles) || e.vacantes_disponibles < 0
        || e.vacantes_disponibles + ocupadas !== e.capacidad_total
        || e.capacidad_total > e.sede?.capacidad_maxima)
      problemas.eventos_con_cupos_inconsistentes.push({id, capacidad: e.capacidad_total, vacantes: e.vacantes_disponibles, confirmadas: ocupadas});
    if (e.estado === "borrador" && inscritos.get(id)) problemas.borradores_con_inscripciones.push(id);
  }
  return problemas;
}

async function verificar() {
  const base = db.getSiblingDB("gestion_eventos");
  const eventos = await base.eventos.find({}).toArray();
  const inscripciones = await base.inscripciones.find({}).toArray();
  if (!eventos.length || !inscripciones.length) throw new Error("Base vacia o incompleta: no se puede validar el poblado.");
  print("TOTALES"); print("Eventos: " + eventos.length); print("Inscripciones: " + inscripciones.length);
  const problemas = auditar(eventos, inscripciones);
  let cantidad = 0;
  for (const [control, detalles] of Object.entries(problemas)) {
    print(control + ": " + detalles.length);
    if (detalles.length) printjson(detalles.slice(0, 5));
    cantidad += detalles.length;
  }
  print("TOTAL DE PROBLEMAS: " + cantidad);
  if (cantidad) throw new Error("Hay inconsistencias; revisar los controles anteriores.");
  print("Verificacion completa: todos los controles en 0.");
}
if (typeof module !== "undefined" && module.exports) module.exports = {auditar};
if (typeof db !== "undefined") verificar().catch(error => {print("ERROR: " + error.message); quit(1);});
