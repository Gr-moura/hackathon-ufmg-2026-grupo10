import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Numeric, String, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Processo(Base):
    __tablename__ = "processo"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    numero_processo: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    advogado_id: Mapped[str] = mapped_column(String(60), nullable=False)
    valor_causa: Mapped[float] = mapped_column(Numeric(12, 2), nullable=True)
    # pendente | processando | analisado | concluido
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pendente")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    documentos: Mapped[list["Documento"]] = relationship(  # type: ignore[name-defined]
        "Documento", back_populates="processo", cascade="all, delete-orphan"
    )
    analise: Mapped["AnaliseIA | None"] = relationship(  # type: ignore[name-defined]
        "AnaliseIA", back_populates="processo", uselist=False
    )
