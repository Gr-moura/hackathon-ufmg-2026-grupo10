"""
Fixtures compartilhadas para a suíte de integração do EnterOS.

Estratégia de banco de dados:
  - SQLite in-memory por padrão (sem dependências externas, roda localmente).
  - Se TEST_DATABASE_URL estiver definida, usa PostgreSQL real (ideal para CI/Docker).

Motivo do SQLite:
  - PostgreSQL-specific types (UUID, JSONB) funcionam em SQLite via SQLAlchemy 2:
    * postgresql.UUID herda de sqltypes.UUID (cross-platform em SQLAlchemy 2)
    * postgresql.JSONB herda de JSON (serialização Python-side é suficiente)
  - SentencaHistorica (pgvector) NÃO é importada neste path de import → não
    aparece em Base.metadata → create_all() funciona.

Execução:
  cd src/back && pytest tests/
  ou com PostgreSQL real:
  TEST_DATABASE_URL=postgresql+psycopg://enteros:enteros_dev@localhost:5432/enteros_test pytest tests/
"""

from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Importa os models ANTES de Base.metadata.create_all() para que as tabelas
# sejam registradas. NÃO importar SentencaHistorica (usa pgvector).
from app.db.models.analise_ia import AnaliseIA  # noqa: F401
from app.db.models.decisao_advogado import DecisaoAdvogado  # noqa: F401
from app.db.models.documento import Documento  # noqa: F401
from app.db.models.processo import Processo  # noqa: F401
from app.db.models.proposta_acordo import PropostaAcordo  # noqa: F401
from app.db.base import Base
from app.db.session import get_db
from app.main import app


_TEST_DB_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///./test_integration.db")
_CONNECT_ARGS = {"check_same_thread": False} if "sqlite" in _TEST_DB_URL else {}


def _make_test_engine():
    return create_engine(_TEST_DB_URL, connect_args=_CONNECT_ARGS)


@pytest.fixture()
def db() -> Generator[Session, None, None]:
    """Sessão isolada: cria schema fresh + descarta ao final do teste."""
    engine = _make_test_engine()
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db: Session) -> Generator[TestClient, None, None]:
    """TestClient com get_db sobrescrito para usar a sessão SQLite de teste."""

    def _override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers de autenticação — reutilizáveis nos testes
# ---------------------------------------------------------------------------

def get_advogado_token(client: TestClient) -> str:
    """Faz login como advogado e retorna o JWT."""
    resp = client.post(
        "/auth/login",
        data={"username": "advogado@banco.com", "password": "advogado123"},
    )
    assert resp.status_code == 200, f"Login falhou: {resp.text}"
    return resp.json()["access_token"]


def get_banco_token(client: TestClient) -> str:
    """Faz login como banco e retorna o JWT."""
    resp = client.post(
        "/auth/login",
        data={"username": "banco@banco.com", "password": "banco123"},
    )
    assert resp.status_code == 200, f"Login falhou: {resp.text}"
    return resp.json()["access_token"]
