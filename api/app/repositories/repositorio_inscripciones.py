from bson import ObjectId
from pymongo.errors import OperationFailure


def verificar_indice_usuario(base):
    """Solo lectura: bloquear escrituras hasta completar la migracion de la base."""
    for indice in base.inscripciones.list_indexes():
        if (indice["name"] == "evento_usuario_dni_unico"
            and list(indice["key"].items()) == [("evento_id", 1), ("usuario.dni", 1)]
            and indice.get("unique") is True and not indice.get("sparse")
            and not indice.get("partialFilterExpression")):
            return
    raise OperationFailure("Base no migrada: falta el indice unico evento_usuario_dni_unico. Complete la recarga antes de usar inscripciones.")


def buscar_inscripcion(base, evento_id, dni, session):
    return base.inscripciones.find_one(
        {"evento_id": ObjectId(evento_id), "usuario.dni": dni}, session=session)


def insertar_inscripcion(base, documento, session):
    return base.inscripciones.insert_one(documento, session=session).inserted_id


def listar_inscripciones_evento(base, evento_id, dni=None):
    filtro = {"evento_id": ObjectId(evento_id)}
    if dni is not None:
        filtro["usuario.dni"] = dni
    return list(base.inscripciones.find(filtro).sort([("fecha_inscripcion", -1), ("_id", 1)]).limit(100))


def buscar_inscripcion_por_id(base, inscripcion_id, session):
    return base.inscripciones.find_one({"_id": ObjectId(inscripcion_id)}, session=session)


def marcar_inscripcion_cancelada(base, inscripcion_id, ahora, session):
    return base.inscripciones.update_one(
        {"_id": ObjectId(inscripcion_id), "estado_inscripcion": "confirmada"},
        {"$set": {"estado_inscripcion": "cancelada", "fecha_cancelacion": ahora}},
        session=session).modified_count == 1


def hay_confirmadas_sin_conocimientos(base, evento_id, requisitos, session):
    return base.inscripciones.find_one(
        {"evento_id": evento_id, "estado_inscripcion": "confirmada", "$expr": {
            "$not": [{"$setIsSubset": [{"$literal": requisitos}, {"$ifNull": ["$usuario.conocimientos", []]}]}]}},
        {"_id": 1}, session=session) is not None
