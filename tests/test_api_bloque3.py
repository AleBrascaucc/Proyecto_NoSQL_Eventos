"""Pruebas sin conexion a MongoDB. El doble transaccional prueba la orquestacion,
no reemplaza la verificacion de atomicidad/concurrencia con un replica set real.
Ejecutar desde api/: python -m pytest ../tests/test_api_bloque3.py -q
"""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from bson import ObjectId, Decimal128
from fastapi.testclient import TestClient
from pydantic import ValidationError
from pymongo.errors import DuplicateKeyError, OperationFailure
from app import db
from app.main import app
from app.routes import http
from app.schemas.modelos import EventoCrear, EventoActualizar, FiltrosEventos, InscripcionCrear
from app.services import servicio_inscripciones as servicio
from app.services import servicio_eventos
from app.repositories import repositorio_inscripciones as inscripciones
from app.repositories import repositorio_eventos as eventos


def entrada(**cambios):
    datos = {"usuario": {"dni": "44555666", "nombre_completo": "Prueba", "email": "prueba@example.com", "conocimientos": [" SQL ", "MongoDB"]},
             "actividades_seleccionadas": ["ACT-01"], "metodo_pago": "efectivo"}
    datos.update(cambios)
    return datos


def evento_nuevo(**cambios):
    inicio = datetime.now(timezone.utc) + timedelta(days=30)
    fin = inicio + timedelta(hours=2)
    datos = {"titulo": "Demo", "categoria": "tecnologia", "fecha_inicio": inicio, "fecha_fin": fin,
             "precio_entrada": "100.00", "capacidad_total": 10,
             "sede": {"nombre": "Sala", "direccion": "Calle 1", "ciudad": "Cordoba", "capacidad_maxima": 10},
             "actividades": [{"tipo": "taller", "codigo_actividad": "ACT-01", "titulo": "Taller", "orador": "Ana", "sala": "A", "inicio": inicio, "fin": fin}],
             "conocimientos_requeridos": [" SQL ", "sql", "MongoDB"]}
    datos.update(cambios)
    return datos


@pytest.fixture
def escenario(monkeypatch):
    e = {"_id": ObjectId(), "titulo": "Demo", "fecha_inicio": datetime.now(timezone.utc) + timedelta(days=30),
         "estado": "publicado", "capacidad_total": 2, "vacantes_disponibles": 2,
         "precio_entrada": Decimal128("100.00"), "actividades": [{"codigo_actividad": "ACT-01"}],
         "conocimientos_requeridos": ["sql", "mongodb"]}
    estado = {"evento": e, "inscripciones": {}, "visitas": []}
    session = object()

    def usar(s):
        assert s is session

    def transaccion(base, callback):
        assert base is estado
        previo = deepcopy(estado)
        try:
            return callback(session)
        except Exception:
            estado.clear()
            estado.update(previo)
            raise

    def reservar(base, eid, ahora, s):
        usar(s)
        base["visitas"].append("reservar")
        evento = base["evento"]
        if evento and str(evento["_id"]) == eid and evento["estado"] == "publicado" and evento["fecha_inicio"] > ahora and evento["vacantes_disponibles"] > 0:
            evento["vacantes_disponibles"] -= 1
            return deepcopy(evento)
        return None

    def buscar_evento(base, eid, s):
        usar(s)
        return deepcopy(base["evento"]) if base["evento"] and str(base["evento"]["_id"]) == eid else None

    def buscar(base, eid, dni, s):
        usar(s)
        return next((deepcopy(i) for i in base["inscripciones"].values() if str(i["evento_id"]) == eid and i["usuario"]["dni"] == dni), None)

    def insertar(base, documento, s):
        usar(s)
        if buscar(base, str(documento["evento_id"]), documento["usuario"]["dni"], s):
            raise DuplicateKeyError("duplicado")
        identificador = ObjectId()
        base["inscripciones"][str(identificador)] = dict(deepcopy(documento), _id=identificador)
        return identificador

    def buscar_id(base, iid, s):
        usar(s)
        return deepcopy(base["inscripciones"].get(iid))

    def cancelar(base, iid, ahora, s):
        usar(s)
        inscripcion = base["inscripciones"][iid]
        if inscripcion["estado_inscripcion"] != "confirmada":
            return False
        inscripcion.update(estado_inscripcion="cancelada", fecha_cancelacion=ahora)
        return True

    def restituir(base, eid, s):
        usar(s)
        evento = base["evento"]
        if evento["vacantes_disponibles"] >= evento["capacidad_total"]:
            return False
        evento["vacantes_disponibles"] += 1
        return True

    monkeypatch.setattr(servicio, "ejecutar_transaccion", transaccion)
    monkeypatch.setattr(inscripciones, "verificar_indice_usuario", lambda base: None)
    monkeypatch.setattr(eventos, "reservar_vacante", reservar)
    monkeypatch.setattr(eventos, "buscar_evento_por_id", buscar_evento)
    monkeypatch.setattr(eventos, "restituir_vacante", restituir)
    monkeypatch.setattr(inscripciones, "buscar_inscripcion", buscar)
    monkeypatch.setattr(inscripciones, "insertar_inscripcion", insertar)
    monkeypatch.setattr(inscripciones, "buscar_inscripcion_por_id", buscar_id)
    monkeypatch.setattr(inscripciones, "marcar_inscripcion_cancelada", cancelar)
    return estado, str(e["_id"])


def test_normalizacion_y_modelo():
    datos = entrada()
    datos["usuario"]["conocimientos"] = [" SQL ", "sql", "MongoDB"]
    usuario = InscripcionCrear.model_validate(datos).usuario
    assert usuario.conocimientos == ["sql", "mongodb"]
    assert "participante" not in InscripcionCrear.model_fields
    assert "telefono" not in type(usuario).model_fields
    assert EventoCrear.model_validate(evento_nuevo()).conocimientos_requeridos == ["sql", "mongodb"]
    assert EventoActualizar(conocimientos_requeridos=[]).conocimientos_requeridos == []
    assert FiltrosEventos(conocimiento=" SQL ").conocimiento == "sql"


@pytest.mark.parametrize("valores", [["   "], [42], None, "sql"])
def test_conocimientos_invalidos(valores):
    datos = entrada()
    datos["usuario"]["conocimientos"] = valores
    with pytest.raises(ValidationError):
        InscripcionCrear.model_validate(datos)


def test_rechaza_campo_anterior():
    datos = entrada()
    datos["participante"] = datos.pop("usuario")
    with pytest.raises(ValidationError):
        InscripcionCrear.model_validate(datos)


@pytest.mark.parametrize("cambios", [{"capacidad_total": 11}, {"fecha_fin": datetime.now(timezone.utc)}, {"actividades": []}])
def test_preserva_validaciones_eventos(cambios):
    with pytest.raises(ValidationError):
        EventoCrear.model_validate(evento_nuevo(**cambios))


def test_inscripcion_valida(escenario):
    base, eid = escenario
    resultado = servicio.confirmar_inscripcion(base, eid, InscripcionCrear.model_validate(entrada()))
    assert base["evento"]["vacantes_disponibles"] == 1
    assert len(base["inscripciones"]) == 1
    assert resultado["usuario"]["conocimientos"] == ["sql", "mongodb"]
    assert resultado["importe_abonado"].to_decimal() == 100
    assert "participante" not in resultado
    assert base["visitas"] == ["reservar"]


def test_requisitos_faltantes_aborta(escenario):
    base, eid = escenario
    datos = entrada()
    datos["usuario"]["conocimientos"] = ["sql"]
    with pytest.raises(servicio.ConocimientosFaltantes) as error:
        servicio.confirmar_inscripcion(base, eid, InscripcionCrear.model_validate(datos))
    assert error.value.detail["conocimientos_faltantes"] == ["mongodb"]
    assert base["evento"]["vacantes_disponibles"] == 2
    assert not base["inscripciones"]


def test_evento_sin_requisitos(escenario):
    base, eid = escenario
    base["evento"]["conocimientos_requeridos"] = []
    datos = entrada()
    datos["usuario"]["conocimientos"] = []
    servicio.confirmar_inscripcion(base, eid, InscripcionCrear.model_validate(datos))
    assert base["evento"]["vacantes_disponibles"] == 1


@pytest.mark.parametrize("cambios", [{"actividades_seleccionadas": ["NO-EXISTE"]}, {"metodo_pago": None}])
def test_error_despues_de_reservar_aborta(escenario, cambios):
    base, eid = escenario
    with pytest.raises(ValueError):
        servicio.confirmar_inscripcion(base, eid, InscripcionCrear.model_validate(entrada(**cambios)))
    assert base["evento"]["vacantes_disponibles"] == 2
    assert not base["inscripciones"]


def test_duplicado_no_descuenta(escenario):
    base, eid = escenario
    datos = InscripcionCrear.model_validate(entrada())
    servicio.confirmar_inscripcion(base, eid, datos)
    with pytest.raises(ValueError, match="ya tiene"):
        servicio.confirmar_inscripcion(base, eid, datos)
    assert base["evento"]["vacantes_disponibles"] == 1
    assert len(base["inscripciones"]) == 1


def test_error_indice_unico_aborta(escenario, monkeypatch):
    base, eid = escenario
    def fallo(*args):
        raise DuplicateKeyError("duplicado concurrente simulado")
    monkeypatch.setattr(inscripciones, "insertar_inscripcion", fallo)
    with pytest.raises(ValueError, match="ya tiene"):
        servicio.confirmar_inscripcion(base, eid, InscripcionCrear.model_validate(entrada()))
    assert base["evento"]["vacantes_disponibles"] == 2
    assert not base["inscripciones"]


@pytest.mark.parametrize("campo,valor", [("estado", "cancelado"), ("vacantes_disponibles", 0), ("fecha_inicio", datetime.now(timezone.utc)-timedelta(days=1))])
def test_reserva_rechazada(escenario, campo, valor):
    base, eid = escenario
    base["evento"][campo] = valor
    anterior = base["evento"]["vacantes_disponibles"]
    with pytest.raises(ValueError):
        servicio.confirmar_inscripcion(base, eid, InscripcionCrear.model_validate(entrada()))
    assert base["evento"]["vacantes_disponibles"] == anterior


def test_evento_inexistente(escenario):
    base, _ = escenario
    with pytest.raises(LookupError):
        servicio.confirmar_inscripcion(base, str(ObjectId()), InscripcionCrear.model_validate(entrada()))


def test_cancelacion_repetida(escenario):
    base, eid = escenario
    original = servicio.confirmar_inscripcion(base, eid, InscripcionCrear.model_validate(entrada()))
    primera = servicio.cancelar_inscripcion(base, original["id"])
    segunda = servicio.cancelar_inscripcion(base, original["id"])
    assert primera == segunda
    assert base["evento"]["vacantes_disponibles"] == 2


def test_fallo_restitucion_aborta_cancelacion(escenario, monkeypatch):
    base, eid = escenario
    original = servicio.confirmar_inscripcion(base, eid, InscripcionCrear.model_validate(entrada()))
    monkeypatch.setattr(eventos, "restituir_vacante", lambda *args: False)
    with pytest.raises(ValueError, match="abortada"):
        servicio.cancelar_inscripcion(base, original["id"])
    assert base["inscripciones"][original["id"]]["estado_inscripcion"] == "confirmada"
    assert base["evento"]["vacantes_disponibles"] == 1


def test_protege_requisitos_de_confirmadas(monkeypatch):
    base = object()
    session = object()
    actual = {"_id": ObjectId(), "estado": "publicado", "capacidad_total": 2, "vacantes_disponibles": 1}
    monkeypatch.setattr(servicio_eventos, "buscar_evento_por_id", lambda *args, **kw: actual)
    monkeypatch.setattr(servicio_eventos, "ejecutar_transaccion", lambda b, fn: fn(session))
    monkeypatch.setattr(servicio_eventos, "hay_confirmadas_sin_conocimientos", lambda *args: True)
    with pytest.raises(ValueError, match="nuevos requisitos"):
        servicio_eventos.modificar_evento(base, str(actual["_id"]), EventoActualizar(conocimientos_requeridos=["docker"]))


def test_sesion_y_opciones_transaccion():
    session = Mock()
    session.__enter__ = Mock(return_value=session)
    session.__exit__ = Mock(return_value=False)
    session.with_transaction.return_value = "OK"
    base = Mock()
    base.client.start_session.return_value = session
    callback = lambda s: None
    assert db.ejecutar_transaccion(base, callback) == "OK"
    args, kw = session.with_transaction.call_args
    assert args == (callback,)
    assert kw["read_concern"].document == {"level": "snapshot"}
    assert kw["write_concern"].document == {"w": "majority"}


def test_contrato_repositorio_reserva():
    base = Mock()
    session = object()
    ahora = datetime.now(timezone.utc)
    eid = str(ObjectId())
    eventos.reservar_vacante(base, eid, ahora, session)
    args, kw = base.eventos.find_one_and_update.call_args
    assert args[0] == {"_id": ObjectId(eid), "estado": "publicado", "fecha_inicio": {"$gt": ahora}, "vacantes_disponibles": {"$gt": 0}}
    assert args[1] == {"$inc": {"vacantes_disponibles": -1}}
    assert kw["session"] is session
    assert kw["return_document"] is True


@pytest.mark.parametrize("indice,acepta", [
    ({"name": "evento_usuario_dni_unico", "key": {"evento_id": 1, "usuario.dni": 1}, "unique": True}, True),
    ({"name": "viejo", "key": {"evento_id": 1, "participante.dni": 1}, "unique": True}, False),
    ({"name": "evento_usuario_dni_unico", "key": {"evento_id": 1, "usuario.dni": 1}, "unique": False}, False)])
def test_guardia_indice(indice, acepta):
    base = Mock()
    base.inscripciones.list_indexes.return_value = [indice]
    if acepta:
        inscripciones.verificar_indice_usuario(base)
    else:
        with pytest.raises(OperationFailure):
            inscripciones.verificar_indice_usuario(base)


def test_http_conocimiento_faltante(escenario):
    base, eid = escenario
    app.state.base = base
    datos = entrada()
    datos["usuario"]["conocimientos"] = ["sql"]
    respuesta = TestClient(app).post(f"/eventos/{eid}/inscripciones", json=datos)
    assert respuesta.status_code == 409
    assert respuesta.json()["detail"]["conocimientos_faltantes"] == ["mongodb"]
    assert base["evento"]["vacantes_disponibles"] == 2


def test_http_201_y_cancelacion_repetida(escenario):
    base, eid = escenario
    app.state.base = base
    cliente = TestClient(app)
    respuesta = cliente.post(f"/eventos/{eid}/inscripciones", json=entrada())
    assert respuesta.status_code == 201
    ruta = f'/inscripciones/{respuesta.json()["id"]}/cancelacion'
    assert cliente.patch(ruta).status_code == 200
    assert cliente.patch(ruta).status_code == 200
    assert base["evento"]["vacantes_disponibles"] == 2


@pytest.mark.parametrize("ruta", ["/eventos/no-es-id", "/eventos?precio_minimo=8000&precio_maximo=4000"])
def test_http_422(ruta):
    assert TestClient(app).get(ruta).status_code == 422


def test_http_404(escenario):
    base, _ = escenario
    app.state.base = base
    respuesta = TestClient(app).post(f"/eventos/{ObjectId()}/inscripciones", json=entrada())
    assert respuesta.status_code == 404


def test_http_filtro_conocimiento_normalizado(monkeypatch):
    recibido = []
    monkeypatch.setattr(http, "listar_eventos", lambda base, filtros: recibido.append(filtros.conocimiento) or [])
    assert TestClient(app).get("/eventos", params={"conocimiento": " SQL "}).status_code == 200
    assert recibido == ["sql"]


def test_routes_sin_acceso_a_repositorios():
    import ast
    from pathlib import Path
    arbol = ast.parse(Path(http.__file__).read_text())
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.ImportFrom):
            assert "repositories" not in (nodo.module or "")
        if isinstance(nodo, ast.Attribute):
            assert nodo.attr not in {"find_one", "find", "insert_one", "update_one", "find_one_and_update", "delete_one", "command", "count_documents"}
