"""Pipeline de análise IA — orquestra retriever + classifier + valuator + persistência.

Fluxo:
    1. Lê metadados já extraídos no upload (`Processo.metadata_extraida`).
    2. Constrói `InProcessRetriever` com RAG sobre os PDFs do processo corrente.
    3. Consulta o histórico (`sentenca_historica`) para a probabilidade empírica
       de vitória por UF/sub_assunto — puramente SQL, sem embedding.
    4. Calcula penalidades documentais + proposta determinística (policy.yaml).
    5. Chama `classifier.classify()` com os trechos retrivados + stats históricos.
       Em falha/sem key → fallback heurístico `_decisao()`.
    6. Chama `valuator.evaluate_settlement()` com os mesmos trechos grounded.
       Em falha/sem key → mantém proposta determinística.
    7. Persiste `AnaliseIA` (+ `PropostaAcordo` se ACORDO). Idempotente.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.models.analise_ia import AnaliseIA
from app.db.models.documento import Documento  # noqa: F401 (type hint context)
from app.db.models.processo import Processo
from app.db.models.proposta_acordo import PropostaAcordo
from app.services.ai.llm_classifier import ClassifierInput, classify
from app.services.ai.retriever import (
    InProcessRetriever,
    RetrievedChunk,
    lookup_historical_win_rate,
)
from app.services.ai.valuator import (
    ValuationContext,
    ValuationResult,
    evaluate_settlement,
    load_policy,
)

logger = get_logger(__name__)


# Tópicos de interesse para grounding do classifier + valuator.
_RAG_TOPICS: dict[str, str] = {
    "assinatura": (
        "cláusulas sobre assinatura, autenticidade do contrato, "
        "alegação de falsificação ou não-reconhecimento de assinatura"
    ),
    "valor_operacao": (
        "valor da operação, valor do empréstimo contratado, "
        "montante depositado ou liberado ao consumidor"
    ),
    "provas_banco": (
        "contrato de adesão, extrato bancário, comprovante de crédito, "
        "dossiê de verificação de identidade, subsídios do banco"
    ),
    "fraude": (
        "alegação de fraude, golpe, estelionato, uso indevido de documentos, "
        "contratação por terceiro sem consentimento"
    ),
}


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

    majoracao = 1.3 if sub_assunto == "golpe" else 1.0
    custo_litigar = min(
        valor_causa * majoracao + piso_abs, valor_causa * majoracao + teto_abs
    )

    intervalo_min = max(valor_causa * piso_pct, piso_abs)
    intervalo_max = min(valor_causa * teto_pct, custo_litigar * 0.75, teto_abs)
    valor_sugerido = max(intervalo_min, min(valor_causa * 0.40, intervalo_max))

    return {
        "valor_sugerido": round(valor_sugerido, 2),
        "intervalo_min": round(intervalo_min, 2),
        "intervalo_max": round(intervalo_max, 2),
        "custo_estimado_litigar": round(custo_litigar, 2),
    }


def _grounded_text(
    retrieved_by_topic: dict[str, list[RetrievedChunk]], budget: int = 12_000
) -> str:
    """Concatena só os trechos retornados pelo RAG, evitando estouro de contexto."""
    blocks: list[str] = []
    remaining = budget
    for topic, chunks in retrieved_by_topic.items():
        if not chunks:
            continue
        blocks.append(f"### {topic.upper()}")
        for rc in chunks:
            line = (
                f"[{rc.chunk.doc_type} — {rc.chunk.doc_filename}] "
                f"(score={rc.score:.3f})\n{rc.chunk.text}"
            )
            if len(line) > remaining:
                line = line[:remaining]
            blocks.append(line)
            remaining -= len(line)
            if remaining <= 0:
                break
        if remaining <= 0:
            break
    return "\n\n".join(blocks)


def _decisao_heuristica(
    confidence: float, penalty: float, historical_win_rate: float
) -> str:
    """Fallback determinístico: ACORDO se doc fraca OU histórico ruim OU conf alta."""
    if penalty <= -0.30:
        return "ACORDO"
    if historical_win_rate <= 0.25:
        return "ACORDO"
    if confidence >= 0.65:
        return "ACORDO"
    return "DEFESA"


def _confidence(penalty: float, has_peticao: bool, has_extrato: bool) -> float:
    """Confidence base (antes do classifier LLM)."""
    base = 0.90
    base += penalty
    if not has_peticao:
        base -= 0.15
    if not has_extrato:
        base -= 0.05
    return max(0.20, min(0.99, round(base, 3)))


def _trechos_chave_from_rag(
    retrieved_by_topic: dict[str, list[RetrievedChunk]], limit: int = 5
) -> list[dict[str, Any]]:
    """Transforma os chunks recuperados em `trechos_chave` para persistência."""
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()
    # Achata topic→chunk mantendo ordem de prioridade dos tópicos.
    for _topic, chunks in retrieved_by_topic.items():
        for rc in chunks:
            key = (rc.chunk.doc_type, rc.chunk.chunk_index)
            if key in seen:
                continue
            seen.add(key)
            out.append(
                {
                    "doc": rc.chunk.doc_type,
                    "page": 1,
                    "quote": rc.chunk.preview(),
                }
            )
            if len(out) >= limit:
                return out
    return out


def run_pipeline(processo_or_id, db: Session) -> AnaliseIA:
    """Executa o pipeline completo e persiste AnaliseIA + PropostaAcordo.

    Aceita tanto um `Processo` já carregado quanto um UUID — o router passa o
    UUID via `asyncio.to_thread` para evitar compartilhar Sessions entre
    threads.

    Idempotente: se já existir análise para o processo, apenas retorna a existente.
    """
    if isinstance(processo_or_id, Processo):
        processo = processo_or_id
    else:
        processo = db.get(Processo, processo_or_id)
        if processo is None:
            raise ValueError(f"Processo {processo_or_id} não encontrado")

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
    confidence_base = _confidence(penalty, has_peticao, has_extrato)

    # --- RAG sobre os PDFs do próprio processo -------------------------------
    retriever = InProcessRetriever.from_documents(processo.documentos)
    retrieved_by_topic: dict[str, list[RetrievedChunk]] = {
        topic: retriever.search(question, k=3)
        for topic, question in _RAG_TOPICS.items()
    }
    grounded = _grounded_text(retrieved_by_topic)
    logger.info(
        "RAG method=%s | chunks=%d | trechos por tópico=%s",
        retriever.method,
        len(retriever.chunks),
        {t: len(v) for t, v in retrieved_by_topic.items()},
    )

    # --- Lookup histórico (SQL, sem embedding) -------------------------------
    historical_win_rate, n_historical = lookup_historical_win_rate(
        db, uf, sub_assunto
    )

    # --- Proposta determinística ----------------------------------------------
    if valor_causa <= 0:
        logger.warning(
            "Processo %s sem valor_causa — proposta será omitida",
            processo.numero_processo,
        )
        valores: dict[str, float] | None = None
    else:
        valores = _base_proposta(valor_causa, sub_assunto, policy)

    # --- Classifier LLM (com grounding RAG) -----------------------------------
    fatores_pro_acordo_base: list[str] = []
    if has_peticao:
        fatores_pro_acordo_base.append("peticao_inicial_ingerida")
    if has_extrato:
        fatores_pro_acordo_base.append("extrato_bancario_disponivel")
    if sub_assunto == "golpe":
        fatores_pro_acordo_base.append("indicio_de_fraude_terceiro")
    if uf:
        fatores_pro_acordo_base.append(f"jurisdicao_{uf}")

    trechos_peticao_para_prompt = [
        rc.chunk.preview(max_chars=300)
        for rc in (retrieved_by_topic.get("fraude", [])[:2]
                   + retrieved_by_topic.get("assinatura", [])[:1])
    ]

    clf_input = ClassifierInput(
        uf=uf,
        sub_assunto=sub_assunto,
        valor_causa=valor_causa or None,
        doc_types_presentes=sorted(doc_types),
        fatores_pro_acordo=fatores_pro_acordo_base,
        fatores_pro_defesa=fatores_defesa,
        penalty_documental=penalty,
        probabilidade_vitoria_historica=historical_win_rate,
        casos_similares=[
            {
                "n_amostras": n_historical,
                "uf": uf,
                "sub_assunto": sub_assunto,
                "win_rate": historical_win_rate,
            }
        ],
        trechos_peticao=trechos_peticao_para_prompt,
    )
    clf_output = classify(clf_input)

    if clf_output is not None:
        decisao = clf_output.decisao
        confidence = clf_output.confidence
        rationale_llm = clf_output.rationale
        fatores_pro_acordo = (
            fatores_pro_acordo_base + list(clf_output.fatores_extra_pro_acordo)
        )
        fatores_pro_defesa_final = (
            fatores_defesa + list(clf_output.fatores_extra_pro_defesa)
        )
    else:
        decisao = _decisao_heuristica(
            confidence_base, penalty, historical_win_rate
        )
        confidence = confidence_base
        rationale_llm = None
        fatores_pro_acordo = fatores_pro_acordo_base
        fatores_pro_defesa_final = fatores_defesa

    if not fatores_pro_acordo:
        fatores_pro_acordo.append("documentacao_minima")

    # --- Valuator LLM (refina a proposta com grounding) -----------------------
    llm_rationale: str | None = None
    modulador_llm = 1.0
    if valores:
        try:
            from app.config import get_settings

            if get_settings().openai_api_key:
                ctx = ValuationContext(
                    valor_da_causa=valor_causa,
                    probabilidade_vitoria=historical_win_rate,
                    sub_assunto=sub_assunto or "generico",
                    pontos_fortes=fatores_pro_defesa_final,
                    pontos_fracos=fatores_defesa,
                    document_texts=grounded or "(sem trechos relevantes recuperados)",
                )
                refined: ValuationResult = evaluate_settlement(ctx)
                modulador_llm = (
                    float(refined.valor_sugerido)
                    / max(valores["valor_sugerido"], 1.0)
                )
                clamped_valor = max(
                    valores["intervalo_min"],
                    min(
                        float(refined.valor_sugerido),
                        valores["intervalo_max"],
                    ),
                )
                valores["valor_sugerido"] = round(clamped_valor, 2)
                clamped_max = max(
                    valores["intervalo_max"],
                    min(
                        float(refined.intervalo_max),
                        valores["custo_estimado_litigar"],
                    ),
                )
                valores["intervalo_max"] = round(clamped_max, 2)
                valores["custo_estimado_litigar"] = round(
                    float(refined.custo_estimado_litigar), 2
                )
                llm_rationale = refined.justificativa
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Refinamento LLM (valuator) falhou — seguindo determinístico: %s",
                exc,
            )

    # --- Rationale consolidado ------------------------------------------------
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
        (
            f"Histórico {uf or '-'}/{sub_assunto or '-'}: "
            f"{historical_win_rate:.0%} de êxito em {n_historical} casos."
        ),
        f"RAG={retriever.method} com {len(retriever.chunks)} chunks.",
    ]
    if rationale_llm:
        rationale_parts.append(f"Classifier: {rationale_llm}")
    if llm_rationale:
        rationale_parts.append(f"Valuator: {llm_rationale}")
    if not rationale_llm and not llm_rationale:
        rationale_parts.append(
            "Recomendação baseada em policy e heurísticas determinísticas."
        )
    rationale = " ".join(rationale_parts)

    # --- Persistência ---------------------------------------------------------
    analise = AnaliseIA(
        processo_id=processo.id,
        decisao=decisao,
        confidence=confidence,
        rationale=rationale,
        fatores_pro_acordo=fatores_pro_acordo,
        fatores_pro_defesa=fatores_pro_defesa_final,
        requires_supervisor=confidence < 0.60,
        variaveis_extraidas={
            "uf": uf,
            "sub_assunto": sub_assunto,
            "valor_da_causa": valor_causa or None,
            "doc_types": sorted(doc_types),
            "probabilidade_vitoria_historica": historical_win_rate,
            "n_casos_historicos": n_historical,
            "rag_method": retriever.method,
        },
        casos_similares=[
            {
                "n_amostras": n_historical,
                "uf": uf,
                "sub_assunto": sub_assunto,
                "win_rate": historical_win_rate,
            }
        ] if n_historical else None,
        trechos_chave=_trechos_chave_from_rag(retrieved_by_topic),
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
            n_casos_similares=n_historical,
        )
        db.add(proposta)

    processo.status = "analisado"
    db.commit()
    db.refresh(analise)

    logger.info(
        "Pipeline concluído: processo=%s | decisao=%s | confidence=%.2f | RAG=%s",
        processo.numero_processo,
        decisao,
        confidence,
        retriever.method,
    )
    return analise
