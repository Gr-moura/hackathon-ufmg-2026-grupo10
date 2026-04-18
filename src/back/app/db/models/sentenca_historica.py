from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

EMBEDDING_DIM = 1536  # text-embedding-3-small


class SentencaHistorica(Base):
    __tablename__ = "sentenca_historica"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    numero_caso: Mapped[str | None] = mapped_column(String(60), nullable=True, index=True)
    uf: Mapped[str | None] = mapped_column(String(2), nullable=True, index=True)
    assunto: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sub_assunto: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    resultado_macro: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resultado_micro: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    valor_causa: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    valor_condenacao: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    embedding: Mapped[list | None] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)
