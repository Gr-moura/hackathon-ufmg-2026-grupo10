import uuid

from sqlalchemy import ForeignKey, Integer, String, Text, UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

# Tipos de documento conforme §4.1
DOC_TYPES = (
    "PETICAO_INICIAL",
    "PROCURACAO",
    "CONTRATO",
    "EXTRATO",
    "COMPROVANTE_CREDITO",
    "DOSSIE",
    "DEMONSTRATIVO_DIVIDA",
    "LAUDO_REFERENCIADO",
    "OUTRO",
)


class Documento(Base):
    __tablename__ = "documento"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    processo_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("processo.id", ondelete="CASCADE"), nullable=False
    )
    doc_type: Mapped[str] = mapped_column(String(30), nullable=False, default="OUTRO")
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    tables: Mapped[list | None] = mapped_column(JSON, nullable=True)
    page_count: Mapped[int] = mapped_column(Integer, default=0)
    parse_errors: Mapped[list | None] = mapped_column(JSON, nullable=True)

    processo: Mapped["Processo"] = relationship(  # type: ignore[name-defined]
        "Processo", back_populates="documentos"
    )
