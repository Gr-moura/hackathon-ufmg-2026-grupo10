from fastapi import APIRouter

from app.deps import CurrentUser, DbDep
from app.services.metrics.aggregator import get_global_metrics, get_recommendations_feed
from pydantic import BaseModel

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class AderenciaAdvogado(BaseModel):
    advogado_id: str
    total: int
    aceitos: int
    aderencia: float


class DriftConfianca(BaseModel):
    dia: str
    avg_confidence: float


class MetricsResponse(BaseModel):
    total_processos: int
    total_decisoes: int
    aderencia_global: float | None
    economia_total: float | None
    casos_alto_risco: int
    aderencia_por_advogado: list[AderenciaAdvogado]
    drift_confianca: list[DriftConfianca]


class RecommendationFeedItem(BaseModel):
    processo_id: str
    numero_processo: str
    decisao: str
    confidence: float
    valor_sugerido: float | None
    created_at: str


@router.get("/metrics", response_model=MetricsResponse)
def get_metrics(db: DbDep, current_user: CurrentUser) -> MetricsResponse:
    return MetricsResponse(**get_global_metrics(db))


@router.get("/recommendations", response_model=list[RecommendationFeedItem])
def get_recommendations(db: DbDep, current_user: CurrentUser) -> list[RecommendationFeedItem]:
    return [RecommendationFeedItem(**r) for r in get_recommendations_feed(db)]
