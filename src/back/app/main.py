from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect

from app.core.logging import configure_logging, get_logger
from app.routers import analysis, auth, metrics, processes
from app.db.base import Base
from app.db.session import engine
import app.db.models  # noqa

configure_logging()
logger = get_logger(__name__)

# Inicializar Banco de Dados
try:
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    logger.info("Banco de dados pronto. Tabelas: %s", inspector.get_table_names())
except Exception as e:
    logger.error("Erro ao criar tabelas: %s", str(e))

app = FastAPI(title="EanterOS API", version="0.1.0", docs_url="/docs", redoc_url="/redoc")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(processes.router)
app.include_router(analysis.router)
app.include_router(metrics.router)


@app.get("/health", tags=["infra"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
