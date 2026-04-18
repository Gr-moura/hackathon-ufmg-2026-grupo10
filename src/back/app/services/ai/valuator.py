"""Serviço de precificação de acordos via OpenAI Structured Outputs com ingestão de documentos."""

from __future__ import annotations

from pathlib import Path
from typing import Any, List

import yaml
from openai import OpenAI
from pydantic import BaseModel, Field

from app.config import get_settings
from app.core.logging import get_logger
from app.services.ingestion.pdf import IngestedDocument, ingest_pdf

logger = get_logger(__name__)


def load_policy() -> dict[str, Any]:
    """Carrega as configurações de política de acordos do arquivo policy.yaml."""
    policy_path = Path(__file__).parents[3] / "policy.yaml"
    try:
        with open(policy_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error("Erro ao carregar policy.yaml em %s: %s", policy_path, e)
        return {
            "settlement_bounds": {
                "piso_pct_valor_causa": 0.30,
                "teto_pct_valor_causa": 0.70,
                "piso_absoluto_brl": 1500.00,
            }
        }


def generate_system_prompt(policy: dict[str, Any]) -> str:
    """Gera o prompt de sistema injetando os valores da política e contexto de documentos."""
    bounds = policy.get("settlement_bounds", {})
    piso_pct = bounds.get("piso_pct_valor_causa", 0.30)
    teto_pct = bounds.get("teto_pct_valor_causa", 0.70)
    piso_abs = bounds.get("piso_absoluto_brl", 1500.00)

    return f"""\
Atue como Calculista Jurídico de Mitigação de Danos do Banco UFMG.

Você receberá dados estruturados do processo E o conteúdo textual dos documentos anexados (Petição Inicial, Contratos, etc).

PREMISSAS DE NEGÓCIO (STRICT):
1. Probabilidade de vitória baixa.
2. Custo Fixo de Litigância Evitado: R$ {piso_abs:,.2f} (Piso Absoluto da Política).
3. Parâmetros de Acordo:
   - Piso Alvo: {piso_pct:.0%} do Valor da Causa.
   - Teto Máximo Permitido: {teto_pct:.0%} do Valor da Causa.

CÁLCULO ESTRATÉGICO:
1. Custo Estimado de Litigar: [Valor da Causa] + Custo Fixo + (Majoração de Danos Morais se sub-assunto = 'golpe').
2. Limite Máximo (intervalo_max): Estritamente travado em 75% do [Custo Estimado de Litigar], respeitando o Teto de {teto_pct:.0%} da Causa.
3. Valor Sugerido (Alvo): Entre {piso_pct:.0%} e 50% do [Valor da Causa], calibrado pelos Argumentos de Defesa e Falhas de Prova identificados nos documentos.

SUA TAREFA:
Analise o texto dos documentos para validar se os "Pontos Fracos" informados são graves o suficiente para subir a proposta ou se há "Pontos Fortes" residuais para manter a proposta no piso.

Retorne estritamente os valores solicitados em formato JSON estruturado.
"""


class ValuationContext(BaseModel):
    valor_da_causa: float
    probabilidade_vitoria: float
    sub_assunto: str
    pontos_fortes: List[str] = Field(default_factory=list)
    pontos_fracos: List[str] = Field(default_factory=list)
    document_texts: str = Field(
        "", description="Texto consolidado de todos os documentos"
    )


class ValuationResult(BaseModel):
    valor_sugerido: float = Field(..., description="Proposta inicial (BRL)")
    intervalo_max: float = Field(..., description="Limite de alçada/break-even (BRL)")
    custo_estimado_litigar: float = Field(
        ..., description="Estimativa de perda total (BRL)"
    )
    justificativa: str = Field(
        ..., description="Fundamentação matemática e documental concisa"
    )


def evaluate_settlement(
    context: ValuationContext, model: str | None = None
) -> ValuationResult:
    """
    Calcula parâmetros de acordo via LLM, integrando dados e textos dos documentos.
    """
    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)
    chosen_model = model or settings.openai_model_reasoning

    policy = load_policy()
    system_prompt = generate_system_prompt(policy)

    input_data = (
        f"--- DADOS DO PROCESSO ---\n"
        f"Valor da Causa: R$ {context.valor_da_causa:.2f}\n"
        f"Probabilidade de Vitória: {context.probabilidade_vitoria:.2%}\n"
        f"Sub-assunto: {context.sub_assunto}\n"
        f"Pontos Fortes Pré-analisados: {', '.join(context.pontos_fortes) if context.pontos_fortes else 'Nenhum'}\n"
        f"Pontos Fracos Pré-analisados: {', '.join(context.pontos_fracos) if context.pontos_fracos else 'Nenhum'}\n\n"
        f"--- CONTEÚDO DOS DOCUMENTOS ---\n"
        f"{context.document_texts}"
    )

    response = client.beta.chat.completions.parse(
        model=chosen_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input_data},
        ],
        response_format=ValuationResult,
        temperature=0.0,
    )

    result = response.choices[0].message.parsed
    if result is None:
        raise ValueError("Falha ao processar a resposta estruturada do Valuator.")

    logger.info(
        "GPT Acordo concluído | Sugerido: R$ %.2f | Teto: R$ %.2f",
        result.valor_sugerido,
        result.intervalo_max,
    )

    return result


def evaluate_from_documents(
    documents: List[IngestedDocument],
    base_context: ValuationContext,
    model: str | None = None,
) -> ValuationResult:
    """
    Consolida textos de documentos injetados e chama o valuator.
    """
    combined_text = "\n\n---\n\n".join(
        f"[Tipo: {doc.doc_type}] Texto:\n{doc.raw_text}" for doc in documents
    )
    base_context.document_texts = combined_text
    return evaluate_settlement(base_context, model=model)


def evaluate_from_pdf_paths(
    paths: List[Path], base_context: ValuationContext, model: str | None = None
) -> ValuationResult:
    """
    Ingere arquivos PDF de caminhos locais e processa o acordo.
    """
    documents = [ingest_pdf(p) for p in paths]
    return evaluate_from_documents(documents, base_context, model=model)
