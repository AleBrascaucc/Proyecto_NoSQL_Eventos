from app.repositories import repositorio_eventos as eventos
from app.repositories import repositorio_inscripciones as inscripciones
from app.repositories import estado


def consultar_estado(base):
    return estado.consultar_estado(base)


def listar_eventos(base, filtros):
    return eventos.listar_eventos(base, filtros)


def buscar_evento_por_id(base, evento_id):
    return eventos.buscar_evento_por_id(base, evento_id)


def listar_inscripciones_evento(base, evento_id, dni=None):
    return inscripciones.listar_inscripciones_evento(base, evento_id, dni)
