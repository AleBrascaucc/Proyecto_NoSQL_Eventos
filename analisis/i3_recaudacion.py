"""I3: recaudacion bruta registrada por mes UTC; solo lecturas MongoDB."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import pandas as pd
from bson import Decimal128
from dotenv import load_dotenv
from pymongo import MongoClient, ReadPreference
from pymongo.read_concern import ReadConcern

COLUMNAS = ["mes_utc", "importe_bruto", "cantidad_inscripciones", "inscripciones_canceladas", "importe_canceladas", "mes_sin_registros"]


def pipeline_i3():
    # No filtrar estado: incluye canceladas. No convertir strings a dinero.
    return [
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m", "date": "$fecha_inscripcion", "timezone": "UTC"}},
            "importe_bruto": {"$sum": "$importe_abonado"},
            "cantidad_inscripciones": {"$sum": 1},
            "inscripciones_canceladas": {"$sum": {"$cond": [{"$eq": ["$estado_inscripcion", "cancelada"]}, 1, 0]}},
            "importe_canceladas": {"$sum": {"$cond": [{"$eq": ["$estado_inscripcion", "cancelada"]}, "$importe_abonado", 0]}},
            "importes_invalidos": {"$sum": {"$cond": [{"$and": [
                {"$eq": [{"$type": "$importe_abonado"}, "decimal"]},
                {"$gte": ["$importe_abonado", Decimal128("0")]}]}, 0, 1]}},
        }},
        {"$sort": {"_id": 1}},
    ]


def dinero(valor):
    if isinstance(valor, Decimal128):
        valor = valor.to_decimal()
    elif isinstance(valor, int) and not isinstance(valor, bool) and valor == 0:
        valor = Decimal(0)  # $sum del subconjunto cancelado puede devolver cero entero.
    if not isinstance(valor, Decimal) or not valor.is_finite() or valor < 0:
        raise ValueError("Importe no decimal, no finito o negativo. Revisar los datos.")
    return valor


def construir_tabla(filas):
    por_mes = {}
    for f in filas:
        mes = f["_id"]
        try:
            valido = isinstance(mes, str) and len(mes) == 7 and datetime.strptime(mes, "%Y-%m").strftime("%Y-%m") == mes
        except ValueError:
            valido = False
        if not valido or mes in por_mes:
            raise ValueError("Mes invalido o repetido en el resultado.")
        if f.get("importes_invalidos", 0):
            raise ValueError("Hay importes que no son Decimal128 no negativos; no se informa una suma parcial.")
        cantidad, canceladas = f["cantidad_inscripciones"], f["inscripciones_canceladas"]
        if not all(isinstance(v, int) and not isinstance(v, bool) for v in (cantidad, canceladas)) or cantidad <= 0 or not 0 <= canceladas <= cantidad:
            raise ValueError("Conteos mensuales inconsistentes.")
        bruto, importe_canceladas = dinero(f["importe_bruto"]), dinero(f["importe_canceladas"])
        if importe_canceladas > bruto:
            raise ValueError("El importe cancelado no puede superar al bruto registrado.")
        por_mes[mes] = {"mes_utc": mes, "importe_bruto": bruto, "cantidad_inscripciones": cantidad,
                       "inscripciones_canceladas": canceladas, "importe_canceladas": importe_canceladas, "mes_sin_registros": False}
    if not por_mes:
        return pd.DataFrame(columns=COLUMNAS)
    meses = pd.period_range(min(por_mes), max(por_mes), freq="M")
    registros = [por_mes.get(str(m), {"mes_utc": str(m), "importe_bruto": Decimal(0), "cantidad_inscripciones": 0,
                  "inscripciones_canceladas": 0, "importe_canceladas": Decimal(0), "mes_sin_registros": True}) for m in meses]
    return pd.DataFrame(registros, columns=COLUMNAS)


def resumir(tabla):
    total = sum(tabla.importe_bruto, Decimal(0))
    cancelado = sum(tabla.importe_canceladas, Decimal(0))
    return {"meses_mostrados": len(tabla), "meses_sin_registros_rellenados": int(tabla.mes_sin_registros.sum()) if not tabla.empty else 0,
            "inscripciones_en_tabla": int(tabla.cantidad_inscripciones.sum()),
            "inscripciones_canceladas_en_tabla": int(tabla.inscripciones_canceladas.sum()),
            "importe_bruto_total": format(total, ".2f"), "importe_registrado_canceladas": format(cancelado, ".2f")}


def obtener_i3(raiz=None):
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
                         "inscripciones": base.inscripciones.count_documents({}, session=sesion)}
                filas = list(base.inscripciones.aggregate(pipeline_i3(), session=sesion))
    tabla = construir_tabla(filas)
    corte.update(resumir(tabla))
    if corte["inscripciones_en_tabla"] != corte["inscripciones"]:
        raise ValueError("El conteo mensual no coincide con el total de inscripciones.")
    corte.update({"unidad": "importe monetario registrado, sin conversion de moneda",
                  "regla": "sumar importe_abonado por mes UTC de fecha_inscripcion; incluir todos los estados",
                  "politica_demo": "base actual, sin excluir por titulo ni recargar datos",
                  "meses_vacios": "rellenar con cero solo entre el primer y ultimo mes observados"})
    return tabla, corte


def graficar(tabla, corte, destino):
    fig, ax = plt.subplots(figsize=(10, 5.5))
    if tabla.empty:
        ax.text(0.5, 0.5, "No hay inscripciones registradas.", ha="center", va="center", transform=ax.transAxes)
        ax.set_axis_off()
    else:
        x = list(range(len(tabla)))
        # Unica conversion a float: representacion visual, no calculos monetarios.
        y = [float(v) for v in tabla.importe_bruto]
        ax.plot(x, y, color="#087f8c", marker="o", linewidth=2.5, markersize=7)
        ax.set_xticks(x, tabla.mes_utc)
        ax.set_xlabel("Mes UTC de inscripcion")
        ax.set_ylabel("Importe bruto registrado (unidades monetarias)")
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}".replace(",", ".")))
        ax.set_ylim(0, max(max(y) * 1.22, 1))
        ax.set_axisbelow(True)
        ax.grid(axis="y", alpha=0.2)
        for j, importe in enumerate(tabla.importe_bruto):
            etiqueta = f"{importe:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            ax.annotate(etiqueta, (j, y[j]), xytext=(0, 10), textcoords="offset points", ha="center", fontsize=10)
        for borde in ("top", "right"):
            ax.spines[borde].set_visible(False)
    fig.suptitle("I3 · Recaudación bruta registrada por mes", fontsize=16, fontweight="bold", x=0.04, ha="left")
    fig.text(0.04, 0.02,
             f'Corte UTC: {corte["fecha_ejecucion_utc"]} | Base: {corte["eventos"]} eventos / {corte["inscripciones"]} inscripciones\n'
             'Incluye inscripciones canceladas. No descuenta devoluciones ni representa ingreso neto. No es una proyección.',
             fontsize=8, color="#444444")
    fig.tight_layout(rect=(0, 0.1, 1, 0.94))
    try:
        fig.savefig(Path(destino) / "i3_recaudacion.png", dpi=300, bbox_inches="tight", facecolor="white")
        fig.savefig(Path(destino) / "i3_recaudacion.svg", bbox_inches="tight", facecolor="white")
    finally:
        plt.close(fig)


def interpretar(tabla, corte):
    lineas = ["# I3. Recaudacion bruta registrada por mes", "", f'Corte UTC: {corte["fecha_ejecucion_utc"]}.',
              f'Base: {corte["eventos"]} eventos y {corte["inscripciones"]} inscripciones.', "",
              f'Importe bruto registrado: **{corte["importe_bruto_total"]}** en **{corte["meses_mostrados"]} meses mostrados.',
              f'Incluye **{corte["inscripciones_canceladas_en_tabla"]} inscripciones canceladas**, que registran '
              f'**{corte["importe_registrado_canceladas"]}**. No se restan estos importes.', ""]
    if not tabla.empty:
        maximo = max(tabla.importe_bruto)
        meses = ", ".join(tabla.loc[tabla.importe_bruto == maximo, "mes_utc"])
        lineas.append(f'El mayor importe mensual corresponde a **{meses}**, con **{maximo:.2f}**.')
        for r in tabla.itertuples():
            lineas.append(f'- {r.mes_utc}: {r.importe_bruto:.2f}; {r.cantidad_inscripciones} inscripciones '
                          f'({r.inscripciones_canceladas} canceladas).')
    else:
        lineas.append("No hay registros para analizar.")
    lineas += ["", "## Interpretacion y limites", "",
               "Se agrupa por fecha de inscripcion, no por fecha del evento. La zona horaria es UTC.",
               "Es recaudacion bruta registrada: no se deducen devoluciones, comisiones, impuestos o costos; no representa ganancia ni ingreso neto.",
               "Un mes con importe cero puede contener inscripciones gratuitas o invitaciones; no implica necesariamente ausencia de inscripciones.",
               "Solo se rellenan meses intermedios sin registros con cero, identificados en la tabla; no se agregan meses externos al periodo observado.",
               "El grafico conecta totales mensuales observados: no estima valores diarios ni proyecta periodos futuros.",
               "Las diferencias del poblado ficticio dependen de las fechas, precios e invitaciones generados; no se interpretan como tendencia del mercado.",
               "La demo gratuita y cancelada se incluye en el conteo mensual, aunque su importe es cero.", ""]
    return "\n".join(lineas)


def exportar_i3(tabla, corte, raiz=None):
    raiz = Path(raiz) if raiz else Path(__file__).resolve().parents[1]
    destino = raiz / "analisis" / "resultados" / ("I3_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ"))
    destino.mkdir(parents=True, exist_ok=False)
    tabla.to_csv(destino / "i3_recaudacion.csv", index=False, encoding="utf-8-sig")
    (destino / "corte.json").write_text(json.dumps(corte, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (destino / "i3_interpretacion.md").write_text(interpretar(tabla, corte), encoding="utf-8")
    graficar(tabla, corte, destino)
    return destino


def main():
    tabla, corte = obtener_i3()
    destino = exportar_i3(tabla, corte)
    print(tabla.to_string(index=False))
    print("\nCORTE:")
    print(json.dumps(corte, ensure_ascii=False, indent=2))
    print("\nResultados guardados en:", destino)
    print("Solo se realizaron lecturas en MongoDB.")


if __name__ == "__main__":
    main()
