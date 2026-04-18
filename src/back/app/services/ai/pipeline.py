"""Pipeline de IA — orquestra RN1 (classificador) e GPT Acordo (valuator)."""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy.orm import Session, selectinload

from app.core.logging import get_logger
from app.db.models.analise_ia import AnaliseIA
from app.db.models.processo import Processo
from app.db.models.proposta_acordo import PropostaAcordo
from app.services.ai.classifier import build_case_data, predict_outcome
from app.services.ai.extractor import ProcessMetadata, extract_from_documents
from app.services.ai.valuator import ValuationContext, evaluate_settlement
from app.services.ingestion.pdf import IngestedDocument

logger = get_logger(__name__)

_POLICY_PATH = Path(__file__).parents[3] / "policy.yaml"


def _load_policy() -> dict[str, Any]:
    try:
        with open(_POLICY_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as exc:
        logger.warning("Falha ao ler policy.yaml: %s — usando defaults", exc)
        return {"confidence_thresholds": {"yellow": 0.60, "green": 0.85}}


def _extract_metadata(processo: Processo) -> ProcessMetadata:
    """Usa metadata já extraída ou chama o extractor via OpenAI."""
    if processo.metadata_extraida:
        meta = processo.metadata_extraida
        return ProcessMetadata(
            uf=meta.get("uf"),
            valor_da_causa=meta.get("valor_da_causa") or meta.get("valor_causa"),
            sub_assunto=meta.get("sub_assunto"),
        )

    docs_with_text = [
        IngestedDocument(
            doc_type=d.doc_type,
            raw_text=d.raw_text or "",
            page_count=d.page_count,
        )
        for d in processo.documentos
        if d.raw_text
    ]

    if not docs_with_text:
        logger.warning(
            "processo=%s sem documentos com texto — metadados vazios", processo.id
        )
        return ProcessMetadata()

    return extract_from_documents(docs_with_text)


def _build_rationale(
    decisao: str,
    prob_derrota: float,
    threshold: float,
    meta: ProcessMetadata,
    doc_types: list[str],
) -> str:
    uf = meta.uf or "N/A"
    valor = f"R$ {meta.valor_da_causa:,.2f}" if meta.valor_da_causa else "N/A"
    sub = meta.sub_assunto or "generico"
    docs_presentes = [dt for dt in doc_types if dt not in ("PETICAO_INICIAL", "PROCURACAO", "OUTRO")]

    if decisao == "ACORDO":
        return (
            f"RN1 estimou probabilidade de derrota em {prob_derrota:.1%}, "
            f"acima do limiar configurado de {threshold:.0%}. "
            f"Processo: UF={uf}, sub-assunto={sub}, valor={valor}. "
            f"Subsídios presentes: {', '.join(docs_presentes) or 'nenhum'}. "
            "Recomenda-se proposta de acordo para mitigar risco."
        )
    return (
        f"RN1 estimou probabilidade de derrota em {prob_derrota:.1%}, "
        f"abaixo do limiar configurado de {threshold:.0%}. "
        f"Processo: UF={uf}, sub-assunto={sub}, valor={valor}. "
        f"Subsídios presentes: {', '.join(docs_presentes) or 'nenhum'}. "
        "Base documental suficiente para sustentar defesa judicial."
    )


def run_pipeline(processo_id: uuid.UUID, db: Session) -> AnaliseIA:
    """Executa o pipeline de IA para um processo e persiste o resultado no banco.

    Estágio 2: RN1 prediz probabilidade de derrota.
    Estágio 4 (condicional): GPT Acordo valora o acordo se prob_derrota > threshold.

    Args:
        processo_id: UUID do processo a analisar.
        db: Sessão SQLAlchemy ativa.

    Returns:
        AnaliseIA persistida com decisão, rationale e proposta (se ACORDO).
    """
    processo = (
        db.query(Processo)
        .options(selectinload(Processo.documentos))
        .filter(Processo.id == processo_id)
        .first()
    )
    if processo is None:
        raise ValueError(f"Processo {processo_id} não encontrado")

    processo.status = "processando"
    db.flush()

    policy = _load_policy()
    threshold: float = policy.get("confidence_thresholds", {}).get("yellow", 0.60)
    green: float = policy.get("confidence_thresholds", {}).get("green", 0.85)

    # Estágio 1 — metadados (extração ou cache)
    meta = _extract_metadata(processo)
    doc_types = [d.doc_type for d in processo.documentos]

    # Persiste metadados extraídos se ainda não havia
    if not processo.metadata_extraida:
        processo.metadata_extraida = {
            "uf": meta.uf,
            "valor_da_causa": meta.valor_da_causa,
            "sub_assunto": meta.sub_assunto.value if meta.sub_assunto else None,
        }

    # Estágio 2 — RN1
    case_data = build_case_data(
        uf=meta.uf,
        sub_assunto=meta.sub_assunto.value if meta.sub_assunto else None,
        valor_causa=meta.valor_da_causa or float(processo.valor_causa or 0),
        doc_types=doc_types,
    )

    try:
        prob_derrota = predict_outcome(case_data)
    except RuntimeError as exc:
        logger.error("Falha no RN1 — usando fallback heurístico: %s", exc)
        # Fallback: heurística baseada em subsídios presentes
        doc_subsídios = {"CONTRATO", "EXTRATO", "COMPROVANTE_CREDITO", "DOSSIE"}
        presentes = len(doc_subsídios & set(doc_types))
        prob_derrota = max(0.75 - presentes * 0.10, 0.20)

    decisao = "ACORDO" if prob_derrota > threshold else "DEFESA"
    confidence = prob_derrota if decisao == "ACORDO" else 1.0 - prob_derrota
    requires_supervisor = not (confidence >= green)

    fatores_pro_acordo: list[str] = []
    fatores_pro_defesa: list[str] = []

    if meta.sub_assunto and meta.sub_assunto.value == "golpe":
        fatores_pro_acordo.append("Sub-assunto classificado como golpe — maior exposição ao banco")
    for dt in ("CONTRATO", "COMPROVANTE_CREDITO", "DOSSIE"):
        if dt in doc_types:
            fatores_pro_defesa.append(f"Subsídio {dt} presente — sustenta defesa")
        else:
            fatores_pro_acordo.append(f"Ausência de {dt} fragiliza a defesa")

    rationale = _build_rationale(decisao, prob_derrota, threshold, meta, doc_types)

    logger.info(
        "Pipeline concluído: processo=%s decisao=%s prob_derrota=%.3f confidence=%.3f",
        processo_id,
        decisao,
        prob_derrota,
        confidence,
    )

    # Upsert AnaliseIA
    analise = (
        db.query(AnaliseIA).filter(AnaliseIA.processo_id == processo_id).first()
        or AnaliseIA(id=uuid.uuid4(), processo_id=processo_id)
    )
    analise.decisao = decisao
    analise.confidence = round(confidence, 4)
    analise.rationale = rationale
    analise.fatores_pro_acordo = fatores_pro_acordo
    analise.fatores_pro_defesa = fatores_pro_defesa
    analise.requires_supervisor = requires_supervisor
    analise.variaveis_extraidas = case_data
    analise.trechos_chave = []
    db.add(analise)
    db.flush()

    # Estágio 4 — Valuator (apenas para ACORDO)
    if decisao == "ACORDO":
        valor_causa = meta.valor_da_causa or float(processo.valor_causa or 1000.0)
        doc_texts = "\n\n---\n\n".join(
            f"[{d.doc_type}]\n{d.raw_text}"
            for d in processo.documentos
            if d.raw_text
        )

        valuation_ctx = ValuationContext(
            valor_da_causa=valor_causa,
            probabilidade_vitoria=1.0 - prob_derrota,
            sub_assunto=meta.sub_assunto.value if meta.sub_assunto else "generico",
            pontos_fortes=fatores_pro_defesa,
            pontos_fracos=fatores_pro_acordo,
            document_texts=doc_texts,
        )

        try:
            val_result = evaluate_settlement(valuation_ctx)
            piso_pct = policy.get("settlement_bounds", {}).get("piso_pct_valor_causa", 0.30)
            proposta = (
                db.query(PropostaAcordo)
                .filter(PropostaAcordo.analise_id == analise.id)
                .first()
                or PropostaAcordo(id=uuid.uuid4(), analise_id=analise.id)
            )
            proposta.valor_sugerido = val_result.valor_sugerido
            proposta.valor_base_estatistico = round(valor_causa * piso_pct, 2)
            proposta.modulador_llm = round(
                val_result.valor_sugerido / max(valor_causa * piso_pct, 1.0), 4
            )
            proposta.intervalo_min = round(valor_causa * piso_pct, 2)
            proposta.intervalo_max = val_result.intervalo_max
            proposta.custo_estimado_litigar = val_result.custo_estimado_litigar
            proposta.n_casos_similares = 0
            db.add(proposta)
            analise.rationale = rationale + f"\n\n{val_result.justificativa}"
        except Exception as exc:
            logger.error("Falha no Valuator — proposta não gerada: %s", exc)

    processo.status = "analisado"
    db.commit()
    db.refresh(analise)
    return analise
