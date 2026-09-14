import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine, get_db
from app.routers import admin, auth, chatbot, formations, horaires, infos
from app.seed import seed_if_empty
from app.services import rag_service

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    try:
        seed_if_empty(db)
        if settings.rag_enabled:
            try:
                n = rag_service.rebuild_index(db)
                logger.info("Index RAG construit : %s passages.", n)
            except Exception as e:
                logger.warning("Index RAG non construit (%s). Le chat utilisera le mode classique.", e)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Plateforme universitaire — API",
    description="Formations, horaires, infos, chatbot (REST).",
    version="1.0.0",
    lifespan=lifespan,
)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(formations.router, prefix="/api")
app.include_router(horaires.router, prefix="/api")
app.include_router(infos.router, prefix="/api")
app.include_router(chatbot.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}
