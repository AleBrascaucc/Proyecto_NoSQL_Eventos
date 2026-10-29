from fastapi import FastAPI
from app.db import lifespan
from app.routes.http import router

app = FastAPI(title="API de Gestion de Eventos", version="2.0.0", lifespan=lifespan)
app.include_router(router)
