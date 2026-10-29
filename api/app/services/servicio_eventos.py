from app.db import ejecutar_transaccion
from app.repositories.repositorio_inscripciones import hay_confirmadas_sin_conocimientos
from bson import Decimal128
from app.schemas.modelos import EventoCrear
from app.repositories.repositorio_eventos import insertar_evento
from datetime import datetime, timezone
from app.schemas.modelos import EventoActualizar
from app.repositories.repositorio_eventos import buscar_evento_por_id, actualizar_evento_documento
from app.repositories.repositorio_eventos import evento_tiene_inscripciones, eliminar_borrador
from app.repositories.repositorio_eventos import cancelar_evento_documento

def _crear_evento(base, datos: EventoCrear, session):
    documento = datos.model_dump(exclude_none=True)
    documento['precio_entrada'] = Decimal128(documento['precio_entrada'])
    documento['estado'] = 'borrador'
    documento['vacantes_disponibles'] = documento['capacidad_total']
    identificador = insertar_evento(base, documento, session=session)
    documento.pop('_id', None)
    documento['id'] = str(identificador)
    return documento

def _modificar_evento(base, evento_id, datos: EventoActualizar, session):
    actual = buscar_evento_por_id(base, evento_id, session=session)
    if actual is None:
        raise LookupError('El evento no existe.')
    if actual['estado'] in ('cancelado', 'finalizado'):
        raise ValueError('Esta operacion solo permite modificar borradores o publicados.')
    cambios = datos.model_dump(exclude_unset=True)
    if 'capacidad_total' in cambios:
        nueva_capacidad = cambios['capacidad_total']
        ocupadas = actual['capacidad_total'] - actual['vacantes_disponibles']
        if nueva_capacidad > actual['sede']['capacidad_maxima']:
            raise ValueError('La capacidad supera la capacidad maxima de la sede.')
        if nueva_capacidad < ocupadas:
            raise ValueError('La capacidad no puede ser menor que los lugares ocupados.')
        cambios['vacantes_disponibles'] = nueva_capacidad - ocupadas
    if cambios.get('estado') == 'publicado' and actual['estado'] == 'borrador':
        inicio = actual['fecha_inicio']
        if inicio.tzinfo is None:
            inicio = inicio.replace(tzinfo=timezone.utc)
        if inicio <= datetime.now(timezone.utc):
            raise ValueError('No se puede publicar un evento que ya comenzo.')
    if 'conocimientos_requeridos' in cambios:
        if hay_confirmadas_sin_conocimientos(base, actual['_id'], cambios['conocimientos_requeridos'], session):
            raise ValueError('Los nuevos requisitos no son cumplidos por todas las inscripciones confirmadas.')
    if 'precio_entrada' in cambios:
        cambios['precio_entrada'] = Decimal128(cambios['precio_entrada'])
    actualizado = actualizar_evento_documento(base, actual, cambios, session=session)
    if actualizado is None:
        raise ValueError('El evento cambio durante la operacion. Consulte y reintente.')
    actualizado['id'] = str(actualizado.pop('_id'))
    return actualizado

def _borrar_evento(base, evento_id, session):
    actual = buscar_evento_por_id(base, evento_id, session=session)
    if actual is None:
        raise LookupError('El evento no existe.')
    if actual['estado'] != 'borrador':
        raise ValueError('Solo se pueden eliminar eventos en borrador.')
    if evento_tiene_inscripciones(base, evento_id, session=session):
        raise ValueError('No se puede eliminar un evento con inscripciones.')
    eliminados = eliminar_borrador(base, evento_id, session=session)
    if eliminados == 0:
        raise ValueError('El evento cambio durante la operacion. Consulte y reintente.')

def _cancelar_evento(base, evento_id, session):
    actual = buscar_evento_por_id(base, evento_id, session=session)
    if actual is None:
        raise LookupError('El evento no existe.')
    if actual['estado'] == 'cancelado':
        actual['id'] = str(actual.pop('_id'))
        return actual
    if actual['estado'] not in ('borrador', 'publicado'):
        raise ValueError('Solo se pueden cancelar eventos en borrador o publicados.')
    ahora = datetime.now(timezone.utc)
    inicio = actual['fecha_inicio']
    if inicio.tzinfo is None:
        inicio = inicio.replace(tzinfo=timezone.utc)
    if inicio <= ahora:
        raise ValueError('No se puede cancelar un evento que ya comenzo.')
    actualizado = cancelar_evento_documento(base, evento_id, ahora, session=session)
    if actualizado is None:
        raise ValueError('El evento cambio durante la operacion. Consulte y reintente.')
    actualizado['id'] = str(actualizado.pop('_id'))
    return actualizado

def crear_evento(base, datos):
    return ejecutar_transaccion(base, lambda session: _crear_evento(base, datos, session))

def modificar_evento(base, evento_id, datos):
    return ejecutar_transaccion(base, lambda session: _modificar_evento(base, evento_id, datos, session))

def borrar_evento(base, evento_id):
    return ejecutar_transaccion(base, lambda session: _borrar_evento(base, evento_id, session))

def cancelar_evento(base, evento_id):
    return ejecutar_transaccion(base, lambda session: _cancelar_evento(base, evento_id, session))
