"""Agregações SQL para aderência e efetividade da política de acordos."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.db.models.analise_ia import AnaliseIA
from app.db.models.decisao_advogado import DecisaoAdvogado
from app.db.models.processo import Processo
from app.db.models.proposta_acordo import PropostaAcordo


def get_global_metrics(db: Session) -> dict:
    """Calcula todas as métricas agregadas para o dashboard do banco."""
    total_processos = db.query(Processo).count()
    total_decisoes = db.query(DecisaoAdvogado).count()

    aceitos = db.query(DecisaoAdvogado).filter(DecisaoAdvogado.acao == "ACEITAR").count()
    aderencia_global = round(aceitos / total_decisoes, 4) if total_decisoes > 0 else None

    # Economia = custo_litigar - valor_efetivamente_pago para casos acordados
    economia_query = (
        db.query(
            func.sum(PropostaAcordo.custo_estimado_litigar - DecisaoAdvogado.valor_advogado)
        )
        .join(AnaliseIA, PropostaAcordo.analise_id == AnaliseIA.id)
        .join(DecisaoAdvogado, DecisaoAdvogado.analise_id == AnaliseIA.id)
        .filter(DecisaoAdvogado.acao.in_(["ACEITAR", "AJUSTAR"]))
        .filter(DecisaoAdvogado.valor_advogado.isnot(None))
        .scalar()
    )

    casos_alto_risco = (
        db.query(AnaliseIA).filter(AnaliseIA.confidence < 0.60).count()
    )

    # Aderência por advogado
    adv_rows = (
        db.query(
            DecisaoAdvogado.advogado_id,
            func.count(DecisaoAdvogado.id).label("total"),
            func.sum(case((DecisaoAdvogado.acao == "ACEITAR", 1), else_=0)).label("aceitos"),
        )
        .group_by(DecisaoAdvogado.advogado_id)
        .all()
    )

    aderencia_por_advogado = [
        {
            "advogado_id": r.advogado_id,
            "total": r.total,
            "aceitos": int(r.aceitos or 0),
            "aderencia": round(int(r.aceitos or 0) / r.total, 4) if r.total > 0 else 0.0,
        }
        for r in adv_rows
    ]

    # Drift de confiança: média diária dos últimos 7 dias
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    drift_rows = (
        db.query(
            func.date(AnaliseIA.created_at).label("dia"),
            func.avg(AnaliseIA.confidence).label("avg_confidence"),
        )
        .filter(AnaliseIA.created_at >= cutoff)
        .group_by(func.date(AnaliseIA.created_at))
        .order_by(func.date(AnaliseIA.created_at))
        .all()
    )

    drift_confianca = [
        {"dia": str(r.dia), "avg_confidence": round(float(r.avg_confidence), 4)}
        for r in drift_rows
    ]

    return {
        "total_processos": total_processos,
        "total_decisoes": total_decisoes,
        "aderencia_global": aderencia_global,
        "economia_total": float(economia_query) if economia_query else None,
        "casos_alto_risco": casos_alto_risco,
        "aderencia_por_advogado": aderencia_por_advogado,
        "drift_confianca": drift_confianca,
    }


def get_recommendations_feed(db: Session, limit: int = 20) -> list[dict]:
    """Lista as análises mais recentes para o feed do Monitoring."""
    rows = (
        db.query(AnaliseIA, Processo, PropostaAcordo)
        .join(Processo, AnaliseIA.processo_id == Processo.id)
        .outerjoin(PropostaAcordo, PropostaAcordo.analise_id == AnaliseIA.id)
        .order_by(AnaliseIA.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "processo_id": str(analise.processo_id),
            "numero_processo": processo.numero_processo,
            "decisao": analise.decisao,
            "confidence": analise.confidence,
            "valor_sugerido": float(proposta.valor_sugerido) if proposta else None,
            "created_at": analise.created_at.isoformat(),
        }
        for analise, processo, proposta in rows
    ]
