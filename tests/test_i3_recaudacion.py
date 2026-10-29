"""Pruebas de I3 sin conexion a MongoDB."""
import importlib.util
from pathlib import Path
from decimal import Decimal
from unittest.mock import MagicMock, patch
from bson import Decimal128
import pytest

spec=importlib.util.spec_from_file_location("i3_recaudacion",Path(__file__).resolve().parents[1]/"analisis/i3_recaudacion.py")
i3=importlib.util.module_from_spec(spec);spec.loader.exec_module(i3)


def fila(mes="2026-08",importe="234000.00",cantidad=55,canceladas=15):
    return {"_id":mes,"importe_bruto":Decimal128(importe),"cantidad_inscripciones":cantidad,
            "inscripciones_canceladas":canceladas,"importe_canceladas":Decimal128("0.00"),"importes_invalidos":0}


def test_orden_y_mes_cero_con_inscripcion():
    t=i3.construir_tabla([fila("2026-10","555000.00",144,33),fila(),fila("2026-09","0.00",1,0)])
    assert list(t.mes_utc)==["2026-08","2026-09","2026-10"]
    assert t.iloc[1].importe_bruto==Decimal(0) and t.iloc[1].cantidad_inscripciones==1
    assert not t.iloc[1].mes_sin_registros
    assert i3.resumir(t)["importe_bruto_total"]=="789000.00"


def test_rellena_solo_meses_intermedios():
    t=i3.construir_tabla([fila("2026-08"),fila("2026-10")])
    assert len(t)==3 and t.iloc[1].mes_sin_registros and t.iloc[1].cantidad_inscripciones==0


def test_centavos_se_mantienen_decimal():
    t=i3.construir_tabla([fila("2026-08","0.10"),fila("2026-09","0.20")])
    assert i3.resumir(t)["importe_bruto_total"]=="0.30"
    assert all(isinstance(v,Decimal)for v in t.importe_bruto)


@pytest.mark.parametrize("cambio",[{"_id":"2026-13"},{"_id":None},{"importes_invalidos":1},
    {"importe_bruto":234.5},{"importe_bruto":Decimal128("NaN")},{"importe_bruto":Decimal128("-1")},
    {"cantidad_inscripciones":0},{"inscripciones_canceladas":60},{"importe_canceladas":Decimal128("999999")}])
def test_datos_invalidos_fallan(cambio):
    f=fila();f.update(cambio)
    with pytest.raises(ValueError):i3.construir_tabla([f])


def test_mes_repetido_falla():
    with pytest.raises(ValueError):i3.construir_tabla([fila(),fila()])


def test_vacio_sin_divisiones_ni_meses_inventados():
    t=i3.construir_tabla([])
    assert t.empty and i3.resumir(t)["importe_bruto_total"]=="0.00"


def test_pipeline_incluye_todos_los_estados_y_utc():
    p=i3.pipeline_i3()
    assert "$match" not in p[0]
    assert p[0]["$group"]["_id"]["$dateToString"]["timezone"]=="UTC"
    assert not any("$out"in x or "$merge"in x for x in p)


def test_exportacion_sin_sobrescribir(tmp_path):
    t=i3.construir_tabla([fila()]);c=dict(i3.resumir(t),fecha_ejecucion_utc="PRUEBA LOCAL",eventos=20,inscripciones=55)
    a=i3.exportar_i3(t,c,tmp_path);b=i3.exportar_i3(t,c,tmp_path)
    assert a!=b
    assert {p.name for p in a.iterdir()}=={"i3_recaudacion.csv","i3_recaudacion.png","i3_recaudacion.svg","corte.json","i3_interpretacion.md"}
    assert "no representa ganancia"in(a/"i3_interpretacion.md").read_text()


def test_sesion_snapshot_y_conteo_consistente(tmp_path):
    cliente=MagicMock();cliente.__enter__.return_value=cliente
    base=cliente.__getitem__.return_value;sesion=cliente.start_session.return_value.__enter__.return_value
    base.eventos.count_documents.return_value=22;base.inscripciones.count_documents.return_value=55
    base.inscripciones.aggregate.return_value=[fila()]
    with patch.object(i3,"MongoClient",return_value=cliente):t,c=i3.obtener_i3(tmp_path)
    assert c["inscripciones_en_tabla"]==55
    assert base.inscripciones.aggregate.call_args.kwargs["session"]is sesion
    assert sesion.start_transaction.call_args.kwargs["read_concern"].document=={"level":"snapshot"}
    base.inscripciones.insert_one.assert_not_called()
