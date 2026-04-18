"""Router de análise — DB layer completo; pipeline IA (DEV-2) chamado via run_pipeline."""
import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import joinedload

from app.core.logging import get_logger
from app.db.models.analise_ia import AnaliseIA
from app.db.models.decisao_advogado import DecisaoAdvogado
from app.db.models.processo import Processo
from app.db.models.proposta_acordo import PropostaAcordo
from app.deps import CurrentUser, DbDep
from app.schemas.analysis import (
    AnaliseIAResponse,
    DecisaoAdvogadoRequest,
    Decisao,
    PropostaAcordoResponse,
    TrechoChave,
)

router = APIRouter(tags=["analysis"])
logger = get_logger(__name__)


def _to_response(analise: AnaliseIA) -> AnaliseIAResponse:
    proposta = None
    if analise.proposta:
        p = analise.proposta
        economia = float(p.custo_estimado_litigar) - float(p.valor_sugerido)
        proposta = PropostaAcordoResponse(
            valor_sugerido=p.valor_sugerido,
            intervalo_min=p.intervalo_min,
            intervalo_max=p.intervalo_max,
            custo_estimado_litigar=p.custo_estimado_litigar,
            economia_esperada=max(economia, 0),
            n_casos_similares=p.n_casos_similares,
        )

    trechos = [TrechoChave(**t) for t in (analise.trechos_chave or [])]

    return AnaliseIAResponse(
        id=analise.id,
        processo_id=analise.processo_id,
        decisao=Decisao(analise.decisao),
        confidence=analise.confidence,
        rationale=analise.rationale,
        fatores_pro_acordo=analise.fatores_pro_acordo or [],
        fatores_pro_defesa=analise.fatores_pro_defesa or [],
        requires_supervisor=analise.requires_supervisor,
        proposta=proposta,
        trechos_chave=trechos,
    )


@router.post("/processes/{processo_id}/analyze", response_model=AnaliseIAResponse)
async def analyze_processo(
    processo_id: uuid.UUID,
    db: DbDep,
    current_user: CurrentUser,
) -> AnaliseIAResponse:
    import asyncio

    from app.services.ai.pipeline import run_pipeline

    processo = db.get(Processo, processo_id)
    if not processo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processo não encontrado")

    try:
        analise = await asyncio.to_thread(run_pipeline, processo_id, db)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Erro no pipeline IA: processo=%s erro=%s", processo_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha no pipeline de IA: {exc}",
        ) from exc

    return _to_response(analise)


@router.get("/processes/{processo_id}/analysis", response_model=AnaliseIAResponse)
def get_analysis(
    processo_id: uuid.UUID,
    db: DbDep,
    current_user: CurrentUser,
) -> AnaliseIAResponse:
    analise = (
        db.query(AnaliseIA)
        .options(joinedload(AnaliseIA.proposta))
        .filter(AnaliseIA.processo_id == processo_id)
        .first()
    )
    if not analise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Análise não encontrada")
    return _to_response(analise)


@router.post("/processes/analysis/{analise_id}/decision", status_code=status.HTTP_204_NO_CONTENT)
def register_decision(
    analise_id: uuid.UUID,
    body: DecisaoAdvogadoRequest,
    db: DbDep,
    current_user: CurrentUser,
) -> None:
    analise = db.query(AnaliseIA).options(joinedload(AnaliseIA.proposta)).filter(AnaliseIA.id == analise_id).first()
    if not analise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Análise não encontrada")

    # Validação: AJUSTAR com delta > 15% exige justificativa
    if body.acao == "AJUSTAR" and body.valor_advogado and analise.proposta:
        delta_pct = abs(float(body.valor_advogado) - float(analise.proposta.valor_sugerido)) / float(analise.proposta.valor_sugerido)
        if delta_pct > 0.15 and not body.justificativa:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Justificativa obrigatória quando o delta é superior a 15%",
            )
        if delta_pct > 0.30:
            logger.warning(
                "Delta de valor alto: analise=%s | sugerido=%.2f | advogado=%.2f (%.0f%%)",
                analise_id,
                float(analise.proposta.valor_sugerido),
                float(body.valor_advogado),
                delta_pct * 100,
            )

    # Upsert: atualiza se já existe, cria se não
    decisao = (
        db.query(DecisaoAdvogado).filter(DecisaoAdvogado.analise_id == analise_id).first()
        or DecisaoAdvogado(analise_id=analise_id)
    )
    decisao.acao = body.acao
    decisao.valor_advogado = body.valor_advogado
    decisao.justificativa = body.justificativa
    decisao.advogado_id = current_user["sub"]

    db.add(decisao)

    # Atualiza status do processo
    processo = db.get(Processo, analise.processo_id)
    if processo:
        processo.status = "concluido"

    db.commit()
    logger.info("Decisão registrada: analise=%s acao=%s advogado=%s", analise_id, body.acao, current_user["sub"][:8])
