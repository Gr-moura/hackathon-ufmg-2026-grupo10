"""Ingestão de PDFs nativos com fallback automático para OCR."""
from dataclasses import dataclass, field
from pathlib import Path

import pdfplumber

from app.core.exceptions import DocumentParsingError
from app.core.logging import get_logger

logger = get_logger(__name__)

# Threshold: se o texto extraído tiver menos que isso, assume PDF escaneado
_OCR_THRESHOLD = 200

# Mapeamento de palavras-chave do nome do arquivo → doc_type
_FILENAME_TYPE_MAP: list[tuple[list[str], str]] = [
    (["autos", "peticao", "inicial", "procuracao"], "PETICAO_INICIAL"),
    (["procuracao"], "PROCURACAO"),
    (["contrato"], "CONTRATO"),
    (["extrato", "bancario"], "EXTRATO"),
    (["bacen", "comprovante", "credito"], "COMPROVANTE_CREDITO"),
    (["dossie", "veritas", "grafotec"], "DOSSIE"),
    (["demonstrativo", "divida", "evolucao"], "DEMONSTRATIVO_DIVIDA"),
    (["laudo", "referenciado"], "LAUDO_REFERENCIADO"),
]


@dataclass
class IngestedDocument:
    raw_text: str
    tables: list[list] = field(default_factory=list)
    page_count: int = 0
    doc_type: str = "OUTRO"
    parse_errors: list[dict] = field(default_factory=list)


def infer_doc_type(filename: str) -> str:
    """Infere o tipo do documento pelo nome do arquivo."""
    stem = filename.lower().replace("-", "_").replace(" ", "_")
    for keywords, doc_type in _FILENAME_TYPE_MAP:
        if any(kw in stem for kw in keywords):
            return doc_type
    return "OUTRO"


def ingest_pdf(path: Path) -> IngestedDocument:
    """Extrai texto e tabelas de um PDF.

    Aplica OCR automaticamente quando o texto nativo é insuficiente (< 200 chars).
    Nunca retorna documento vazio sem flag — erros ficam em parse_errors.
    """
    doc_type = infer_doc_type(path.name)
    parse_errors: list[dict] = []

    # Extração nativa via pdfplumber
    try:
        with pdfplumber.open(path) as pdf:
            page_count = len(pdf.pages)
            text_parts: list[str] = []
            all_tables: list[list] = []

            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text_parts.append(page_text)

                for table in page.extract_tables() or []:
                    if table:
                        all_tables.append(table)

            raw_text = "\n".join(text_parts).strip()

    except Exception as e:
        raise DocumentParsingError(path.name, "pdf_corrompido", recoverable=False) from e

    # Fallback para OCR se o texto nativo for insuficiente
    if len(raw_text) < _OCR_THRESHOLD:
        logger.info("Texto insuficiente em '%s' (%d chars) — ativando OCR", path.name, len(raw_text))
        try:
            from app.services.ingestion.ocr import ocr_pdf
            raw_text = ocr_pdf(path).strip()
        except DocumentParsingError as ocr_err:
            parse_errors.append({"stage": "ocr", "reason": ocr_err.reason})
            logger.warning("OCR falhou para '%s': %s", path.name, ocr_err.reason)

    if not raw_text:
        raise DocumentParsingError(path.name, "documento_vazio", recoverable=False)

    return IngestedDocument(
        raw_text=raw_text,
        tables=all_tables,
        page_count=page_count,
        doc_type=doc_type,
        parse_errors=parse_errors,
    )
