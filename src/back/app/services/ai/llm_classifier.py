"""Classificador LLM ACORDO vs DEFESA (gpt-4o-mini via Structured Outputs).

Usa o mesmo modelo `openai_model_reasoning` do extractor e do valuator.
Recebe metadados + fatores documentais + top-k casos similares e devolve:
  - `decisao`: ACORDO ou DEFESA
  - `confidence`: [0, 1] — confiança do modelo
  - `rationale`: justificativa curta (<= 400 chars)
  - `fatores`: lista de fatores extras pró-acordo ou pró-defesa identificados

Comportamento offline:
  - Sem `OPENAI_API_KEY` ou em falha de chamada, devolve `None`; o pipeline
    cai no heurístico determinístico `_decisao()`.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


_SYSTEM_PROMPT = """\
Você é um classificador jurídico do Banco UFMG.

Dado o contexto de um processo civil de não-reconhecimento de contratação de
empréstimo, decida se a estratégia deve ser:
  - "ACORDO": propor acordo; o banco tende a perder em juízo OU a economia de
    litigar é compensatória.
  - "DEFESA": contestar em juízo; há documentação robusta e histórico favorável.

Regras de negócio:
  1. Se a petição alega "golpe" (fraude por terceiro) e faltam Contrato ou
     Comprovante de Crédito, tende a ACORDO.
  2. Se a documentação do banco está completa (Contrato + Extrato + Comprovante
     + Dossiê) e o histórico de casos similares mostra taxa alta de êxito em
     juízo, tende a DEFESA.
  3. Se `probabilidade_vitoria_historica` < 0.25, tende a ACORDO.
  4. Nunca recomende DEFESA quando houver `red flags` graves (assinatura
     evidentemente falsificada, ausência total de comprovante de crédito).
  5. Sua `confidence` deve refletir a robustez da evidência — menor quando há
     poucos casos similares ou sub_assunto não classificado.

Responda **apenas** no formato estruturado solicitado.
"""


class ClassifierInput(BaseModel):
    uf: str | None = None
    sub_assunto: str | None = None
    valor_causa: float | None = None
    doc_types_presentes: list[str] = Field(default_factory=list)
    fatores_pro_acordo: list[str] = Field(default_factory=list)
    fatores_pro_defesa: list[str] = Field(default_factory=list)
    penalty_documental: float = 0.0
    probabilidade_vitoria_historica: float = 0.30
    casos_similares: list[dict[str, Any]] = Field(default_factory=list)
    trechos_peticao: list[str] = Field(default_factory=list)


class ClassifierOutput(BaseModel):
    decisao: str = Field(..., description="ACORDO ou DEFESA")
    confidence: float = Field(..., ge=0.0, le=1.0)
    rationale: str = Field(..., max_length=600)
    fatores_extra_pro_acordo: list[str] = Field(default_factory=list)
    fatores_extra_pro_defesa: list[str] = Field(default_factory=list)


def _format_casos(casos: list[dict[str, Any]]) -> str:
    if not casos:
        return "Nenhum caso similar encontrado na base."
    lines = []
    for i, c in enumerate(casos, 1):
        # Formato agregado (estatísticas por UF/sub_assunto)
        if "n_amostras" in c or "win_rate" in c:
            lines.append(
                f"{i}. n_amostras={c.get('n_amostras', 0)} "
                f"| UF={c.get('uf', '?')} "
                f"| sub_assunto={c.get('sub_assunto', '?')} "
                f"| win_rate={c.get('win_rate', 'N/A')}"
            )
        else:
            # Formato per-caso
            lines.append(
                f"{i}. nº={c.get('numero_caso', 'N/A')} | UF={c.get('uf', '?')} "
                f"| sub_assunto={c.get('sub_assunto', '?')} "
                f"| resultado={c.get('resultado_macro', '?')}/"
                f"{c.get('resultado_micro', '?')} "
                f"| valor_causa={c.get('valor_causa', 'N/A')} "
                f"| condenação={c.get('valor_condenacao', 'N/A')}"
            )
    return "\n".join(lines)


def _format_user_message(inp: ClassifierInput) -> str:
    valor_line = (
        f"Valor da causa: R$ {inp.valor_causa:.2f}"
        if inp.valor_causa
        else "Valor da causa: não identificado"
    )
    docs_line = ", ".join(inp.doc_types_presentes) or "nenhum"
    pro_acordo = ", ".join(inp.fatores_pro_acordo) or "nenhum"
    pro_defesa = ", ".join(inp.fatores_pro_defesa) or "nenhum"
    trechos_block = (
        "\n".join(f"> {t}" for t in inp.trechos_peticao[:3])
        if inp.trechos_peticao
        else "(indisponível)"
    )

    return (
        "--- METADADOS ---\n"
        f"UF: {inp.uf or 'N/A'}\n"
        f"Sub-assunto: {inp.sub_assunto or 'N/A'}\n"
        f"{valor_line}\n"
        f"Documentos presentes: {docs_line}\n"
        f"Penalidade documental acumulada: {inp.penalty_documental:+.2f}\n"
        f"Probabilidade de vitória (histórico): {inp.probabilidade_vitoria_historica:.0%}\n\n"
        "--- FATORES IDENTIFICADOS ---\n"
        f"Pró-acordo: {pro_acordo}\n"
        f"Pró-defesa: {pro_defesa}\n\n"
        f"--- CASOS SIMILARES (top-{len(inp.casos_similares)}) ---\n"
        f"{_format_casos(inp.casos_similares)}\n\n"
        "--- TRECHOS DA PETIÇÃO INICIAL ---\n"
        f"{trechos_block}"
    )


def classify(inp: ClassifierInput, model: str | None = None) -> ClassifierOutput | None:
    """Classifica a decisão estratégica via LLM. Devolve `None` em falha/sem key."""
    settings = get_settings()
    if not settings.openai_api_key:
        logger.info("Classifier: sem OPENAI_API_KEY — fallback para heurística")
        return None

    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        chosen_model = model or settings.openai_model_reasoning

        response = client.beta.chat.completions.parse(
            model=chosen_model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": _format_user_message(inp)},
            ],
            response_format=ClassifierOutput,
            temperature=0.0,
        )
        parsed = response.choices[0].message.parsed
        if parsed is None:
            logger.warning("Classifier: resposta estruturada vazia")
            return None
        # Normaliza a decisão para ACORDO/DEFESA mesmo se o modelo variar caixa
        parsed.decisao = parsed.decisao.strip().upper()
        if parsed.decisao not in ("ACORDO", "DEFESA"):
            logger.warning(
                "Classifier: decisao inválida '%s' — descartando saída",
                parsed.decisao,
            )
            return None
        logger.info(
            "Classifier concluído: %s | confidence=%.2f",
            parsed.decisao,
            parsed.confidence,
        )
        return parsed
    except Exception as exc:  # noqa: BLE001
        logger.warning("Classifier falhou (%s) — fallback para heurística", exc)
        return None
