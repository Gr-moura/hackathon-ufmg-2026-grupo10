from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ProcessoCreate(BaseModel):
    numero_processo: str = Field(..., max_length=60)
    valor_causa: float | None = None


class DocumentoResponse(BaseModel):
    id: uuid.UUID
    doc_type: str
    original_filename: str
    page_count: int
    parse_errors: list | None = None

    model_config = {"from_attributes": True}


class ProcessoResponse(BaseModel):
    id: uuid.UUID
    numero_processo: str
    advogado_id: str
    valor_causa: float | None
    status: str
    created_at: datetime
    documentos: list[DocumentoResponse] = []

    model_config = {"from_attributes": True}


class ProcessoListItem(BaseModel):
    id: uuid.UUID
    numero_processo: str
    status: str
    created_at: datetime
    n_documentos: int = 0

    model_config = {"from_attributes": True}
