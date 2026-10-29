from fastapi import APIRouter, HTTPException, Request
from pymongo.errors import PyMongoError
from app.services import consultas
from fastapi import Query
from app.services.consultas import listar_eventos
from typing import Annotated
from app.schemas.modelos import FiltrosEventos
from bson import ObjectId, Decimal128
from fastapi.encoders import jsonable_encoder
from app.services.consultas import buscar_evento_por_id
from app.schemas.modelos import EventoCrear
from app.services.servicio_eventos import crear_evento
from app.schemas.modelos import EventoActualizar
from app.services.servicio_eventos import modificar_evento
from fastapi import Response
from app.services.servicio_eventos import borrar_evento
from app.schemas.modelos import InscripcionCrear
from app.services.servicio_inscripciones import confirmar_inscripcion
from app.services.consultas import listar_inscripciones_evento
from app.services.servicio_inscripciones import cancelar_inscripcion
from app.services.servicio_eventos import cancelar_evento
router = APIRouter()

@router.get('/')
def inicio(request: Request):
    return {'mensaje': 'API de Gestion de Eventos funcionando'}

@router.get('/estado')
def consultar_estado(request: Request):
    try:
        return consultas.consultar_estado(request.app.state.base)
    except PyMongoError:
        raise HTTPException(status_code=503, detail='No se pudo consultar MongoDB.')

@router.get('/eventos')
def obtener_eventos(request: Request, filtros: Annotated[FiltrosEventos, Query()]):
    try:
        return listar_eventos(request.app.state.base, filtros)
    except PyMongoError:
        raise HTTPException(status_code=503, detail='No se pudieron consultar los eventos.')

@router.get('/eventos/{evento_id}')
def obtener_evento(request: Request, evento_id: str):
    if not ObjectId.is_valid(evento_id):
        raise HTTPException(status_code=422, detail='El identificador del evento no tiene un formato valido.')
    try:
        evento = buscar_evento_por_id(request.app.state.base, evento_id)
    except PyMongoError:
        raise HTTPException(status_code=503, detail='No se pudo consultar el evento.')
    if evento is None:
        raise HTTPException(status_code=404, detail='El evento no existe.')
    evento['id'] = str(evento.pop('_id'))
    return jsonable_encoder(evento, custom_encoder={ObjectId: str, Decimal128: str})

@router.post('/eventos', status_code=201)
def registrar_evento(request: Request, datos: EventoCrear):
    try:
        evento = crear_evento(request.app.state.base, datos)
    except PyMongoError:
        raise HTTPException(status_code=503, detail='No se pudo guardar el evento.')
    return jsonable_encoder(evento, custom_encoder={ObjectId: str, Decimal128: str})

@router.patch('/eventos/{evento_id}')
def actualizar_evento(request: Request, evento_id: str, datos: EventoActualizar):
    if not ObjectId.is_valid(evento_id):
        raise HTTPException(status_code=422, detail='El identificador del evento no tiene un formato valido.')
    try:
        evento = modificar_evento(request.app.state.base, evento_id, datos)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=getattr(error, 'detail', str(error)))
    except ValueError as error:
        raise HTTPException(status_code=409, detail=getattr(error, 'detail', str(error)))
    except PyMongoError:
        raise HTTPException(status_code=503, detail='No se pudo actualizar el evento.')
    return jsonable_encoder(evento, custom_encoder={ObjectId: str, Decimal128: str})

@router.delete('/eventos/{evento_id}', status_code=204)
def eliminar_evento(request: Request, evento_id: str):
    if not ObjectId.is_valid(evento_id):
        raise HTTPException(status_code=422, detail='El identificador del evento no tiene un formato valido.')
    try:
        borrar_evento(request.app.state.base, evento_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=getattr(error, 'detail', str(error)))
    except ValueError as error:
        raise HTTPException(status_code=409, detail=getattr(error, 'detail', str(error)))
    except PyMongoError:
        raise HTTPException(status_code=503, detail='No se pudo eliminar el evento.')
    return Response(status_code=204)

@router.post('/eventos/{evento_id}/inscripciones', status_code=201)
def registrar_inscripcion(request: Request, evento_id: str, datos: InscripcionCrear):
    if not ObjectId.is_valid(evento_id):
        raise HTTPException(status_code=422, detail='El identificador del evento no tiene un formato valido.')
    try:
        inscripcion = confirmar_inscripcion(request.app.state.base, evento_id, datos)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=getattr(error, 'detail', str(error)))
    except ValueError as error:
        raise HTTPException(status_code=409, detail=getattr(error, 'detail', str(error)))
    except PyMongoError:
        raise HTTPException(status_code=503, detail='No se pudo completar el registro de la inscripcion.')
    return jsonable_encoder(inscripcion, custom_encoder={ObjectId: str, Decimal128: str})

@router.get('/eventos/{evento_id}/inscripciones')
def consultar_inscripciones(request: Request, evento_id: str, dni: str | None=Query(default=None, pattern='^[0-9]+$')):
    if not ObjectId.is_valid(evento_id):
        raise HTTPException(status_code=422, detail='El identificador del evento no tiene un formato valido.')
    try:
        if buscar_evento_por_id(request.app.state.base, evento_id) is None:
            raise HTTPException(status_code=404, detail='El evento no existe.')
        documentos = listar_inscripciones_evento(request.app.state.base, evento_id, dni)
    except PyMongoError:
        raise HTTPException(status_code=503, detail='No se pudieron consultar las inscripciones.')
    for documento in documentos:
        documento['id'] = str(documento.pop('_id'))
    return jsonable_encoder(documentos, custom_encoder={ObjectId: str, Decimal128: str})

@router.patch('/inscripciones/{inscripcion_id}/cancelacion')
def cancelar_registro(request: Request, inscripcion_id: str):
    if not ObjectId.is_valid(inscripcion_id):
        raise HTTPException(status_code=422, detail='El identificador de la inscripcion no tiene un formato valido.')
    try:
        inscripcion = cancelar_inscripcion(request.app.state.base, inscripcion_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=getattr(error, 'detail', str(error)))
    except ValueError as error:
        raise HTTPException(status_code=409, detail=getattr(error, 'detail', str(error)))
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=getattr(error, 'detail', str(error)))
    except PyMongoError:
        raise HTTPException(status_code=503, detail='No se pudo completar la cancelacion.')
    return jsonable_encoder(inscripcion, custom_encoder={ObjectId: str, Decimal128: str})

@router.patch('/eventos/{evento_id}/cancelacion')
def cancelar_evento_api(request: Request, evento_id: str):
    if not ObjectId.is_valid(evento_id):
        raise HTTPException(status_code=422, detail='El identificador del evento no tiene un formato valido.')
    try:
        evento = cancelar_evento(request.app.state.base, evento_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=getattr(error, 'detail', str(error)))
    except ValueError as error:
        raise HTTPException(status_code=409, detail=getattr(error, 'detail', str(error)))
    except PyMongoError:
        raise HTTPException(status_code=503, detail='No se pudo cancelar el evento.')
    return jsonable_encoder(evento, custom_encoder={ObjectId: str, Decimal128: str})
