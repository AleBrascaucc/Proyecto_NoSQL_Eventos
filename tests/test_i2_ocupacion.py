"""Pruebas locales de I2; no conectan a MongoDB."""
import importlib.util
from pathlib import Path
from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest

spec=importlib.util.spec_from_file_location("i2_ocupacion",Path(__file__).resolve().parents[1]/"analisis/i2_ocupacion.py")
i2=importlib.util.module_from_spec(spec);spec.loader.exec_module(i2)


def fila(eid="a",capacidad=10,confirmadas=4,estado="publicado"):
    return {"_id":eid,"titulo":"Evento "+eid,"estado":estado,"capacidad_total":capacidad,
            "inscripciones_confirmadas":confirmadas,"vacantes_disponibles":capacidad-confirmadas}


def test_porcentaje_y_orden():
    t=i2.construir_tabla([fila(),fila("b",10,10)])
    assert list(t.ocupacion_porcentaje)==[Decimal("100.00"),Decimal("40.00")]
    assert t.iloc[0].evento_id=="b"


def test_promedio_simple_no_es_global():
    t=i2.construir_tabla([fila("a",10,10),fila("b",90,0)])
    r=i2.resumir(t)
    assert r["ocupacion_global_ponderada_porcentaje"]=="10.00"
    assert r["promedio_simple_por_evento_porcentaje"]=="50.00"


def test_cero_confirmadas_incluido():
    assert i2.construir_tabla([fila(confirmadas=0)]).iloc[0].ocupacion_porcentaje==Decimal("0.00")


@pytest.mark.parametrize("cambio",[
    {"capacidad_total":0},{"vacantes_disponibles":8},{"inscripciones_confirmadas":-1},
    {"capacidad_total":10.5},{"vacantes_disponibles":True},{"estado":"cancelado"},{"estado":"borrador"}])
def test_inconsistencias_y_estados_excluidos_fallan(cambio):
    f=fila();f.update(cambio)
    with pytest.raises(ValueError):i2.construir_tabla([f])


def test_eventos_duplicados_fallan():
    with pytest.raises(ValueError):i2.construir_tabla([fila(),fila()])


def test_sin_eventos_no_divide_por_cero():
    t=i2.construir_tabla([]);r=i2.resumir(t)
    assert t.empty and r["eventos_incluidos"]==0
    assert r["ocupacion_global_ponderada_porcentaje"] is None
    assert r["promedio_simple_por_evento_porcentaje"] is None


def test_redondeo_half_even():
    assert i2.porcentaje(9,32)==Decimal("28.12")


def test_pipeline_solo_elegibles_y_confirmadas():
    p=i2.pipeline_i2()
    assert p[0]=={"$match":{"estado":{"$in":["publicado","finalizado"]}}}
    assert p[1]["$lookup"]["pipeline"][0]["$match"]["estado_inscripcion"]=="confirmada"
    assert not any("$out"in x or "$merge"in x for x in p)


def test_exportaciones_no_sobrescriben(tmp_path):
    t=i2.construir_tabla([fila()]);c=dict(i2.resumir(t),fecha_ejecucion_utc="PRUEBA LOCAL",eventos=1,inscripciones=4,eventos_excluidos=0)
    a=i2.exportar_i2(t,c,tmp_path);b=i2.exportar_i2(t,c,tmp_path)
    assert a!=b
    assert {p.name for p in a.iterdir()}=={"i2_ocupacion.csv","i2_interpretacion.md","corte.json"}
    assert "40.00%"in(a/"i2_interpretacion.md").read_text()


def test_lecturas_con_sesion_snapshot(tmp_path):
    cliente=MagicMock();cliente.__enter__.return_value=cliente
    sesion=cliente.start_session.return_value.__enter__.return_value
    base=cliente.__getitem__.return_value
    base.eventos.count_documents.return_value=22
    base.inscripciones.count_documents.side_effect=[201,152]
    base.eventos.aggregate.return_value=[fila()]
    with patch.object(i2,"MongoClient",return_value=cliente):
        t,c=i2.obtener_i2(tmp_path)
    assert c["eventos"]==22 and c["eventos_incluidos"]==1 and c["eventos_excluidos"]==21
    assert base.eventos.aggregate.call_args.kwargs["session"] is sesion
    assert sesion.start_transaction.call_args.kwargs["read_concern"].document=={"level":"snapshot"}
    for llamada in base.inscripciones.count_documents.call_args_list:assert llamada.kwargs["session"]is sesion
    base.eventos.update_one.assert_not_called();base.inscripciones.insert_one.assert_not_called()
