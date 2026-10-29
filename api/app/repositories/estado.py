def consultar_estado(base):
    base.command("ping")
    return {"conexion": "OK", "base": base.name,
            "eventos": base.eventos.count_documents({}),
            "inscripciones": base.inscripciones.count_documents({})}
