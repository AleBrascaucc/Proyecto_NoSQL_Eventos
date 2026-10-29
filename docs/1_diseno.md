# 1. Diseno documental justificado

## Colecciones y relaciones

| Coleccion | Unidad de documento | Embebidos | Referencias |
|---|---|---|---|
| eventos | Un evento | sede y actividades[] con detalles por tipo | Ninguna obligatoria |
| inscripciones | Una inscripcion de un usuario a un evento | usuario y evento_resumen | evento_id apunta a eventos._id |

La sede y el cronograma se consultan junto al evento y tienen tamano acotado:
embebidos permiten recuperar su detalle sin joins. Las inscripciones se separan
porque su cantidad puede crecer y necesitan consulta y modificacion independientes.
No se coloca un array creciente de personas dentro de cada evento.

usuario contiene los datos aportados para esa inscripcion. No es una referencia
a una coleccion de usuarios ni existe id_usuario. El DNI, como string para no
perder ceros iniciales, identifica al usuario en el dominio. _id identifica la
INSCRIPCION. El par (evento_id, usuario.dni) tiene unicidad global en la coleccion,
incluyendo inscripciones canceladas: cancelar no permite reinscribir el mismo DNI
en el mismo evento con la regla actual.

Un mismo DNI puede figurar en distintos eventos. Sus datos son copias embebidas;
no existe sincronizacion automatica de perfiles entre inscripciones. evento_resumen
es una copia historica del titulo y fecha al inscribirse; evento_id permite consultar
la version actual del evento. Editar un evento no reescribe las copias historicas.

## Ejemplos en Extended JSON

Ejemplos ilustrativos del modelo, no nuevas inserciones ni exportaciones de la base:

```json
{
  "_id": {"$oid": "6715a1b2c3d4e5f6a7b8c9d0"},
  "titulo": "Taller de MongoDB",
  "categoria": "Tecnología",
  "estado": "publicado",
  "fecha_inicio": {"$date": "2026-11-15T12:00:00Z"},
  "fecha_fin": {"$date": "2026-11-15T16:00:00Z"},
  "precio_entrada": {"$numberDecimal": "15000.00"},
  "capacidad_total": 30,
  "vacantes_disponibles": 29,
  "conocimientos_requeridos": ["mongodb", "docker"],
  "sede": {
    "nombre": "Centro de Capacitación",
    "direccion": "Av. Colón 100",
    "ciudad": "Córdoba",
    "capacidad_maxima": 100
  },
  "actividades": [{
    "codigo_actividad": "ACT-01",
    "titulo": "Introducción al modelado documental",
    "tipo": "taller",
    "orador": "Ana Pérez",
    "inicio": {"$date": "2026-11-15T12:00:00Z"},
    "fin": {"$date": "2026-11-15T14:00:00Z"},
    "sala": "Aula 1",
    "detalles_especificos": {
      "requiere_notebook": true,
      "software_previo": ["MongoDB Compass"],
      "nivel": "inicial"
    }
  }],
  "etiquetas": ["mongodb", "bases-de-datos"]
}
```

```json
{
  "_id": {"$oid": "730000000000000000000000"},
  "evento_id": {"$oid": "6715a1b2c3d4e5f6a7b8c9d0"},
  "evento_resumen": {
    "titulo": "Taller de MongoDB",
    "fecha_inicio": {"$date": "2026-11-15T12:00:00Z"}
  },
  "usuario": {
    "dni": "44123456",
    "nombre_completo": "Juan Pérez",
    "email": "juan@example.com",
    "conocimientos": ["mongodb", "docker"]
  },
  "fecha_inscripcion": {"$date": "2026-10-11T12:00:00Z"},
  "estado_inscripcion": "confirmada",
  "tipo_entrada": "general",
  "importe_abonado": {"$numberDecimal": "15000.00"},
  "metodo_pago": "transferencia",
  "actividades_seleccionadas": ["ACT-01"]
}
```

## Diccionario: eventos

| Campo | Tipo BSON / estructura | Regla |
|---|---|---|
| _id | ObjectId | Identificador del evento |
| titulo, categoria | String | Textos no vacios |
| estado | String | borrador, publicado, finalizado o cancelado; API crea borrador |
| fecha_inicio, fecha_fin | Date | Fin posterior al inicio; entradas API con zona horaria |
| precio_entrada | Decimal128 | No negativo; entrada API con hasta dos decimales |
| capacidad_total | Entero | Positivo y no superior a sede.capacidad_maxima |
| vacantes_disponibles | Entero | capacidad_total menos confirmadas; no negativo |
| conocimientos_requeridos | Array de strings | Siempre presente; puede estar vacio; minusculas y sin espacios al borde |
| sede | Documento | nombre, direccion, ciudad y capacidad_maxima; servicios_disponibles opcional en poblado |
| actividades | Array de documentos | Codigos unicos dentro del evento y horarios dentro de sus limites |
| actividades[].tipo | String | taller, conferencia o panel; detalles_especificos depende del tipo |
| etiquetas | Array de strings | Opcional en documentos de carga |
| requisitos_generales | String | Opcional; texto descriptivo, diferente del array de conocimientos |

## Diccionario: inscripciones

| Campo | Tipo BSON / estructura | Regla |
|---|---|---|
| _id | ObjectId | Identifica la inscripcion |
| evento_id | ObjectId | Referencia a un evento existente |
| evento_resumen | Documento | titulo y fecha_inicio como copia historica |
| usuario | Documento | Reemplaza al campo anterior participante |
| usuario.dni | String | Digitos; identificador del usuario; unicidad por evento |
| usuario.nombre_completo | String | No vacio |
| usuario.email | String | Validado como email en la API |
| usuario.institucion | String | Opcional |
| usuario.conocimientos | Array de strings | Minusculas, recortados y sin duplicados; puede estar vacio |
| fecha_inscripcion | Date | La genera la API al confirmar |
| estado_inscripcion | String | confirmada o cancelada |
| tipo_entrada | String | general o invitacion |
| importe_abonado | Decimal128 | Lo calcula el servidor; cero si es invitacion |
| metodo_pago | String | efectivo o transferencia; obligatorio si importe > 0 |
| actividades_seleccionadas | Array de strings | Codigos del evento; sin repetir; puede estar vacio |
| preferencias_alimentarias | Array de strings | Opcional |
| fecha_cancelacion | Date | Se agrega al cancelar |

## Regla de conocimientos

Para confirmar una inscripcion debe cumplirse:

    conocimientos_requeridos del evento ⊆ usuario.conocimientos

Se exigen TODOS los requisitos. Un evento con [] acepta cualquier conjunto de
conocimientos. La API normaliza strings, rechaza vacios y quita repetidos.
Si faltan conocimientos devuelve 409 con detail.conocimientos_faltantes.
El catalogo fijo de ocho valores se usa en el generador; la API no limita los
conocimientos a ese catalogo. Editar requisitos se rechaza si invalida alguna
inscripcion confirmada existente.

## Atomicidad y consistencia

Al inscribirse se descuenta cupo con filtro por publicado, fecha futura y vacantes
positivas; se recupera el evento y, usando la misma sesion, se validan requisitos,
actividades, duplicado y pago, y se inserta la inscripcion. Una excepcion aborta
ambas escrituras. El indice unico es la garantia de unicidad concurrente.

Cancelar marca la inscripcion y restituye una vacante en una transaccion. Repetir
la cancelacion es idempotente: devuelve 200 sin sumar otra vacante. Se usa snapshot,
write concern majority y lectura del primario. Los callbacks no tienen efectos
externos para permitir reintentos del driver.

La recarga es diferente: el drop y la preparacion de colecciones/indice quedan
FUERA de la transaccion; toda la insercion queda dentro. Un fallo de insercion
no recupera el contenido borrado por el drop. Se requiere backup antes de recargar.
