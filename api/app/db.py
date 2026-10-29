"""Conexion y sesiones. Las colecciones se consultan solo en repositories/."""
import os
from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient, ReadPreference
from pymongo.read_concern import ReadConcern
from pymongo.write_concern import WriteConcern

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

@asynccontextmanager
async def lifespan(app):
    uri, nombre = os.getenv("MONGO_URI"), os.getenv("MONGO_DB")
    if not uri or not nombre:
        raise RuntimeError("Falta configurar MONGO_URI o MONGO_DB.")
    cliente = MongoClient(uri, serverSelectionTimeoutMS=5000, tz_aware=True)
    app.state.base = cliente[nombre]
    try:
        yield
    finally:
        cliente.close()


def ejecutar_transaccion(base, operacion):
    # with_transaction aborta ante excepciones y reintenta errores transitorios.
    # El callback no debe producir efectos externos (archivos, correos, etc.).
    with base.client.start_session() as session:
        return session.with_transaction(
            operacion, read_concern=ReadConcern("snapshot"),
            write_concern=WriteConcern("majority"), read_preference=ReadPreference.PRIMARY)
