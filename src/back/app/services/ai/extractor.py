"""Extrator de metadados jurídicos de PDFs via OpenAI Structured Outputs.

Extrai UF, valor da causa e classificação (golpe vs genérico) da petição inicial.
"""
from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Optional

from openai import OpenAI
from pydantic import BaseModel, Field

from app.config import get_settings
from app.core.logging import get_logger
from app.services.ingestion.pdf import IngestedDocument, ingest_pdf

logger = get_logger(__name__)

_SYSTEM_PROMPT = """\
Você é um assistente jurídico especializado em processos cíveis de não reconhecimento de contratação de empréstimo.

Analise o texto fornecido e extraia:

1. **uf**: Estado (Unidade Federativa) onde o processo tramita.
   Procure no cabeçalho do tribunal, número do processo ou menção a cidades/estados.

2. **valor_da_causa**: Valor da causa em reais (número decimal, sem R$ ou separadores de milhar).
   Procure por "valor da causa", "dá à causa o valor de", "atribuindo à causa", etc.

3. **sub_assunto**: Classifique o processo em EXATAMENTE uma das duas categorias:
   - "golpe": há indícios claros de fraude/estelionato — terceiro contratou o empréstimo
     em nome da parte sem o seu conhecimento, usando documentos falsificados ou identidade roubada.
     Sinais: "nunca contratei", "minha identidade foi usada", "não reconheço a assinatura",
     "golpe", "estelionato", "fraude", "falsificação de documentos".
   - "generico": processo de não reconhecimento sem evidência clara de fraude de terceiro —
     pode ser esquecimento, cobrança indevida, contrato de adesão contestado, etc.

Retorne null para campos que não conseguir identificar com confiança.
"""


class SubAssunto(str, Enum):
    GOLPE = "golpe"
    GENERICO = "generico"


class ProcessMetadata(BaseModel):
    uf: Optional[str] = Field(None, description="Sigla do estado (ex: SP, MG, RJ)")
    valor_da_causa: Optional[float] = Field(None, description="Valor da causa em reais")
    sub_assunto: Optional[SubAssunto] = Field(
        None, description="'golpe' se há indício de fraude de terceiro, 'generico' caso contrário"
    )


def extract_metadata(text: str, model: str | None = None) -> ProcessMetadata:
    """Extrai UF, valor da causa e sub-assunto de texto jurídico via OpenAI."""
    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)
    chosen_model = model or settings.openai_model_reasoning

    text_truncated = text[:32_000] if len(text) > 32_000 else text

    response = client.beta.chat.completions.parse(
        model=chosen_model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": f"Texto do processo:\n\n{text_truncated}"},
        ],
        response_format=ProcessMetadata,
        temperature=0.1,
    )

    result: ProcessMetadata = response.choices[0].message.parsed or ProcessMetadata()
    logger.info(
        "Extração concluída — UF=%s | valor_causa=%.2f | sub_assunto=%s",
        result.uf,
        result.valor_da_causa or 0.0,
        result.sub_assunto,
    )
    return result


def extract_from_pdf(path: Path, model: str | None = None) -> ProcessMetadata:
    """Ingere um PDF e extrai metadados do processo."""
    doc: IngestedDocument = ingest_pdf(path)
    return extract_metadata(doc.raw_text, model=model)


def extract_from_documents(docs: list[IngestedDocument], model: str | None = None) -> ProcessMetadata:
    """Extrai metadados de múltiplos documentos de um processo.

    Prioriza a petição inicial; usa demais documentos como contexto.
    """
    peticoes = [d for d in docs if d.doc_type == "PETICAO_INICIAL"]
    outros = [d for d in docs if d.doc_type != "PETICAO_INICIAL"]
    ordered = peticoes + outros

    combined_text = "\n\n---\n\n".join(
        f"[{d.doc_type}]\n{d.raw_text}" for d in ordered
    )
    return extract_metadata(combined_text, model=model)
