import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DecisaoAdvogado(Base):
    __tablename__ = "decisao_advogado"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    analise_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("analise_ia.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    # ACEITAR | AJUSTAR | RECUSAR
    acao: Mapped[str] = mapped_column(String(10), nullable=False)
    valor_advogado: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    justificativa: Mapped[str | None] = mapped_column(Text, nullable=True)
    advogado_id: Mapped[str] = mapped_column(String(60), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    analise: Mapped["AnaliseIA"] = relationship(  # type: ignore[name-defined]
        "AnaliseIA", back_populates="decisao_advogado"
    )
