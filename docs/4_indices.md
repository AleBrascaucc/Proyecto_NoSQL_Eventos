# 4. Indices y planes de ejecucion

Mediciones observadas el 29/10/2026 despues de cargar 20 eventos y 200 inscripciones,
antes de agregar la demo de Postman. Salida completa en anexo/indices_modelo.txt.

Cada prueba conserva filtro, orden y proyeccion. hint({$natural:1}) fuerza el
recorrido natural, sin borrar indices; hint(nombre) fuerza el indice candidato.
La comparacion no prueba que el optimizador lo elija sin hint ni garantiza menor
tiempo con un dataset tan pequeno. No se midieron tiempos para inferir aceleraciones.

## Resultados observados

| Indice | Plan sin / con indice | Docs sin / con | Claves sin / con | Devueltos en ambos |
|---|---|---:|---:|---:|
| estado_ciudad_fecha | SORT + COLLSCAN / FETCH + IXSCAN | 20 / 4 | 0 / 4 | 4 |
| evento_usuario_dni_unico | COLLSCAN / FETCH + IXSCAN | 200 / 1 | 0 / 1 | 1 |
| conocimientos_requeridos_multikey | COLLSCAN / FETCH + IXSCAN | 20 / 4 | 0 / 4 | 4 |

## 1. Estado, ciudad y fecha

```javascript
{ estado: 1, "sede.ciudad": 1, fecha_inicio: 1 }
```

Consulta: publicados en Cordoba con fecha_inicio en noviembre de 2026; sort por
fecha_inicio ascendente. La igualdad en los dos primeros campos permite aprovechar
el rango y orden del tercero. El plan indexado revisa cuatro documentos y evita
la etapa SORT que aparecia en el recorrido natural. isMultiKey: false.

Costo: espacio y mantenimiento por inserciones o cambios de estado, sede.ciudad y
fecha_inicio. No optimiza por igual todas las combinaciones de filtros de la API.

## 2. Unicidad por evento y DNI

```javascript
{ evento_id: 1, "usuario.dni": 1 }
// unique: true, name: "evento_usuario_dni_unico"
```

Consulta exacta por evento_id del Taller de MongoDB y usuario.dni 44123456.
El plan indexado examina una clave y un documento frente a 200 documentos del
recorrido natural. isUnique: true, isMultiKey: false.

Justificacion: busqueda frecuente e integridad; impide duplicar un DNI en un evento,
incluso si la inscripcion anterior esta cancelada. Reemplaza al indice sobre
participante.dni. Costo: almacenamiento, mantenimiento y comprobacion de unicidad.

Se intento insertar una copia con OTRO _id y el mismo evento/DNI. MongoDB rechazo
la operacion con 11000 por el indice compuesto. La prueba se ejecuto en una
transaccion y los totales antes/despues fueron 200/200.

## 3. Requisitos de conocimientos (multikey)

```javascript
{ conocimientos_requeridos: 1 }
// name: "conocimientos_requeridos_multikey"
```

Consulta: eventos que requieren javascript. isMultiKey: true y multiKeyPaths
identifica conocimientos_requeridos como array. El plan examina cuatro claves y
cuatro documentos, con los mismos cuatro resultados del recorrido de 20 documentos.

Costo: genera claves por elementos del array y debe mantenerlas al modificarlo.
Esta medicion corresponde a igualdad por un conocimiento; NO demuestra que el
indice optimice el $setIsSubset usado para elegibilidad.

## Lectura de metricas

- totalDocsExamined: documentos que el plan debio examinar.
- totalKeysExamined: entradas del indice examinadas; 0 en recorrido natural.
- nReturned: resultados entregados; debe coincidir entre los dos planes.
- FETCH: recupera documentos a partir de claves; estas no son consultas cubiertas.

Los indices automaticos de _id tambien existen; los tres anteriores son los
indices adicionales del proyecto.
