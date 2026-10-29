"""I1: demanda por actividad. Solo lecturas MongoDB; exportaciones locales.
Ejecutar desde la raiz: python analisis/i1_demanda.py
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient, ReadPreference
from pymongo.read_concern import ReadConcern

COLUMNAS = ["evento_id", "evento", "estado_evento", "codigo_actividad", "actividad", "selecciones_confirmadas"]


def pipeline_i1():
    # Los codigos son locales: agrupar por evento Y codigo.
    return [
        {"$match": {"estado_inscripcion": "confirmada"}},
        {"$unwind": "$actividades_seleccionadas"},
        {"$group": {"_id": {"evento_id": "$evento_id", "codigo": "$actividades_seleccionadas"},
                     "selecciones_confirmadas": {"$sum": 1}}},
        {"$lookup": {"from": "eventos", "localField": "_id.evento_id", "foreignField": "_id", "as": "evento"}},
        {"$unwind": {"path": "$evento", "preserveNullAndEmptyArrays": True}},
        {"$project": {"_id": 1, "selecciones_confirmadas": 1, "titulo": "$evento.titulo",
                      "estado": "$evento.estado", "actividades": "$evento.actividades"}},
    ]


def construir_tabla(filas):
    registros = []
    for fila in filas:
        codigo = fila["_id"]["codigo"]
        actividades = [a for a in fila.get("actividades", []) if a["codigo_actividad"] == codigo]
        if not fila.get("titulo") or len(actividades) != 1:
            raise ValueError("Una seleccion no tiene un evento/actividad valido. Ejecutar las verificaciones.")
        cantidad = fila["selecciones_confirmadas"]
        if not isinstance(cantidad, int) or isinstance(cantidad, bool) or cantidad <= 0:
            raise ValueError("El conteo de selecciones debe ser un entero positivo.")
        registros.append({"evento_id": str(fila["_id"]["evento_id"]), "evento": fila["titulo"],
                          "estado_evento": fila["estado"], "codigo_actividad": codigo,
                          "actividad": actividades[0]["titulo"], "selecciones_confirmadas": cantidad})
    tabla = pd.DataFrame(registros, columns=COLUMNAS)
    if tabla.duplicated(["evento_id", "codigo_actividad"]).any():
        raise ValueError("Hay pares evento/actividad duplicados en el resultado.")
    return tabla.sort_values(["selecciones_confirmadas", "evento", "codigo_actividad", "evento_id"],
                             ascending=[False, True, True, True], kind="stable").reset_index(drop=True)


def obtener_i1(raiz=None):
    raiz = Path(raiz) if raiz else Path(__file__).resolve().parents[1]
    load_dotenv(raiz / ".env")
    uri = os.getenv("MONGO_URI", "mongodb://localhost:27018/?replicaSet=rs0&directConnection=true")
    nombre = os.getenv("MONGO_DB", "gestion_eventos")
    with MongoClient(uri, tz_aware=True, serverSelectionTimeoutMS=5000) as cliente:
        base = cliente[nombre]
        base.command("ping")
        # Una misma instantanea para los conteos y el indicador. No hay escrituras.
        with cliente.start_session() as sesion:
            with sesion.start_transaction(read_concern=ReadConcern("snapshot"), read_preference=ReadPreference.PRIMARY):
                corte = {
                    "fecha_ejecucion_utc": datetime.now(timezone.utc).isoformat(),
                    "base": nombre,
                    "eventos": base.eventos.count_documents({}, session=sesion),
                    "inscripciones": base.inscripciones.count_documents({}, session=sesion),
                    "inscripciones_confirmadas": base.inscripciones.count_documents({"estado_inscripcion": "confirmada"}, session=sesion),
                    "confirmadas_sin_actividad": base.inscripciones.count_documents(
                        {"estado_inscripcion": "confirmada", "actividades_seleccionadas": {"$size": 0}}, session=sesion),
                }
                filas = list(base.inscripciones.aggregate(pipeline_i1(), session=sesion))
    tabla = construir_tabla(filas)
    corte.update({"pares_evento_actividad": len(tabla),
                  "selecciones_confirmadas": int(tabla["selecciones_confirmadas"].sum()),
                  "regla": "estado_inscripcion=confirmada; sin filtro por estado del evento",
                  "unidad": "selecciones por par evento_id/codigo_actividad",
                  "politica_demo": "base actual; sin excluir por titulo ni recargar datos"})
    return tabla, corte


def graficar(tabla, corte, destino):
    destino = Path(destino)
    alto = max(5, len(tabla) * 0.34 + 2.5)
    fig, ax = plt.subplots(figsize=(13, alto))
    if tabla.empty:
        ax.text(0.5, 0.5, "No hay selecciones de actividades en inscripciones confirmadas.",
                ha="center", va="center", transform=ax.transAxes)
        ax.set_axis_off()
    else:
        maximo = tabla["selecciones_confirmadas"].max()
        etiquetas = [f'{r.evento} · {r.codigo_actividad}' for r in tabla.itertuples()]
        colores = ["#087f8c" if n == maximo else "#334b68" for n in tabla["selecciones_confirmadas"]]
        barras = ax.barh(range(len(tabla)), tabla["selecciones_confirmadas"], color=colores, height=0.7)
        ax.set_yticks(range(len(tabla)), etiquetas, fontsize=9)
        ax.invert_yaxis()
        ax.bar_label(barras, padding=4, fontsize=9)
        ax.set_xlim(0, maximo * 1.18)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax.set_xlabel("Selecciones en inscripciones confirmadas")
        ax.set_axisbelow(True)
        ax.grid(axis="x", alpha=0.16)
        for borde in ("top", "right", "left"):
            ax.spines[borde].set_visible(False)
    fig.suptitle("I1 · Demanda por actividad y evento", fontsize=17, fontweight="bold", x=0.04, ha="left")
    fig.text(0.04, 0.02,
             f'Corte UTC: {corte["fecha_ejecucion_utc"]} | Base: {corte["eventos"]} eventos / {corte["inscripciones"]} inscripciones\n'
             'Incluye todos los estados de evento; solo inscripciones confirmadas. Una inscripcion puede elegir varias actividades.',
             fontsize=8, color="#444444")
    fig.tight_layout(rect=(0, 0.065, 1, 0.965))
    try:
        fig.savefig(destino / "i1_demanda.png", dpi=300, bbox_inches="tight", facecolor="white")
        fig.savefig(destino / "i1_demanda.svg", bbox_inches="tight", facecolor="white")
    finally:
        plt.close(fig)


def interpretar(tabla, corte):
    lineas = ["# I1. Demanda por actividad", "",
              f'Corte de ejecucion UTC: {corte["fecha_ejecucion_utc"]}.',
              f'Base consultada: {corte["eventos"]} eventos y {corte["inscripciones"]} inscripciones.', "",
              f'Hay **{corte["inscripciones_confirmadas"]} inscripciones confirmadas**, de las cuales '
              f'**{corte["confirmadas_sin_actividad"]}** no seleccionaron actividades.',
              f'Se registran **{corte["selecciones_confirmadas"]} selecciones** distribuidas en '
              f'**{corte["pares_evento_actividad"]} pares de evento y actividad**.', ""]
    if not tabla.empty:
        mayor = int(tabla["selecciones_confirmadas"].max())
        lideres = tabla.loc[tabla["selecciones_confirmadas"] == mayor]
        lineas.append(f'La mayor demanda observada es de **{mayor} selecciones**:')
        lineas.extend(f'- {r.evento} — {r.codigo_actividad}: {r.actividad}.' for r in lideres.itertuples())
        lineas.append("")
    lineas += ["## Interpretacion y limites", "",
               "La unidad es una seleccion por evento y actividad. No son asistentes efectivos ni personas unicas entre eventos.",
               "Una inscripcion puede elegir varias actividades: la suma de selecciones puede superar el numero de inscriptos que eligieron alguna.",
               "Se agrupa por evento y codigo, porque ACT-01 de un evento no es la misma actividad que ACT-01 de otro.",
               "I1 filtra estado de inscripcion, no estado del evento. Puede incluir demanda historica de un evento cancelado si conserva confirmadas.",
               "Las actividades sin selecciones no aparecen como grupos; el grafico muestra todos los grupos con demanda positiva, sin recortar a un top.",
               "Estos datos ficticios permiten demostrar la tecnica; no justifican inferencias sobre demanda real del mercado.",
               "La inscripcion cancelada de la demo queda excluida por el filtro; los eventos sin inscripciones no aportan selecciones.", ""]
    return "\n".join(lineas)


def exportar_i1(tabla, corte, raiz=None):
    raiz = Path(raiz) if raiz else Path(__file__).resolve().parents[1]
    sello = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    destino = raiz / "analisis" / "resultados" / ("I1_" + sello)
    destino.mkdir(parents=True, exist_ok=False)
    tabla.to_csv(destino / "i1_demanda.csv", index=False, encoding="utf-8-sig")
    (destino / "corte.json").write_text(json.dumps(corte, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (destino / "i1_interpretacion.md").write_text(interpretar(tabla, corte), encoding="utf-8")
    graficar(tabla, corte, destino)
    return destino


def main():
    tabla, corte = obtener_i1()
    destino = exportar_i1(tabla, corte)
    print(tabla.to_string(index=False))
    print("\nCORTE:")
    print(json.dumps(corte, ensure_ascii=False, indent=2))
    print("\nResultados guardados en:", destino)
    print("Solo se realizaron lecturas en MongoDB.")


if __name__ == "__main__":
    main()
