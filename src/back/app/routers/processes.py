import shutil
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.exceptions import DocumentParsingError
from app.core.logging import get_logger
from app.db.models.documento import Documento
from app.db.models.processo import Processo
from app.deps import CurrentUser, DbDep
from app.schemas.process import ProcessoListItem, ProcessoResponse
from app.services.ai.extractor import ProcessMetadata, extract_metadata
from app.services.ingestion.pdf import IngestedDocument, ingest_pdf

router = APIRouter(prefix="/processes", tags=["processes"])
logger = get_logger(__name__)


def _storage_dir(base: str, processo_id: uuid.UUID) -> Path:
    p = Path(base) / "raw" / str(processo_id)
    p.mkdir(parents=True, exist_ok=True)
    return p


@router.post("", response_model=ProcessoResponse, status_code=status.HTTP_201_CREATED)
async def create_processo(
    db: DbDep,
    current_user: CurrentUser,
    numero_processo: Annotated[str, Form()],
    valor_causa: Annotated[float | None, Form()] = None,
    files: Annotated[list[UploadFile], File()] = [],
) -> ProcessoResponse:
    from app.config import get_settings

    settings = get_settings()
    processo = Processo(
        numero_processo=numero_processo,
        advogado_id=current_user["sub"],
        valor_causa=valor_causa,
        status="processando",
    )
    db.add(processo)
    db.flush()  # gera o ID antes de salvar arquivos

    storage = _storage_dir(settings.data_dir, processo.id)
    documentos: list[Documento] = []

    for upload in files:
        filename = upload.filename or "documento.pdf"
        file_path = storage / filename

        # Salva o arquivo em disco
        with file_path.open("wb") as f:
            shutil.copyfileobj(upload.file, f)

        # Ingere o PDF
        parse_errors: list[dict] = []
        raw_text: str | None = None
        tables: list | None = None
        page_count = 0
        doc_type = "OUTRO"

        try:
            ingested = ingest_pdf(file_path)
            raw_text = ingested.raw_text
            tables = ingested.tables or None
            page_count = ingested.page_count
            doc_type = ingested.doc_type
            parse_errors = ingested.parse_errors
        except DocumentParsingError as e:
            logger.warning("Falha ao ingerir '%s': %s", filename, e.reason)
            parse_errors = [{"stage": "ingestion", "reason": e.reason, "recoverable": e.recoverable}]

        doc = Documento(
            processo_id=processo.id,
            doc_type=doc_type,
            original_filename=filename,
            storage_path=str(file_path),
            raw_text=raw_text,
            tables=tables,
            page_count=page_count,
            parse_errors=parse_errors or None,
        )
        db.add(doc)
        documentos.append(doc)

    # Extrai features (UF, sub_assunto, valor_da_causa) dos documentos ingeridos
    ingested_docs = [d for d in documentos if d.raw_text]
    if ingested_docs:
        try:
            combined_text = "\n\n---\n\n".join(
                f"[{d.doc_type}]\n{d.raw_text}"
                for d in sorted(ingested_docs, key=lambda x: 0 if x.doc_type == "PETICAO_INICIAL" else 1)
            )
            meta: ProcessMetadata = extract_metadata(combined_text)
            processo.metadata_extraida = {
                "uf": meta.uf,
                "sub_assunto": meta.sub_assunto.value if meta.sub_assunto else None,
                "valor_da_causa": meta.valor_da_causa,
            }
            if meta.valor_da_causa and not processo.valor_causa:
                processo.valor_causa = meta.valor_da_causa
        except Exception as exc:
            logger.warning("Extração de metadados falhou: %s", exc)

    processo.status = "pendente"
    db.commit()
    db.refresh(processo)

    logger.info(
        "Processo criado: %s | %d documentos | advogado=%s",
        processo.numero_processo,
        len(documentos),
        # Mascara o ID para não logar dados sensíveis completos
        current_user["sub"][:8] + "...",
    )
    return ProcessoResponse.model_validate(processo)


@router.get("", response_model=list[ProcessoListItem])
def list_processos(db: DbDep, current_user: CurrentUser) -> list[ProcessoListItem]:
    processos = (
        db.query(Processo)
        .filter(Processo.advogado_id == current_user["sub"])
        .order_by(Processo.created_at.desc())
        .limit(100)
        .all()
    )
    return [
        ProcessoListItem(
            id=p.id,
            numero_processo=p.numero_processo,
            status=p.status,
            created_at=p.created_at,
            n_documentos=len(p.documentos),
        )
        for p in processos
    ]


@router.get("/{processo_id}", response_model=ProcessoResponse)
def get_processo(processo_id: uuid.UUID, db: DbDep, current_user: CurrentUser) -> ProcessoResponse:
    processo = db.get(Processo, processo_id)
    if not processo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processo não encontrado")
    return ProcessoResponse.model_validate(processo)
