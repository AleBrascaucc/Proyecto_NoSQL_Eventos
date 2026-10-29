const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {generarDatos} = require('../scripts/01_carga_datos.js');
const {auditar} = require('../scripts/04_verificaciones.js');
const crear = () => generarDatos({objectId: x => x, decimal: x => x});
const limpio = x => JSON.parse(JSON.stringify(x));
const sinErrores = d => Object.values(auditar(d.eventos,d.inscripciones)).every(a=>a.length===0);

test('20 eventos, 200 inscripciones, 152 confirmadas y 48 canceladas',()=>{
 const d=crear();assert.equal(d.eventos.length,20);assert.equal(d.inscripciones.length,200);
 assert.equal(d.inscripciones.filter(i=>i.estado_inscripcion==='confirmada').length,152);
 assert.equal(d.inscripciones.filter(i=>i.estado_inscripcion==='cancelada').length,48);
});
test('el generador es determinista, incluidos los IDs',()=>assert.deepEqual(crear(),crear()));
test('IDs fijos validos y sin repeticiones',()=>{
 const d=crear();for(const lista of [d.eventos,d.inscripciones]) {
  assert.equal(new Set(lista.map(x=>x._id)).size,lista.length);
  assert.ok(lista.every(x=>/^[0-9a-f]{24}$/.test(x._id)));
 }
});
test('cuatro estados y dos borradores sin inscripciones',()=>{
 const d=crear();assert.deepEqual([...new Set(d.eventos.map(e=>e.estado))].sort(),['borrador','cancelado','finalizado','publicado']);
 const borradores=d.eventos.filter(e=>e.estado==='borrador');assert.equal(borradores.length,2);
 assert.ok(borradores.every(e=>!d.inscripciones.some(i=>i.evento_id===e._id)));
});
test('evento lleno conservado y cupos calculados con confirmadas',()=>{
 const d=crear();assert.equal(d.eventos.filter(e=>e.vacantes_disponibles===0).length,1);
 assert.equal(d.eventos.find(e=>e.vacantes_disponibles===0).titulo,'Emprendimientos 3');
 for(const e of d.eventos)assert.equal(e.vacantes_disponibles,e.capacidad_total-d.inscripciones.filter(i=>i.evento_id===e._id&&i.estado_inscripcion==='confirmada').length);
});
test('gratuitos, pagos, invitaciones y opcionales ausentes',()=>{
 const d=crear();assert.ok(d.eventos.some(e=>+e.precio_entrada===0));assert.ok(d.eventos.some(e=>+e.precio_entrada>0));
 assert.ok(d.eventos.some(e=>!('etiquetas'in e)));assert.ok(d.inscripciones.some(i=>!('institucion'in i.usuario)));
 assert.ok(d.inscripciones.some(i=>!('metodo_pago'in i)));assert.ok(d.inscripciones.some(i=>i.tipo_entrada==='invitacion'));
});
test('todos cumplen conocimientos, incluidos cancelados; casos exactos y extras',()=>{
 const d=crear();let exactos=0,extras=0;
 for(const i of d.inscripciones){const e=d.eventos.find(e=>e._id===i.evento_id);
  assert.ok(e.conocimientos_requeridos.every(c=>i.usuario.conocimientos.includes(c)));
  if(i.usuario.conocimientos.length===e.conocimientos_requeridos.length)exactos++;else extras++;
 }
 assert.ok(exactos>0);assert.ok(extras>0);assert.ok(d.eventos.some(e=>e.conocimientos_requeridos.length===0));
});
test('normalizacion, catalogo fijo y eliminacion de participante',()=>{
 const d=crear(),catalogo=['python','javascript','sql','mongodb','docker','git','excel','diseño'];
 for(const e of d.eventos)assert.ok(e.conocimientos_requeridos.every(c=>catalogo.includes(c)));
 for(const i of d.inscripciones){assert.ok(!('participante'in i));assert.ok(i.usuario.conocimientos.every(c=>catalogo.includes(c)&&c===c.trim().toLowerCase()));}
});
test('auditoria del poblado: nueve controles en cero',()=>assert.ok(sinErrores(crear())));
const mutaciones=[
 ['inscripciones_sin_evento',d=>d.inscripciones[0].evento_id='ffffffffffffffffffffffff'],
 ['duplicados_evento_usuario_dni',d=>d.inscripciones.push({...d.inscripciones[0],_id:'ffffffffffffffffffffffff'})],
 ['eventos_con_cupos_inconsistentes',d=>d.eventos[0].vacantes_disponibles++],
 ['confirmadas_sin_conocimientos',d=>d.inscripciones[0].usuario.conocimientos=[]],
 ['actividades_seleccionadas_inexistentes',d=>d.inscripciones[0].actividades_seleccionadas=['ACT-NO']],
 ['documentos_con_participante',d=>d.inscripciones[0].participante={}],
 ['conocimientos_sin_normalizar',d=>d.inscripciones[0].usuario.conocimientos=[' SQL ']],
 ['conocimientos_sin_normalizar',d=>delete d.eventos[0].conocimientos_requeridos],
 ['usuarios_invalidos',d=>delete d.inscripciones[0].usuario],
 ['borradores_con_inscripciones',d=>d.eventos[0].estado='borrador'],
];
for(const [control,cambiar] of mutaciones)test('auditoria detecta '+control+' ('+mutaciones.indexOf(mutaciones.find(x=>x[1]===cambiar))+')',()=>{
 const d=crear();cambiar(d);assert.ok(auditar(d.eventos,d.inscripciones)[control].length>0);
});
test('faltantes en una inscripcion cancelada no se cuentan como confirmada',()=>{
 const d=crear();const i=d.inscripciones.find(i=>i.estado_inscripcion==='cancelada');i.usuario.conocimientos=[];
 assert.equal(auditar(d.eventos,d.inscripciones).confirmadas_sin_conocimientos.length,0);
});
test('consulta de elegibilidad: 5 publicados para javascript y git',()=>{
 const d=crear();assert.equal(d.eventos.filter(e=>e.estado==='publicado'&&e.conocimientos_requeridos.every(c=>['javascript','git'].includes(c))).length,5);
});
test('frecuencias esperadas: 8 conocimientos y excel con 72',()=>{
 const d=crear(),cuenta={};for(const i of d.inscripciones.filter(i=>i.estado_inscripcion==='confirmada'))for(const c of i.usuario.conocimientos)cuenta[c]=(cuenta[c]||0)+1;
 assert.equal(Object.keys(cuenta).length,8);assert.equal(cuenta.excel,72);assert.equal(Math.max(...Object.values(cuenta)),72);
});

function entornoCarga({primario=true,fallarInsert=false}={}) {
 const estado={eventos:[],inscripciones:[],nombres:[],registro:[]};
 let enTransaccion=false;
 const coleccion=nombre=>({
  createIndex:async(key,op)=>{assert.equal(enTransaccion,false);estado.registro.push('indice:'+op.name);return op.name;},
  insertMany:async docs=>{assert.ok(enTransaccion);estado.registro.push('insertar:'+nombre);if(fallarInsert&&nombre==='inscripciones')throw Error('fallo simulado');estado[nombre].push(...limpio(docs));},
  countDocuments:async()=>estado[nombre].length,
 });
 const base={adminCommand:async()=>({setName:'rs0',isWritablePrimary:primario}),getCollectionNames:async()=>estado.nombres,
  runCommand:async cmd=>{assert.equal(enTransaccion,false);if(cmd.drop){estado.registro.push('drop:'+cmd.drop);estado[cmd.drop]=[];estado.nombres=estado.nombres.filter(n=>n!==cmd.drop);}else{estado.registro.push('crear:'+cmd.create);estado.nombres.push(cmd.create);}return{ok:1};},
  eventos:coleccion('eventos'),inscripciones:coleccion('inscripciones')};
 const sesion={getDatabase:()=>base,endSession:async()=>{},withTransaction:async fn=>{
  const previo={eventos:limpio(estado.eventos),inscripciones:limpio(estado.inscripciones)};enTransaccion=true;
  try{await fn();}catch(e){estado.eventos=previo.eventos;estado.inscripciones=previo.inscripciones;throw e;}finally{enTransaccion=false;}
 }};
 const contexto={db:{getSiblingDB:()=>base,getMongo:()=>({startSession:()=>sesion})},ObjectId:x=>x,NumberDecimal:x=>x,print:()=>{},quit:()=>{throw Error('quit 1');}};
 return{estado,ejecutar:()=>vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../scripts/01_carga_datos.js'),'utf8'),contexto)};
}
test('flujo simulado: carga desde vacio y repeticion conservan exactamente 20/200',async()=>{
 const e=entornoCarga();await e.ejecutar();const primera=limpio({eventos:e.estado.eventos,inscripciones:e.estado.inscripciones});
 await e.ejecutar();assert.deepEqual(limpio({eventos:e.estado.eventos,inscripciones:e.estado.inscripciones}),primera);
 assert.equal(e.estado.eventos.length,20);assert.equal(e.estado.inscripciones.length,200);
});
test('flujo simulado: indice unico antes de insertar ambas colecciones',async()=>{
 const e=entornoCarga();await e.ejecutar();const r=e.estado.registro;
 assert.ok(r.indexOf('indice:evento_usuario_dni_unico')<r.indexOf('insertar:eventos'));
 assert.ok(r.indexOf('insertar:eventos')<r.indexOf('insertar:inscripciones'));
});
test('flujo simulado: sin primario no se ejecuta ningun drop',async()=>{
 const e=entornoCarga({primario:false});await assert.rejects(e.ejecutar());assert.equal(e.estado.registro.length,0);
});
test('flujo simulado: fallo de insercion aborta lote pero no restaura el drop previo',async()=>{
 const e=entornoCarga({fallarInsert:true});await assert.rejects(e.ejecutar());
 assert.equal(e.estado.eventos.length,0);assert.equal(e.estado.inscripciones.length,0);
 assert.ok(e.estado.nombres.includes('eventos'));assert.ok(e.estado.nombres.includes('inscripciones'));
});
test('12 consultas documentadas, sin operaciones de indices ni escrituras',()=>{
 const s=fs.readFileSync(path.join(__dirname,'../scripts/03_consultas.js'),'utf8');
 assert.equal((s.match(/\/\/ Enunciado:/g)||[]).length,12);assert.equal((s.match(/\/\/ Requisito:/g)||[]).length,12);assert.equal((s.match(/\/\/ Esperado:/g)||[]).length,12);
 assert.doesNotMatch(s,/createIndex\(|insertOne\(|updateOne\(|deleteOne\(/);assert.match(s,/\$setIsSubset/);assert.match(s,/\$usuario\.conocimientos/);
});

test('conserva todos los campos anteriores, excepto renombre usuario, conocimientos e IDs de inscripcion',async()=>{
 const anterior={eventos:[],inscripciones:[]};
 const coleccion=nombre=>({
  createIndex:async()=>{},
  findOne:async filtro=>anterior[nombre].find(d=>Object.entries(filtro).every(([k,v])=>d[k]===v)),
  updateOne:async(filtro,update)=>{
   let doc=anterior[nombre].find(d=>Object.entries(filtro).every(([k,v])=>k==='participante.dni'?d.participante?.dni===v:d[k]===v));
   if(!doc&&update.$setOnInsert){doc=limpio(update.$setOnInsert);anterior[nombre].push(doc);}
   if(doc&&update.$set)Object.assign(doc,limpio(update.$set));
  },
  countDocuments:async(filtro)=>anterior[nombre].filter(d=>Object.entries(filtro).every(([k,v])=>d[k]===v)).length,
 });
 const base={eventos:coleccion('eventos'),inscripciones:coleccion('inscripciones'),getCollectionNames:async()=>['eventos','inscripciones']};
 const sesion={getDatabase:()=>base,withTransaction:async fn=>fn(),endSession:async()=>{}};
 const contexto={db:{getSiblingDB:()=>base,getMongo:()=>({startSession:()=>sesion})},ObjectId:x=>x,NumberDecimal:x=>x,print:()=>{},quit:()=>{throw Error('fallo fuente original');}};
 await vm.runInNewContext(fs.readFileSync(path.join(__dirname,'fixtures/carga_semana2_original.js'),'utf8'),contexto);
 const nuevo=limpio(crear());
 for(const e of nuevo.eventos)delete e.conocimientos_requeridos;
 for(const i of nuevo.inscripciones){i.participante=i.usuario;delete i.usuario;delete i.participante.conocimientos;delete i._id;}
 assert.deepEqual(nuevo.eventos,limpio(anterior.eventos));
 assert.deepEqual(nuevo.inscripciones,limpio(anterior.inscripciones));
});
