import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AnaliseIA(Base):
    __tablename__ = "analise_ia"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    processo_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("processo.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    # ACORDO | DEFESA
    decisao: Mapped[str] = mapped_column(String(10), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    fatores_pro_acordo: Mapped[list] = mapped_column(JSON, default=list)
    fatores_pro_defesa: Mapped[list] = mapped_column(JSON, default=list)
    requires_supervisor: Mapped[bool] = mapped_column(default=False)
    variaveis_extraidas: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    casos_similares: Mapped[list | None] = mapped_column(JSON, nullable=True)
    trechos_chave: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    processo: Mapped["Processo"] = relationship(  # type: ignore[name-defined]
        "Processo", back_populates="analise"
    )
    proposta: Mapped["PropostaAcordo | None"] = relationship(  # type: ignore[name-defined]
        "PropostaAcordo", back_populates="analise", uselist=False
    )
    decisao_advogado: Mapped["DecisaoAdvogado | None"] = relationship(  # type: ignore[name-defined]
        "DecisaoAdvogado", back_populates="analise", uselist=False
    )
