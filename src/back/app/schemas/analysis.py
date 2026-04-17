from __future__ import annotations

from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class Decisao(str, Enum):
    ACORDO = "ACORDO"
    DEFESA = "DEFESA"


class AcaoAdvogado(str, Enum):
    ACEITAR = "ACEITAR"
    AJUSTAR = "AJUSTAR"
    RECUSAR = "RECUSAR"


class TrechoChave(BaseModel):
    doc: str
    page: int
    quote: str = Field(..., max_length=500)


class PropostaAcordoResponse(BaseModel):
    valor_sugerido: float
    intervalo_min: float
    intervalo_max: float
    custo_estimado_litigar: float
    economia_esperada: float
    n_casos_similares: int


class AnaliseIAResponse(BaseModel):
    id: UUID
    processo_id: UUID
    decisao: Decisao
    confidence: float = Field(..., ge=0.0, le=1.0)
    rationale: str
    fatores_pro_acordo: list[str]
    fatores_pro_defesa: list[str]
    requires_supervisor: bool
    proposta: PropostaAcordoResponse | None = None
    trechos_chave: list[TrechoChave]


class DecisaoAdvogadoRequest(BaseModel):
    acao: AcaoAdvogado
    valor_advogado: float | None = None
    justificativa: str | None = None
