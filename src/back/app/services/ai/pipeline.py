"""Pipeline de IA — orquestra RN1 + RAG per-processo + LLM classifier + Valuator.

Fluxo:
    1. Extrai metadados (cache em `Processo.metadata_extraida` ou via extractor GPT).
    2. Constrói `InProcessRetriever` com os PDFs do processo corrente e recupera
       trechos por tópico (assinatura / valor_operacao / provas_banco / fraude).
    3. Executa o RN1 (classificador PyTorch) para estimar `probabilidade_vitoria`
       quantitativa. Fallback heurístico em falha.
    4. Chama o `llm_classifier` com metadados + RN1 prob + trechos RAG para decidir
       ACORDO vs DEFESA com rationale textual. Fallback ao threshold do RN1.
    5. Para ACORDO, chama o Valuator (GPT) alimentado com os trechos grounded do
       RAG em `document_texts`. Fallback: proposta determinística do policy.yaml.
    6. Persiste AnaliseIA (+ PropostaAcordo) idempotente.
"""
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
from app.services.ai.llm_classifier import ClassifierInput, classify
from app.services.ai.retriever import InProcessRetriever, RetrievedChunk
from app.services.ai.valuator import ValuationContext, evaluate_settlement
from app.services.ingestion.pdf import IngestedDocument

logger = get_logger(__name__)

_POLICY_PATH = Path(__file__).parents[3] / "policy.yaml"

# Tópicos investigados pelo RAG — perguntas em linguagem natural para kNN.
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
        "dossiê de verificação de identidade"
    ),
    "fraude": (
        "alegação de fraude, golpe, estelionato, uso indevido de documentos, "
        "contratação por terceiro sem consentimento"
    ),
}


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

    try:
        return extract_from_documents(docs_with_text)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Extractor falhou — metadados vazios: %s", exc)
        return ProcessMetadata()


def _grounded_text(
    retrieved_by_topic: dict[str, list[RetrievedChunk]], budget: int = 12_000
) -> str:
    """Concatena só os trechos retornados pelo RAG para alimentar o valuator."""
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


def _trechos_chave_from_rag(
    retrieved_by_topic: dict[str, list[RetrievedChunk]], limit: int = 5
) -> list[dict[str, Any]]:
    """Converte os chunks recuperados no formato `trechos_chave` persistido."""
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()
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


def _build_rationale(
    decisao: str,
    prob_derrota: float,
    threshold: float,
    meta: ProcessMetadata,
    doc_types: list[str],
    rag_method: str,
    n_chunks: int,
    clf_rationale: str | None,
) -> str:
    uf = meta.uf or "N/A"
    valor = f"R$ {meta.valor_da_causa:,.2f}" if meta.valor_da_causa else "N/A"
    sub = meta.sub_assunto or "generico"
    docs_presentes = [
        dt for dt in doc_types if dt not in ("PETICAO_INICIAL", "PROCURACAO", "OUTRO")
    ]

    head = (
        f"RN1 estimou probabilidade de derrota em {prob_derrota:.1%}, "
        f"{'acima' if decisao == 'ACORDO' else 'abaixo'} do limiar de {threshold:.0%}. "
        f"Processo: UF={uf}, sub-assunto={sub}, valor={valor}. "
        f"Subsídios presentes: {', '.join(docs_presentes) or 'nenhum'}. "
        f"RAG={rag_method} com {n_chunks} chunks dos PDFs do processo."
    )
    if clf_rationale:
        head += f"\n\nClassifier LLM: {clf_rationale}"
    tail = (
        " Recomenda-se proposta de acordo para mitigar risco."
        if decisao == "ACORDO"
        else " Base documental suficiente para sustentar defesa judicial."
    )
    return head + tail


def run_pipeline(processo_id: uuid.UUID, db: Session) -> AnaliseIA:
    """Executa o pipeline de IA para um processo e persiste o resultado no banco.

    Args:
        processo_id: UUID do processo a analisar.
        db: Sessão SQLAlchemy ativa.

    Returns:
        AnaliseIA persistida com decisão, rationale, trechos_chave (RAG) e
        PropostaAcordo (se ACORDO).
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

    # Estágio 1 — metadados
    meta = _extract_metadata(processo)
    doc_types = [d.doc_type for d in processo.documentos]

    if not processo.metadata_extraida:
        processo.metadata_extraida = {
            "uf": meta.uf,
            "valor_da_causa": meta.valor_da_causa,
            "sub_assunto": meta.sub_assunto.value if meta.sub_assunto else None,
        }

    # Estágio 2 — RAG sobre os PDFs do próprio processo
    retriever = InProcessRetriever.from_documents(processo.documentos)
    retrieved_by_topic: dict[str, list[RetrievedChunk]] = {
        topic: retriever.search(question, k=3)
        for topic, question in _RAG_TOPICS.items()
    }
    grounded = _grounded_text(retrieved_by_topic)
    logger.info(
        "RAG method=%s | chunks=%d | trechos/tópico=%s",
        retriever.method,
        len(retriever.chunks),
        {t: len(v) for t, v in retrieved_by_topic.items()},
    )

    # Estágio 3 — RN1 (quantitativo)
    sub_assunto_str = meta.sub_assunto.value if meta.sub_assunto else None
    case_data = build_case_data(
        uf=meta.uf,
        sub_assunto=sub_assunto_str,
        valor_causa=meta.valor_da_causa or float(processo.valor_causa or 0),
        doc_types=doc_types,
    )
    try:
        prob_derrota = predict_outcome(case_data)
    except RuntimeError as exc:
        logger.error("Falha no RN1 — usando fallback heurístico: %s", exc)
        doc_subsídios = {"CONTRATO", "EXTRATO", "COMPROVANTE_CREDITO", "DOSSIE"}
        presentes = len(doc_subsídios & set(doc_types))
        prob_derrota = max(0.75 - presentes * 0.10, 0.20)

    # Estágio 4 — LLM classifier (qualitativo, com RAG)
    fatores_pro_acordo: list[str] = []
    fatores_pro_defesa: list[str] = []
    if meta.sub_assunto and meta.sub_assunto.value == "golpe":
        fatores_pro_acordo.append(
            "Sub-assunto classificado como golpe — maior exposição ao banco"
        )
    for dt in ("CONTRATO", "COMPROVANTE_CREDITO", "DOSSIE"):
        if dt in doc_types:
            fatores_pro_defesa.append(f"Subsídio {dt} presente — sustenta defesa")
        else:
            fatores_pro_acordo.append(f"Ausência de {dt} fragiliza a defesa")

    trechos_para_prompt = [
        rc.chunk.preview(max_chars=300)
        for rc in (
            retrieved_by_topic.get("fraude", [])[:2]
            + retrieved_by_topic.get("assinatura", [])[:1]
        )
    ]

    clf_out = classify(
        ClassifierInput(
            uf=meta.uf,
            sub_assunto=sub_assunto_str,
            valor_causa=meta.valor_da_causa,
            doc_types_presentes=sorted(set(doc_types)),
            fatores_pro_acordo=fatores_pro_acordo,
            fatores_pro_defesa=fatores_pro_defesa,
            penalty_documental=-prob_derrota,
            probabilidade_vitoria_historica=round(1.0 - prob_derrota, 3),
            casos_similares=[
                {
                    "n_amostras": 0,
                    "uf": meta.uf,
                    "sub_assunto": sub_assunto_str,
                    "win_rate": round(1.0 - prob_derrota, 3),
                }
            ],
            trechos_peticao=trechos_para_prompt,
        )
    )

    clf_rationale: str | None = None
    if clf_out is not None:
        decisao = clf_out.decisao
        confidence = clf_out.confidence
        clf_rationale = clf_out.rationale
        fatores_pro_acordo = fatores_pro_acordo + list(
            clf_out.fatores_extra_pro_acordo
        )
        fatores_pro_defesa = fatores_pro_defesa + list(
            clf_out.fatores_extra_pro_defesa
        )
    else:
        # Fallback ao threshold do RN1
        decisao = "ACORDO" if prob_derrota > threshold else "DEFESA"
        confidence = prob_derrota if decisao == "ACORDO" else 1.0 - prob_derrota

    requires_supervisor = not (confidence >= green)

    rationale = _build_rationale(
        decisao,
        prob_derrota,
        threshold,
        meta,
        doc_types,
        retriever.method,
        len(retriever.chunks),
        clf_rationale,
    )

    logger.info(
        "Pipeline: processo=%s decisao=%s prob_derrota=%.3f confidence=%.3f RAG=%s",
        processo_id,
        decisao,
        prob_derrota,
        confidence,
        retriever.method,
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
    analise.variaveis_extraidas = {
        **case_data,
        "rag_method": retriever.method,
        "rag_n_chunks": len(retriever.chunks),
    }
    analise.trechos_chave = _trechos_chave_from_rag(retrieved_by_topic)
    db.add(analise)
    db.flush()

    # Estágio 5 — Valuator (apenas para ACORDO)
    if decisao == "ACORDO":
        valor_causa = meta.valor_da_causa or float(processo.valor_causa or 1000.0)
        # Prioriza trechos RAG (grounded); cai para texto bruto se o RAG não achou nada.
        doc_texts = grounded or "\n\n---\n\n".join(
            f"[{d.doc_type}]\n{d.raw_text}"
            for d in processo.documentos
            if d.raw_text
        )

        valuation_ctx = ValuationContext(
            valor_da_causa=valor_causa,
            probabilidade_vitoria=1.0 - prob_derrota,
            sub_assunto=sub_assunto_str or "generico",
            pontos_fortes=fatores_pro_defesa,
            pontos_fracos=fatores_pro_acordo,
            document_texts=doc_texts,
        )

        try:
            val_result = evaluate_settlement(valuation_ctx)
            piso_pct = policy.get("settlement_bounds", {}).get(
                "piso_pct_valor_causa", 0.30
            )
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
