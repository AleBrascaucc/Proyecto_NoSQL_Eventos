"""I2: ocupacion de eventos publicados y finalizados; solo lectura de MongoDB."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient, ReadPreference
from pymongo.read_concern import ReadConcern

COLUMNAS = ["evento_id", "evento", "estado_evento", "capacidad_total", "inscripciones_confirmadas", "vacantes_disponibles", "ocupacion_porcentaje"]
ESTADOS = ("publicado", "finalizado")


def porcentaje(numerador, denominador):
    if denominador <= 0:
        return None
    return (Decimal(int(numerador)) * 100 / Decimal(int(denominador))).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)


def pipeline_i2():
    return [
        {"$match": {"estado": {"$in": list(ESTADOS)}}},
        {"$lookup": {
            "from": "inscripciones", "let": {"evento": "$_id"},
            "pipeline": [
                {"$match": {"$expr": {"$eq": ["$evento_id", "$$evento"]}, "estado_inscripcion": "confirmada"}},
                {"$count": "cantidad"},
            ], "as": "conteo"}},
        {"$project": {"_id": 1, "titulo": 1, "estado": 1, "capacidad_total": 1,
                      "vacantes_disponibles": 1,
                      "inscripciones_confirmadas": {"$ifNull": [{"$arrayElemAt": ["$conteo.cantidad", 0]}, 0]}}},
    ]


def construir_tabla(filas):
    registros = []
    for fila in filas:
        capacidad, confirmadas, vacantes = (fila[c] for c in ("capacidad_total", "inscripciones_confirmadas", "vacantes_disponibles"))
        if not all(isinstance(v, int) and not isinstance(v, bool) for v in (capacidad, confirmadas, vacantes)):
            raise ValueError("Capacidad, confirmadas y vacantes deben ser enteros.")
        if capacidad <= 0 or min(confirmadas, vacantes) < 0 or confirmadas + vacantes != capacidad:
            raise ValueError("Cupos inconsistentes. Ejecutar las verificaciones antes del analisis.")
        if fila["estado"] not in ESTADOS:
            raise ValueError("I2 solo admite eventos publicados y finalizados.")
        registros.append({"evento_id": str(fila["_id"]), "evento": fila["titulo"], "estado_evento": fila["estado"],
                          "capacidad_total": capacidad, "inscripciones_confirmadas": confirmadas,
                          "vacantes_disponibles": vacantes, "ocupacion_porcentaje": porcentaje(confirmadas, capacidad)})
    tabla = pd.DataFrame(registros, columns=COLUMNAS)
    if tabla.evento_id.duplicated().any():
        raise ValueError("Eventos repetidos en el resultado.")
    return tabla.sort_values(["ocupacion_porcentaje", "evento", "evento_id"],
                             ascending=[False, True, True], kind="stable").reset_index(drop=True)


def resumir(tabla):
    capacidad = int(tabla.capacidad_total.sum())
    confirmadas = int(tabla.inscripciones_confirmadas.sum())
    if tabla.empty:
        promedio = None
    else:
        suma = sum((Decimal(int(r.inscripciones_confirmadas)) * 100 / Decimal(int(r.capacidad_total))
                    for r in tabla.itertuples()), Decimal(0))
        promedio = (suma / len(tabla)).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    global_ = porcentaje(confirmadas, capacidad)
    return {"eventos_incluidos": len(tabla), "capacidad_incluida": capacidad,
            "confirmadas_en_eventos_incluidos": confirmadas,
            "vacantes_en_eventos_incluidos": int(tabla.vacantes_disponibles.sum()),
            "ocupacion_global_ponderada_porcentaje": str(global_) if global_ is not None else None,
            "promedio_simple_por_evento_porcentaje": str(promedio) if promedio is not None else None}


def obtener_i2(raiz=None):
    raiz = Path(raiz) if raiz else Path(__file__).resolve().parents[1]
    load_dotenv(raiz / ".env")
    uri = os.getenv("MONGO_URI", "mongodb://localhost:27018/?replicaSet=rs0&directConnection=true")
    nombre = os.getenv("MONGO_DB", "gestion_eventos")
    with MongoClient(uri, tz_aware=True, serverSelectionTimeoutMS=5000) as cliente:
        base = cliente[nombre]
        base.command("ping")
        with cliente.start_session() as sesion:
            with sesion.start_transaction(read_concern=ReadConcern("snapshot"), read_preference=ReadPreference.PRIMARY):
                corte = {"fecha_ejecucion_utc": datetime.now(timezone.utc).isoformat(), "base": nombre,
                         "eventos": base.eventos.count_documents({}, session=sesion),
                         "inscripciones": base.inscripciones.count_documents({}, session=sesion),
                         "inscripciones_confirmadas_totales": base.inscripciones.count_documents(
                             {"estado_inscripcion": "confirmada"}, session=sesion)}
                filas = list(base.eventos.aggregate(pipeline_i2(), session=sesion))
    tabla = construir_tabla(filas)
    corte.update(resumir(tabla))
    corte.update({"eventos_excluidos": corte["eventos"] - len(tabla), "estados_incluidos": list(ESTADOS),
                  "unidad": "porcentaje de capacidad por evento",
                  "formula": "100 * inscripciones_confirmadas / capacidad_total",
                  "politica_demo": "base actual; excluir borradores y cancelados por estado, no por titulo"})
    return tabla, corte


def interpretar(tabla, corte):
    lineas = ["# I2. Ocupacion por evento", "", f'Corte UTC: {corte["fecha_ejecucion_utc"]}.',
              f'Base consultada: {corte["eventos"]} eventos y {corte["inscripciones"]} inscripciones.', "",
              f'Se incluyen **{corte["eventos_incluidos"]} eventos publicados o finalizados** y se excluyen '
              f'**{corte["eventos_excluidos"]}** borradores/cancelados.',
              f'En los eventos incluidos hay **{corte["confirmadas_en_eventos_incluidos"]} inscripciones confirmadas** '
              f'sobre **{corte["capacidad_incluida"]} lugares** de capacidad.', ""]
    if not tabla.empty:
        lineas += [f'Ocupacion global ponderada por capacidad: **{corte["ocupacion_global_ponderada_porcentaje"]}%**.',
                   f'Promedio simple de porcentajes por evento: **{corte["promedio_simple_por_evento_porcentaje"]}%**.', "",
                   "No son el mismo calculo: el global divide las sumas; el promedio simple da igual peso a cada evento.", ""]
        for r in tabla.loc[tabla.ocupacion_porcentaje == tabla.ocupacion_porcentaje.max()].itertuples():
            lineas.append(f'- Mayor porcentaje mostrado: **{r.evento}**, {r.ocupacion_porcentaje}% '
                          f'({r.inscripciones_confirmadas}/{r.capacidad_total}).')
    else:
        lineas.append("No hay eventos elegibles; no se calcula un porcentaje global ni un promedio.")
    lineas += ["", "## Interpretacion y limites", "",
               "Cada porcentaje es 100 * confirmadas / capacidad_total. Las inscripciones canceladas no cuentan.",
               "En un evento publicado mide cupo reservado; en uno finalizado describe el registro final, no asistencia efectiva.",
               "El denominador no son las vacantes ni el numero total de inscripciones de la base.",
               "I1 e I2 usan poblaciones distintas: I1 puede incluir confirmadas de eventos cancelados; I2 excluye esos eventos.",
               "No se eliminan registros de demo: sus estados determinan si participan.",
               "Los porcentajes se muestran con dos decimales; las agregaciones se calculan antes de redondear.",
               "La tabla muestra todos los eventos elegibles, incluidos los de ocupacion cero.",
               "El poblado es ficticio: no se generalizan estos porcentajes a una demanda real del mercado.", ""]
    return "\n".join(lineas)


def exportar_i2(tabla, corte, raiz=None):
    raiz = Path(raiz) if raiz else Path(__file__).resolve().parents[1]
    sello = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    destino = raiz / "analisis" / "resultados" / ("I2_" + sello)
    destino.mkdir(parents=True, exist_ok=False)
    tabla.to_csv(destino / "i2_ocupacion.csv", index=False, encoding="utf-8-sig")
    (destino / "corte.json").write_text(json.dumps(corte, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (destino / "i2_interpretacion.md").write_text(interpretar(tabla, corte), encoding="utf-8")
    return destino


def main():
    tabla, corte = obtener_i2()
    destino = exportar_i2(tabla, corte)
    print(tabla.to_string(index=False))
    print("\nCORTE:")
    print(json.dumps(corte, ensure_ascii=False, indent=2))
    print("\nResultados guardados en:", destino)
    print("Solo se realizaron lecturas en MongoDB.")


if __name__ == "__main__":
    main()
