"""Pipeline de análise IA — orquestra extractor + valuator + persistência.

O pipeline é determinístico por padrão (baseado em `policy.yaml`) e
enriquece com chamadas LLM apenas se `OPENAI_API_KEY` estiver configurada.
Isso permite demos e testes offline sem depender de credenciais externas.

Fluxo:
    1. Lê metadados já extraídos no upload (`Processo.metadata_extraida`).
    2. Calcula penalidades documentais (contrato/comprovante/dossiê ausentes).
    3. Computa proposta via policy (piso/teto) — fallback determinístico.
    4. Opcionalmente refina valores via `valuator.evaluate_settlement`.
    5. Classifica ACORDO vs DEFESA com base em confidence + red flags.
    6. Persiste AnaliseIA + PropostaAcordo no banco.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.models.analise_ia import AnaliseIA
from app.db.models.documento import Documento
from app.db.models.processo import Processo
from app.db.models.proposta_acordo import PropostaAcordo
from app.services.ai.valuator import (
    ValuationContext,
    ValuationResult,
    evaluate_settlement,
    load_policy,
)

logger = get_logger(__name__)


def _completeness_penalty(
    doc_types: set[str], policy: dict[str, Any]
) -> tuple[float, list[str]]:
    """Retorna (penalidade acumulada, fatores pró-defesa) com base em documentos ausentes."""
    penalties = policy.get("documental_completeness_penalty", {})
    total = 0.0
    fatores: list[str] = []
    if "CONTRATO" not in doc_types:
        total += float(penalties.get("contrato_ausente", -0.20))
        fatores.append("contrato_ausente")
    if "COMPROVANTE_CREDITO" not in doc_types:
        total += float(penalties.get("comprovante_credito_ausente", -0.15))
        fatores.append("comprovante_credito_ausente")
    if "DOSSIE" not in doc_types:
        total += float(penalties.get("dossie_ausente", -0.05))
        fatores.append("dossie_ausente")
    return total, fatores


def _base_proposta(
    valor_causa: float, sub_assunto: str | None, policy: dict[str, Any]
) -> dict[str, float]:
    """Proposta determinística baseada em policy.yaml (piso/teto do valor da causa)."""
    bounds = policy.get("settlement_bounds", {})
    piso_pct = float(bounds.get("piso_pct_valor_causa", 0.30))
    teto_pct = float(bounds.get("teto_pct_valor_causa", 0.70))
    piso_abs = float(bounds.get("piso_absoluto_brl", 1500.00))
    teto_abs = float(bounds.get("teto_absoluto_brl", 50000.00))

    # Majoração para 'golpe' aumenta custo estimado de litigar (danos morais)
    majoracao = 1.3 if sub_assunto == "golpe" else 1.0
    custo_litigar = min(valor_causa * majoracao + piso_abs, valor_causa * majoracao + teto_abs)

    intervalo_min = max(valor_causa * piso_pct, piso_abs)
    intervalo_max = min(valor_causa * teto_pct, custo_litigar * 0.75, teto_abs)
    # Alvo: meio do intervalo, entre piso e 50% do valor da causa
    valor_sugerido = max(intervalo_min, min(valor_causa * 0.40, intervalo_max))

    return {
        "valor_sugerido": round(valor_sugerido, 2),
        "intervalo_min": round(intervalo_min, 2),
        "intervalo_max": round(intervalo_max, 2),
        "custo_estimado_litigar": round(custo_litigar, 2),
    }


def _collect_documents_text(documentos: list[Documento], char_budget: int = 24_000) -> str:
    """Concatena texto dos documentos respeitando um orçamento de caracteres."""
    ordered = sorted(
        [d for d in documentos if d.raw_text],
        key=lambda d: 0 if d.doc_type == "PETICAO_INICIAL" else 1,
    )
    parts: list[str] = []
    remaining = char_budget
    for d in ordered:
        text = (d.raw_text or "")[:remaining]
        if not text:
            break
        header = f"[{d.doc_type} — {d.original_filename}]"
        parts.append(f"{header}\n{text}")
        remaining -= len(text)
        if remaining <= 0:
            break
    return "\n\n---\n\n".join(parts)


def _decisao(confidence: float, penalty: float, sub_assunto: str | None) -> str:
    """ACORDO quando a análise é confiante e não há red flags graves."""
    # Penalidades grandes (documentação pobre) favorecem ACORDO defensivo.
    if penalty <= -0.30:
        return "ACORDO"
    if confidence >= 0.65:
        return "ACORDO"
    return "DEFESA"


def _confidence(penalty: float, has_peticao: bool, has_extrato: bool) -> float:
    """Confidence determinística: começa alta e desconta por falta de evidência."""
    base = 0.90
    base += penalty  # penalty é negativo
    if not has_peticao:
        base -= 0.15
    if not has_extrato:
        base -= 0.05
    return max(0.20, min(0.99, round(base, 3)))


def _pick_trechos(documentos: list[Documento], limit: int = 3) -> list[dict[str, Any]]:
    """Seleciona trechos curtos como evidência — primeira frase de cada documento."""
    trechos: list[dict[str, Any]] = []
    for d in documentos:
        if not d.raw_text:
            continue
        snippet = d.raw_text.strip().replace("\n", " ")[:240]
        if not snippet:
            continue
        trechos.append({"doc": d.doc_type, "page": 1, "quote": snippet})
        if len(trechos) >= limit:
            break
    return trechos


def run_pipeline(processo: Processo, db: Session) -> AnaliseIA:
    """Executa o pipeline completo e persiste AnaliseIA + PropostaAcordo.

    Idempotente: se já existir análise para o processo, apenas retorna a existente.
    """
    if processo.analise is not None:
        logger.info(
            "Análise já existe para processo %s — pulando pipeline",
            processo.numero_processo,
        )
        return processo.analise

    policy = load_policy()
    metadata = processo.metadata_extraida or {}
    valor_causa = (
        float(processo.valor_causa)
        if processo.valor_causa
        else float(metadata.get("valor_da_causa") or 0.0)
    )
    sub_assunto = metadata.get("sub_assunto")
    uf = metadata.get("uf")

    doc_types = {d.doc_type for d in processo.documentos}
    penalty, fatores_defesa = _completeness_penalty(doc_types, policy)

    has_peticao = "PETICAO_INICIAL" in doc_types
    has_extrato = "EXTRATO" in doc_types
    confidence = _confidence(penalty, has_peticao, has_extrato)

    # Valores base determinísticos
    if valor_causa <= 0:
        # Sem valor da causa, não há proposta quantitativa — cria análise sem proposta
        logger.warning(
            "Processo %s sem valor_causa — proposta será omitida",
            processo.numero_processo,
        )
        valores: dict[str, float] | None = None
    else:
        valores = _base_proposta(valor_causa, sub_assunto, policy)

    # Enriquece via LLM quando possível — falha silenciosa em modo demo
    llm_rationale: str | None = None
    modulador_llm = 1.0
    if valores:
        try:
            from app.config import get_settings

            if get_settings().openai_api_key:
                ctx = ValuationContext(
                    valor_da_causa=valor_causa,
                    probabilidade_vitoria=0.30,
                    sub_assunto=sub_assunto or "generico",
                    pontos_fortes=[],
                    pontos_fracos=fatores_defesa,
                    document_texts=_collect_documents_text(processo.documentos),
                )
                refined: ValuationResult = evaluate_settlement(ctx)
                modulador_llm = (
                    float(refined.valor_sugerido) / max(valores["valor_sugerido"], 1.0)
                )
                clamped_valor = max(
                    valores["intervalo_min"],
                    min(float(refined.valor_sugerido), valores["intervalo_max"]),
                )
                valores["valor_sugerido"] = round(clamped_valor, 2)
                clamped_max = max(
                    valores["intervalo_max"],
                    min(float(refined.intervalo_max), valores["custo_estimado_litigar"]),
                )
                valores["intervalo_max"] = round(clamped_max, 2)
                valores["custo_estimado_litigar"] = round(
                    float(refined.custo_estimado_litigar), 2
                )
                llm_rationale = refined.justificativa
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Refinamento LLM falhou — seguindo apenas com policy determinística: %s",
                exc,
            )

    decisao = _decisao(confidence, penalty, sub_assunto)

    fatores_pro_acordo: list[str] = []
    if has_peticao:
        fatores_pro_acordo.append("peticao_inicial_ingerida")
    if has_extrato:
        fatores_pro_acordo.append("extrato_bancario_disponivel")
    if sub_assunto == "golpe":
        fatores_pro_acordo.append("indicio_de_fraude_terceiro")
    if uf:
        fatores_pro_acordo.append(f"jurisdicao_{uf}")
    if not fatores_pro_acordo:
        fatores_pro_acordo.append("documentacao_minima")

    rationale_parts = [
        (
            f"Valor da causa: R$ {valor_causa:,.2f}."
            if valor_causa
            else "Valor da causa não identificado."
        ),
        (
            f"Sub-assunto classificado como '{sub_assunto}'."
            if sub_assunto
            else "Sub-assunto não classificado."
        ),
        (
            f"Documentação com {len(doc_types)} tipos distintos; "
            f"penalidade acumulada {penalty:+.2f}."
        ),
    ]
    if llm_rationale:
        rationale_parts.append(f"LLM: {llm_rationale}")
    else:
        rationale_parts.append(
            "Recomendação baseada na política (piso/teto do valor da causa e histórico estimado)."
        )
    rationale = " ".join(rationale_parts)

    analise = AnaliseIA(
        processo_id=processo.id,
        decisao=decisao,
        confidence=confidence,
        rationale=rationale,
        fatores_pro_acordo=fatores_pro_acordo,
        fatores_pro_defesa=fatores_defesa,
        requires_supervisor=confidence < 0.60,
        variaveis_extraidas={
            "uf": uf,
            "sub_assunto": sub_assunto,
            "valor_da_causa": valor_causa or None,
            "doc_types": sorted(doc_types),
        },
        casos_similares=None,
        trechos_chave=_pick_trechos(processo.documentos),
    )
    db.add(analise)
    db.flush()

    if valores and decisao == "ACORDO":
        proposta = PropostaAcordo(
            analise_id=analise.id,
            valor_sugerido=Decimal(str(valores["valor_sugerido"])),
            valor_base_estatistico=Decimal(str(valores["valor_sugerido"])),
            modulador_llm=modulador_llm,
            intervalo_min=Decimal(str(valores["intervalo_min"])),
            intervalo_max=Decimal(str(valores["intervalo_max"])),
            custo_estimado_litigar=Decimal(str(valores["custo_estimado_litigar"])),
            n_casos_similares=0,
        )
        db.add(proposta)

    processo.status = "analisado"
    db.commit()
    db.refresh(analise)

    logger.info(
        "Pipeline concluído: processo=%s | decisao=%s | confidence=%.2f",
        processo.numero_processo,
        decisao,
        confidence,
    )
    return analise
