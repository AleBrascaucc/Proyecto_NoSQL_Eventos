// RECARGA DESTRUCTIVA de eventos e inscripciones. Ejecutar solo con backup y autorizacion.
// Conserva titulos, fechas, precios, estados y campos opcionales del poblado original.
// El drop y la preparacion de colecciones/indice son EXTERNOS a la transaccion.
// Toda la insercion (20 + 200 documentos) se confirma en UNA transaccion.

function generarDatos({objectId = ObjectId, decimal = NumberDecimal} = {}) {
    const eventos = [], inscripciones = [];
    const catalogo = ["python", "javascript", "sql", "mongodb", "docker", "git", "excel", "diseño"];
    const requisitosPorCategoria = {
        "Tecnología": ["javascript", "git"], "Educación": ["excel"],
        "Cultura": ["diseño"], "Negocios": ["sql", "excel"]
    };
    const ciudades = [
      "Córdoba", "Rosario", "Mendoza", "Buenos Aires"
    ];

    const temas = [
      ["Tecnología", "Desarrollo web"],
      ["Educación", "Innovación educativa"],
      ["Cultura", "Encuentro de literatura"],
      ["Negocios", "Emprendimientos"]
    ];

    for (let i = 0; i < 20; i++) {
      const id = objectId(
        i === 0
          ? "6715a1b2c3d4e5f6a7b8c9d0"
          : "72000000000000000000" + String(i).padStart(4, "0")
      );

      // 1 inscripción del ejemplo + 144 + 55 = 200.
      // Los eventos 1 y 2 son borradores sin inscripciones.
      const cantidad = i === 0 ? 1 : i < 3 ? 0 : i < 15 ? 12 : 11;
      const pasado = i >= 15;
      const tema = temas[i % temas.length];

      const inicio = i === 0
        ? new Date("2026-11-15T12:00:00Z")
        : new Date(Date.UTC(2026, pasado ? 8 : 10, i + 1, 12));

      const mitad = new Date(inicio.getTime() + 2 * 3600000);
      const fin = new Date(inicio.getTime() + 4 * 3600000);

      const titulo = i === 0
        ? "Taller de MongoDB"
        : tema[1] + " " + i;

      const precio = i === 0
        ? 15000
        : i % 4 === 0 ? 0 : 2000 * (i % 5 + 1);

      const estado = i > 0 && i < 3
        ? "borrador"
        : pasado ? "finalizado"
        : i === 14 ? "cancelado" : "publicado";

      const capacidad = i === 0 ? 30 : i === 3 ? 12 : 20 + i * 2;

      const actividades = [
        {
          codigo_actividad: "ACT-01",
          titulo: i === 0
            ? "Introducción al modelado documental"
            : tema[1] + " práctico",
          tipo: "taller",
          orador: "Ana Pérez",
          inicio: inicio,
          fin: mitad,
          sala: "Aula 1",
          detalles_especificos: {
            requiere_notebook: true,
            software_previo: ["MongoDB Compass"],
            nivel: i % 2 === 0 ? "inicial" : "intermedio"
          }
        }
      ];

      if (i > 0) {
        actividades.push({
          codigo_actividad: "ACT-02",
          titulo: "Conferencia de cierre",
          tipo: "conferencia",
          orador: "Luis Gómez",
          inicio: mitad,
          fin: fin,
          sala: "Auditorio",
          detalles_especificos: {
            transmision_streaming: false,
            traduccion_simultanea: false
          }
        });
      }

      const evento = {
        _id: id,
        titulo: titulo,
        categoria: i === 0 ? "Tecnología" : tema[0],
        estado: estado,
        fecha_inicio: inicio,
        fecha_fin: fin,
        precio_entrada: decimal(precio.toFixed(2)),
        capacidad_total: capacidad,
        vacantes_disponibles: capacidad,
        sede: {
          nombre: i === 0
            ? "Centro de Capacitación"
            : "Centro de eventos " + i,
          direccion: i === 0
            ? "Av. Colón 100"
            : "Calle de prueba " + (100 + i),
          ciudad: ciudades[i % ciudades.length],
          capacidad_maxima: 100
        },
        conocimientos_requeridos: i === 0 ? ["mongodb", "docker"]
          : i % 5 === 0 ? [] : [...requisitosPorCategoria[tema[0]]],
        actividades: actividades
      };

      if (i % 2 === 0) {
        evento.etiquetas = i === 0
          ? ["mongodb", "bases-de-datos"]
          : ["formacion", tema[0].toLowerCase()];
      }

      eventos.push(evento);

      for (let j = 0; j < cantidad; j++) {
        const dni = i === 0
          ? "44123456"
          : String(45000000 + i * 100 + j);

        const cancelada = i !== 0 && i !== 3 && j % 5 === 0;
        const invitacion = i !== 0 && j % 7 === 0;
        const importe = invitacion ? 0 : precio;

        const fecha = new Date(
          inicio.getTime() - (35 - j) * 86400000
        );

        const requeridos = evento.conocimientos_requeridos;
        const extras = catalogo.filter(x => !requeridos.includes(x));
        const conocimientos = j % 3 === 0 ? [...requeridos]
          : [...requeridos, extras[(i + j) % extras.length]];
        const inscripcion = {
          _id: objectId("73000000000000000000" + String(i * 100 + j).padStart(4, "0")),
          evento_id: id,
          evento_resumen: {
            titulo: titulo,
            fecha_inicio: inicio
          },
          usuario: {
            conocimientos: conocimientos,
            nombre_completo: i === 0
              ? "Juan Pérez"
              : "Participante " + i + "-" + j,
            dni: dni,
            email: i === 0
              ? "juan@example.com"
              : "persona" + i + "_" + j + "@example.com"
          },
          fecha_inscripcion: fecha,
          estado_inscripcion: cancelada ? "cancelada" : "confirmada",
          tipo_entrada: invitacion ? "invitacion" : "general",
          importe_abonado: decimal(importe.toFixed(2)),
          actividades_seleccionadas: i === 0
            ? ["ACT-01"]
            : j % 3 === 0 ? []
            : j % 3 === 1 ? ["ACT-01"] : ["ACT-01", "ACT-02"]
        };

        if (importe > 0) {
          inscripcion.metodo_pago = j % 2 === 0
            ? "transferencia" : "efectivo";
        }

        if (cancelada) {
          inscripcion.fecha_cancelacion = new Date(
            fecha.getTime() + 86400000
          );
        }

        if (j % 2 === 1) {
          inscripcion.usuario.institucion = "Institución de prueba";
        }

        if (j % 4 === 1) {
          inscripcion.preferencias_alimentarias = ["Sin TACC"];
        }

        inscripciones.push(inscripcion);
      }

      const ocupadas = inscripciones.filter(x => x.evento_id.toString() === id.toString() && x.estado_inscripcion === "confirmada").length;
      if (ocupadas > capacidad) throw new Error("Capacidad insuficiente en " + titulo);
      evento.vacantes_disponibles = capacidad - ocupadas;
    }
    if (eventos.length !== 20 || inscripciones.length !== 200) throw new Error("Totales del generador incorrectos.");
    const pares = new Set();
    for (const i of inscripciones) {
        const e = eventos.find(e => e._id.toString() === i.evento_id.toString());
        const clave = i.evento_id.toString() + ":" + i.usuario.dni;
        if (pares.has(clave)) throw new Error("DNI duplicado en el generador.");
        pares.add(clave);
        if (!e || !e.conocimientos_requeridos.every(c => i.usuario.conocimientos.includes(c)))
            throw new Error("El generador no cumple los requisitos.");
        if (!i.usuario.conocimientos.every(c => catalogo.includes(c) && c === c.trim().toLowerCase()))
            throw new Error("Conocimientos fuera del catalogo o sin normalizar.");
    }
    return {eventos, inscripciones};
}

async function recargar() {
    const base = db.getSiblingDB("gestion_eventos");
    const hello = await base.adminCommand({hello: 1});
    if (!hello.setName || !hello.isWritablePrimary)
        throw new Error("Se requiere un replica set con primario disponible; no se borro nada.");
    // Generar y validar ANTES del drop. IDs y contenido son deterministas.
    const lote = generarDatos();
    print("REINICIO de eventos e inscripciones (requiere backup previo).");
    for (const nombre of ["inscripciones", "eventos"]) {
        if ((await base.getCollectionNames()).includes(nombre)) {
            const resultado = await base.runCommand({drop: nombre, writeConcern: {w: "majority"}});
            if (!resultado.ok) throw new Error("No se pudo borrar " + nombre);
        }
        const creada = await base.runCommand({create: nombre, writeConcern: {w: "majority"}});
        if (!creada.ok) throw new Error("No se pudo crear " + nombre);
    }
    // Crear ANTES de insertar; el indice antiguo desaparecio al borrar la coleccion.
    await base.inscripciones.createIndex(
        {evento_id: 1, "usuario.dni": 1},
        {unique: true, name: "evento_usuario_dni_unico", writeConcern: {w: "majority"}});
    const sesion = db.getMongo().startSession();
    try {
        await sesion.withTransaction(async () => {
            const datos = sesion.getDatabase("gestion_eventos");
            // Copias nuevas por intento: el driver puede reejecutar el callback.
            const intento = generarDatos();
            await datos.eventos.insertMany(intento.eventos, {ordered: true});
            await datos.inscripciones.insertMany(intento.inscripciones, {ordered: true});
        }, {readConcern: {level: "snapshot"}, writeConcern: {w: "majority"}, readPreference: "primary"});
    } catch (error) {
        print("Insercion abortada. El drop previo NO se revierte; recuperar del backup si corresponde.");
        throw error;
    } finally {
        await sesion.endSession();
    }
    print("Carga completada y confirmada.");
    print("Eventos: " + await base.eventos.countDocuments({}));
    print("Inscripciones: " + await base.inscripciones.countDocuments({}));
    print("Indice unico: evento_usuario_dni_unico");
    print("Ejecutar ahora 04_verificaciones.js.");
}

// Exportacion exclusiva para pruebas del generador en Node; mongosh ejecuta recargar.
if (typeof module !== "undefined" && module.exports) module.exports = {generarDatos};
if (typeof db !== "undefined") recargar().catch(error => {print("ERROR: " + error.message); quit(1);});
