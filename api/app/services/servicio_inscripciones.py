from datetime import datetime, timezone
from decimal import Decimal
from bson import Decimal128
from pymongo.errors import DuplicateKeyError
from app.db import ejecutar_transaccion
from app.repositories import repositorio_eventos as eventos
from app.repositories import repositorio_inscripciones as inscripciones
from app.schemas.modelos import InscripcionCrear


class ConocimientosFaltantes(ValueError):
    def __init__(self, faltantes):
        super().__init__("Faltan conocimientos requeridos: " + ", ".join(faltantes))
        self.detail = {"mensaje": str(self), "conocimientos_faltantes": faltantes}


def respuesta_inscripcion(documento):
    resultado = dict(documento)
    resultado["id"] = str(resultado.pop("_id"))
    return resultado


def confirmar_inscripcion(base, evento_id, datos: InscripcionCrear):
    inscripciones.verificar_indice_usuario(base)

    def operacion(session):
        ahora = datetime.now(timezone.utc)
        # Se reserva PRIMERO; las validaciones posteriores pueden abortar toda la transaccion.
        evento = eventos.reservar_vacante(base, evento_id, ahora, session)
        if evento is None:
            actual = eventos.buscar_evento_por_id(base, evento_id, session)
            if actual is None:
                raise LookupError("El evento no existe.")
            if actual["estado"] != "publicado":
                raise ValueError("Solo se admiten inscripciones en eventos publicados.")
            if actual["fecha_inicio"] <= ahora:
                raise ValueError("El evento ya comenzo.")
            raise ValueError("El evento no tiene vacantes.")

        if inscripciones.buscar_inscripcion(base, evento_id, datos.usuario.dni, session) is not None:
            raise ValueError("El usuario ya tiene una inscripcion para este evento.")
        codigos = {actividad["codigo_actividad"] for actividad in evento["actividades"]}
        if not set(datos.actividades_seleccionadas).issubset(codigos):
            raise ValueError("Alguna actividad seleccionada no pertenece al evento.")
        faltantes = sorted(set(evento.get("conocimientos_requeridos", [])) - set(datos.usuario.conocimientos))
        if faltantes:
            raise ConocimientosFaltantes(faltantes)

        precio = evento["precio_entrada"]
        precio = precio.to_decimal() if isinstance(precio, Decimal128) else Decimal(str(precio))
        importe = Decimal("0.00") if datos.tipo_entrada == "invitacion" else precio
        if importe > 0 and datos.metodo_pago is None:
            raise ValueError("Debe indicar un metodo de pago para una entrada con importe.")
        documento = {
            "evento_id": evento["_id"],
            "evento_resumen": {"titulo": evento["titulo"], "fecha_inicio": evento["fecha_inicio"]},
            "usuario": datos.usuario.model_dump(exclude_none=True),
            "fecha_inscripcion": ahora, "estado_inscripcion": "confirmada",
            "tipo_entrada": datos.tipo_entrada, "importe_abonado": Decimal128(importe),
            "actividades_seleccionadas": datos.actividades_seleccionadas}
        if importe > 0:
            documento["metodo_pago"] = datos.metodo_pago
        if datos.preferencias_alimentarias:
            documento["preferencias_alimentarias"] = datos.preferencias_alimentarias
        identificador = inscripciones.insertar_inscripcion(base, documento, session)
        documento["_id"] = identificador
        return respuesta_inscripcion(documento)

    try:
        return ejecutar_transaccion(base, operacion)
    except DuplicateKeyError as error:
        # Se captura fuera del callback: el error debe abortar tambien el descuento.
        raise ValueError("El usuario ya tiene una inscripcion para este evento.") from error


def cancelar_inscripcion(base, inscripcion_id):
    inscripciones.verificar_indice_usuario(base)

    def operacion(session):
        inscripcion = inscripciones.buscar_inscripcion_por_id(base, inscripcion_id, session)
        if inscripcion is None:
            raise LookupError("La inscripcion no existe.")
        if inscripcion["estado_inscripcion"] == "cancelada":
            return respuesta_inscripcion(inscripcion)
        if inscripcion["estado_inscripcion"] != "confirmada":
            raise ValueError("La inscripcion no esta confirmada.")
        evento = eventos.buscar_evento_por_id(base, str(inscripcion["evento_id"]), session)
        if evento is None:
            raise ValueError("El evento asociado no existe.")
        ahora = datetime.now(timezone.utc)
        if evento["fecha_inicio"] <= ahora:
            raise ValueError("No se puede cancelar una inscripcion una vez iniciado el evento.")
        if not inscripciones.marcar_inscripcion_cancelada(base, inscripcion_id, ahora, session):
            raise ValueError("La inscripcion cambio durante la operacion. Consulte y reintente.")
        if not eventos.restituir_vacante(base, evento["_id"], session):
            raise ValueError("No se pudo restituir la vacante; la cancelacion fue abortada.")
        inscripcion["estado_inscripcion"] = "cancelada"
        inscripcion["fecha_cancelacion"] = ahora
        return respuesta_inscripcion(inscripcion)

    return ejecutar_transaccion(base, operacion)
