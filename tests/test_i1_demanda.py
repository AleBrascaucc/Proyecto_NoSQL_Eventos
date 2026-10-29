"""Pruebas de tabla, interpretacion y exportacion; no conectan con MongoDB."""
import importlib.util
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
import pytest

spec = importlib.util.spec_from_file_location("i1_demanda", Path(__file__).resolve().parents[1] / "analisis/i1_demanda.py")
i1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(i1)


def fila(eid="a", codigo="ACT-01", cantidad=4, titulo="Evento A"):
    return {"_id": {"evento_id": eid, "codigo": codigo}, "selecciones_confirmadas": cantidad,
            "titulo": titulo, "estado": "publicado", "actividades": [{"codigo_actividad": codigo, "titulo": "Actividad"}]}


def corte():
    return {"fecha_ejecucion_utc": datetime.now(timezone.utc).isoformat(), "base": "prueba",
            "eventos": 2, "inscripciones": 7, "inscripciones_confirmadas": 6, "confirmadas_sin_actividad": 1,
            "pares_evento_actividad": 2, "selecciones_confirmadas": 7}


def test_no_mezcla_codigos_de_distintos_eventos():
    t=i1.construir_tabla([fila(), fila(eid="b", cantidad=3, titulo="Evento B")])
    assert len(t)==2 and int(t.selecciones_confirmadas.sum())==7


def test_ordena_y_conserva_titulos():
    t=i1.construir_tabla([fila(cantidad=2),fila(eid="b",cantidad=8,titulo="Evento B")])
    assert t.iloc[0].evento_id=="b"
    assert t.iloc[0].selecciones_confirmadas==8


def test_grupo_duplicado_falla():
    with pytest.raises(ValueError):i1.construir_tabla([fila(),fila()])


@pytest.mark.parametrize("cambio", [{"titulo":None},{"actividades":[]},{"selecciones_confirmadas":0},{"selecciones_confirmadas":1.5}])
def test_datos_invalidos_fallan(cambio):
    f=fila();f.update(cambio)
    with pytest.raises(ValueError):i1.construir_tabla([f])


def test_vacio_conserva_columnas():
    t=i1.construir_tabla([])
    assert t.empty and list(t.columns)==i1.COLUMNAS


def test_pipeline_agrupa_por_evento_y_codigo_sin_escrituras():
    p=i1.pipeline_i1()
    assert p[0]=={"$match":{"estado_inscripcion":"confirmada"}}
    assert p[2]["$group"]["_id"]=={"evento_id":"$evento_id","codigo":"$actividades_seleccionadas"}
    assert not any("$out" in e or "$merge" in e for e in p)


def test_interpretacion_incluye_unidad_y_corte():
    t=i1.construir_tabla([fila(),fila(eid="b",cantidad=3,titulo="Evento B")])
    texto=i1.interpretar(t,corte())
    assert "**7 selecciones**" in texto and "**2 pares" in texto
    assert "personas unicas" in texto and "estado del evento" in texto


def test_exportacion_no_sobrescribe_ejecuciones(tmp_path):
    t=i1.construir_tabla([fila(),fila(eid="b",cantidad=3,titulo="Evento B")])
    a=i1.exportar_i1(t,corte(),tmp_path);b=i1.exportar_i1(t,corte(),tmp_path)
    assert a!=b
    assert {p.name for p in a.iterdir()}=={"i1_demanda.csv","i1_demanda.png","i1_demanda.svg","corte.json","i1_interpretacion.md"}
    assert (a/"i1_demanda.png").stat().st_size>1000


def test_lecturas_comparten_sesion_y_snapshot(tmp_path):
    cliente=MagicMock();cliente.__enter__.return_value=cliente
    sesion=cliente.start_session.return_value.__enter__.return_value
    base=cliente.__getitem__.return_value
    base.eventos.count_documents.return_value=22
    base.inscripciones.count_documents.side_effect=[201,152,52]
    base.inscripciones.aggregate.return_value=[fila()]
    with patch.object(i1,"MongoClient",return_value=cliente):
        tabla,c=i1.obtener_i1(tmp_path)
    assert c["eventos"]==22 and c["inscripciones"]==201
    assert c["selecciones_confirmadas"]==4
    assert sesion.start_transaction.call_args.kwargs["read_concern"].document=={"level":"snapshot"}
    for llamada in base.inscripciones.count_documents.call_args_list:
        assert llamada.kwargs["session"] is sesion
    assert base.inscripciones.aggregate.call_args.kwargs["session"] is sesion
    base.inscripciones.insert_one.assert_not_called()
    base.eventos.update_one.assert_not_called()
