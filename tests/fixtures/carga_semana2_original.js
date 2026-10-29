(async function () {
// Datos ficticios para la semana 2.
// Conserva el ejemplo anterior y no duplica registros al repetir la carga.

const base = db.getSiblingDB("gestion_eventos");

await base.inscripciones.createIndex(
  { evento_id: 1, "participante.dni": 1 },
  { unique: true, name: "evento_participante_unico" }
);

if (!(await base.getCollectionNames()).includes("eventos")) {
  await base.createCollection("eventos");
}

const sesion = db.getMongo().startSession();

try {
  await sesion.withTransaction(async () => {
    const datos = sesion.getDatabase("gestion_eventos");

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
      const id = ObjectId(
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
        precio_entrada: NumberDecimal(precio.toFixed(2)),
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
        actividades: actividades
      };

      if (i % 2 === 0) {
        evento.etiquetas = i === 0
          ? ["mongodb", "bases-de-datos"]
          : ["formacion", tema[0].toLowerCase()];
      }

      const existente = await datos.eventos.findOne({ _id: id });

      if (existente && existente.titulo !== titulo) {
        throw new Error("El identificador pertenece a otro evento: " + id);
      }

      // Solo inserta si el evento todavía no existe.
      await datos.eventos.updateOne(
        { _id: id },
        { $setOnInsert: evento },
        { upsert: true }
      );

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

        const inscripcion = {
          evento_id: id,
          evento_resumen: {
            titulo: titulo,
            fecha_inicio: inicio
          },
          participante: {
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
          importe_abonado: NumberDecimal(importe.toFixed(2)),
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
          inscripcion.participante.institucion = "Institución de prueba";
        }

        if (j % 4 === 1) {
          inscripcion.preferencias_alimentarias = ["Sin TACC"];
        }

        // Conserva la inscripción si ya existe.
        await datos.inscripciones.updateOne(
          { evento_id: id, "participante.dni": dni },
          { $setOnInsert: inscripcion },
          { upsert: true }
        );
      }

      // Calcula las vacantes usando las inscripciones reales.
      const actual = await datos.eventos.findOne({ _id: id });

      const ocupadas = await datos.inscripciones.countDocuments({
        evento_id: id,
        estado_inscripcion: "confirmada"
      });

      if (ocupadas > actual.capacidad_total) {
        throw new Error("Capacidad insuficiente en: " + titulo);
      }

      await datos.eventos.updateOne(
        { _id: id },
        {
          $set: {
            vacantes_disponibles: actual.capacidad_total - ocupadas
          }
        }
      );
    }
  });

  print("Carga completada.");
  print("Eventos: " + await base.eventos.countDocuments({}));
  print("Inscripciones: " + await base.inscripciones.countDocuments({}));

} catch (error) {
  print("No se completó la carga: " + error.message);
  throw error;
} finally {
  await sesion.endSession();
}
})().catch(function (error) {
  print("ERROR: " + error.message);
  quit(1);
});

