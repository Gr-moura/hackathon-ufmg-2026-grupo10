import uuid

from sqlalchemy import Float, ForeignKey, Numeric, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PropostaAcordo(Base):
    __tablename__ = "proposta_acordo"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    analise_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("analise_ia.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    valor_sugerido: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    valor_base_estatistico: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    modulador_llm: Mapped[float] = mapped_column(Float, nullable=False)
    intervalo_min: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    intervalo_max: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    custo_estimado_litigar: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    n_casos_similares: Mapped[int] = mapped_column(default=0)

    analise: Mapped["AnaliseIA"] = relationship(  # type: ignore[name-defined]
        "AnaliseIA", back_populates="proposta"
    )
