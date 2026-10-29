# Bloque 4: scripts del nuevo modelo

## Alcance de esta instalacion

aplicar_bloque4.ps1 SOLO respalda y copia archivos en la rama
cambio-modelo-y-estructura. No ejecuta mongosh, Docker, Git add/commit/push,
la carga ni la API. La recarga requiere una confirmacion posterior del usuario.

Conservar el backup de MongoDB ya generado en la carpeta original:
proyecto-eventos/backups/backup_antes_cambio.archive (112073 bytes).
El respaldo que crea este instalador es SOLO de codigo, no de la base.

## Archivos

- scripts/01_carga_datos.js: recarga destructiva de las dos colecciones.
- scripts/02_indices.js: tres indices, comparacion de planes y prueba de duplicado.
- scripts/03_consultas.js: doce consultas con enunciado, requisito y resultado esperado.
- scripts/04_verificaciones.js: nueve controles de consistencia de solo lectura.
- tests/scripts_bloque4.test.cjs: pruebas locales con Node, sin dependencias externas.
- tests/fixtures/carga_semana2_original.js: fuente original del repo, SOLO como fixture
  para comprobar que no cambiaron los campos anteriores. No usar para recargar.

## 01 - Recarga

Base fija: gestion_eventos. Antes del drop comprueba que exista un primario de
replica set y genera/valida todo el lote en memoria. No genera fechas relativas,
valores aleatorios ni IDs variables.

Borra SOLO eventos e inscripciones, crea ambas colecciones y crea el indice unico
sobre evento_id y usuario.dni ANTES de insertar. Toda la insercion de los 20 eventos
y 200 inscripciones se ejecuta dentro de UNA transaccion con snapshot/majority.

El drop y la creacion de colecciones/indice ocurren FUERA de la transaccion.
Si falla la insercion, las colecciones pueden quedar vacias: el aborto de la
transaccion NO recupera los datos borrados previamente. Por eso se exige el backup.
No ejecutar la API ni otros escritores durante esta recarga y sus verificaciones.

Conserva los IDs de eventos y los titulos, fechas, precios, estados, actividades,
sedes, nombres de personas y campos opcionales del poblado inicial. Se agregan IDs
fijos de inscripcion; las inscripciones previas y las dos pruebas de semana 3 se
eliminan con el drop, como pide la recarga completa.

Catalogo fijo: python, javascript, sql, mongodb, docker, git, excel, diseño.
Requisitos: Tecnologia javascript/git, Educacion excel, Cultura diseño y Negocios
sql/excel. El Taller de MongoDB requiere mongodb/docker. Algunos eventos no
requieren conocimientos. Cada inscripcion cumple TODOS los requisitos; algunas
personas tienen exactamente los requisitos y otras tambien un conocimiento extra.

Los cupos se calculan usando solo las confirmadas. Resultado del generador:
20 eventos; 200 inscripciones (152 confirmadas, 48 canceladas); dos borradores sin
inscripciones; Emprendimientos 3 completo. Se conservan gratuitos, pagos,
invitaciones y documentos con campos opcionales ausentes.

## 02 - Indices

Indices adicionales a los automaticos de _id:

1. estado_ciudad_fecha: {estado:1, 'sede.ciudad':1, fecha_inicio:1} en eventos.
2. evento_usuario_dni_unico: {evento_id:1, 'usuario.dni':1}, unique, en inscripciones.
3. conocimientos_requeridos_multikey: {conocimientos_requeridos:1} en eventos.

Cada comparacion ejecuta EL MISMO filtro y orden dos veces:
- hint({$natural:1}): recorrido natural (COLLSCAN), sin borrar indices.
- hint(nombre): fuerza el indice candidato (IXSCAN).

Se imprimen el plan ganador, las etapas, totalKeysExamined, totalDocsExamined y
nReturned. El script comprueba que se devuelva la misma cantidad de resultados.
Tambien imprime justificacion y costo de cada indice. El indice multikey se prueba
con igualdad de un requisito, NO con $setIsSubset, que no se da por optimizado.

Con solo 20/200 documentos no se promete una mejora de tiempo, ni que el optimizador
elija el indice sin hint. Esta es una comparacion controlada del acceso a datos.

La prueba de duplicado copia una inscripcion usando OTRO _id y el MISMO evento/DNI.
Debe fallar con 11000 por el indice compuesto. Se ejecuta en una transaccion que
se aborta incluso si la insercion se aceptara inesperadamente. Comprueba que el
total final coincida con el inicial. No descuenta ni restituye vacantes.

## 03 - Consultas

Conserva las diez consultas anteriores y quita del archivo la creacion de indices.
Cada consulta tiene enunciado, requisito y resultado esperado en comentarios Y
salida de consola. Agrega:
- Publicados cuyos requisitos son un subconjunto de ['javascript','git']: 5 eventos.
  Incluye requisitos vacios. Cumplir conocimientos no garantiza cupo ni fecha futura.
- Conocimientos mas frecuentes de inscripciones confirmadas: 8 conocimientos,
  encabezados por excel con 72. Se cuentan inscripciones, no personas distintas
  entre eventos; un registro puede aportar a varios conocimientos.

La consulta de proximos eventos usa la fecha REAL del dia; puede devolver menos
resultados si se ejecuta despues de noviembre de 2026. Las otras fechas del
poblado se conservaron porque el usuario pidio no cambiarlas.

La recaudacion es BRUTA registrada por mes de inscripcion: incluye canceladas,
no supone devoluciones y no representa beneficio neto. La consulta 10 incluye
todos los estados como control; el indicador I2 de analisis excluira borradores
y cancelados como se definio anteriormente.

## 04 - Verificaciones

Solo lectura, usando mapas en memoria sobre el dataset pequeno (220 documentos).
Para volumenes grandes deberian migrarse estos controles a agregaciones/batches.
Imprime totales por separado y nueve controles que deben dar 0:
- inscripciones sin evento;
- duplicados por evento y usuario.dni;
- eventos con cupos inconsistentes;
- confirmadas que no cumplen conocimientos;
- actividades seleccionadas inexistentes;
- documentos que aun tienen participante;
- conocimientos no normalizados, ausentes, con tipo incorrecto o repetidos;
- usuarios invalidos;
- borradores con inscripciones.

Si encuentra inconsistencias termina con codigo 1 y muestra hasta cinco ejemplos
por control. Tambien rechaza una base vacia/incompleta para no informar un falso
resultado correcto. No exige siempre 20/200, ya que las pruebas de API agregaran
registros validos mas adelante.

## Verificacion realizada localmente

28 pruebas aprobadas de generacion, campos originales, normalizacion, conocimiento,
cupos, auditoria e introduccion intencional de errores. Tambien se probo el flujo
de carga mediante dobles de MongoDB: repetir la carga, orden del indice, ausencia
de primario y fallo de insercion. Se reviso sintaxis JS de los cuatro scripts.

NO se ejecutaron estos scripts contra MongoDB real; no se midieron indices ni
se comprobaron transacciones del servidor. Eso se verificara en Docker despues
de la confirmacion de recarga. Los valores esperados son del generador, no salida
inventada de una ejecucion en MongoDB.

Para repetir las pruebas locales (si Node esta instalado), desde la raiz:

    node --test .\tests\scripts_bloque4.test.cjs

## Proxima ejecucion, TODAVIA PENDIENTE DE AUTORIZACION

Se detendra la API, se confirmara proyecto/volumen del Compose original y se
copiaran los scripts al contenedor existente antes de recargar. No ejecutar
Compose desde la carpeta nueva sin fijar el proyecto: podria crear otro volumen.

Orden final solicitado: 01_carga_datos.js, 04_verificaciones.js, 03_consultas.js,
02_indices.js. La evidencia real se guardara en docs/anexo/. Los comandos de
recarga se daran por separado, despues de confirmar este bloque instalado.

## Fuentes tecnicas

- https://www.mongodb.com/docs/v8.0/core/transactions-operations/
- https://www.mongodb.com/docs/manual/core/transactions/
- https://www.mongodb.com/docs/manual/reference/method/db.collection.explain/
- Fuente del fixture original:
  https://github.com/AleBrascaucc/Proyecto_NoSQL_Eventos/blob/73ef418e663af5749ba735e80bc48f6963a58b79/carga_datos.js
