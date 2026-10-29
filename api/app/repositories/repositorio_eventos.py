from bson import ObjectId
from pymongo import ReturnDocument

def listar_eventos(base, filtros):
    from bson import Decimal128
    consulta = {}
    for campo in ('categoria', 'estado'):
        valor = getattr(filtros, campo)
        if valor is not None:
            consulta[campo] = valor
    if filtros.ciudad is not None:
        consulta['sede.ciudad'] = filtros.ciudad
    if filtros.conocimiento is not None:
        consulta['conocimientos_requeridos'] = filtros.conocimiento
    if filtros.con_vacantes:
        consulta['vacantes_disponibles'] = {'$gt': 0}
    if filtros.etiqueta is not None:
        consulta['etiquetas'] = filtros.etiqueta
    fechas = {}
    if filtros.fecha_desde is not None:
        fechas['$gte'] = filtros.fecha_desde
    if filtros.fecha_hasta is not None:
        fechas['$lt'] = filtros.fecha_hasta
    if fechas:
        consulta['fecha_inicio'] = fechas
    precios = {}
    if filtros.precio_minimo is not None:
        precios['$gte'] = Decimal128(filtros.precio_minimo)
    if filtros.precio_maximo is not None:
        precios['$lte'] = Decimal128(filtros.precio_maximo)
    if precios:
        consulta['precio_entrada'] = precios
    documentos = base.eventos.find(consulta, {'_id': 1, 'titulo': 1, 'categoria': 1, 'estado': 1, 'fecha_inicio': 1, 'precio_entrada': 1, 'sede.ciudad': 1, 'vacantes_disponibles': 1, 'etiquetas': 1, 'conocimientos_requeridos': 1}).sort([('fecha_inicio', 1), ('_id', 1)]).limit(filtros.limite)
    eventos = []
    for documento in documentos:
        documento['id'] = str(documento.pop('_id'))
        documento['precio_entrada'] = str(documento['precio_entrada'])
        eventos.append(documento)
    return eventos

def buscar_evento_por_id(base, evento_id, session=None):
    return base.eventos.find_one({'_id': ObjectId(evento_id)}, session=session)

def insertar_evento(base, documento, session=None):
    resultado = base.eventos.insert_one(documento, session=session)
    return resultado.inserted_id

def actualizar_evento_documento(base, actual, cambios, session=None):
    return base.eventos.find_one_and_update({'_id': actual['_id'], 'estado': actual['estado'], 'capacidad_total': actual['capacidad_total'], 'vacantes_disponibles': actual['vacantes_disponibles']}, {'$set': cambios}, return_document=ReturnDocument.AFTER, session=session)

def evento_tiene_inscripciones(base, evento_id, session=None):
    inscripcion = base.inscripciones.find_one({'evento_id': ObjectId(evento_id)}, {'_id': 1}, session=session)
    return inscripcion is not None

def eliminar_borrador(base, evento_id, session=None):
    resultado = base.eventos.delete_one({'_id': ObjectId(evento_id), 'estado': 'borrador'}, session=session)
    return resultado.deleted_count

def cancelar_evento_documento(base, evento_id, ahora, session=None):
    return base.eventos.find_one_and_update({'_id': ObjectId(evento_id), 'estado': {'$in': ['borrador', 'publicado']}, 'fecha_inicio': {'$gt': ahora}}, {'$set': {'estado': 'cancelado'}}, return_document=ReturnDocument.AFTER, session=session)

def reservar_vacante(base, evento_id, ahora, session):
    return base.eventos.find_one_and_update({'_id': ObjectId(evento_id), 'estado': 'publicado', 'fecha_inicio': {'$gt': ahora}, 'vacantes_disponibles': {'$gt': 0}}, {'$inc': {'vacantes_disponibles': -1}}, return_document=ReturnDocument.AFTER, session=session)

def restituir_vacante(base, evento_id, session):
    return base.eventos.update_one({'_id': evento_id, '$expr': {'$lt': ['$vacantes_disponibles', '$capacidad_total']}}, {'$inc': {'vacantes_disponibles': 1}}, session=session).modified_count == 1
