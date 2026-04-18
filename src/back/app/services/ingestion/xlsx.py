"""Ingestão de arquivos XLSX (base de sentenças históricas)."""
from pathlib import Path

import pandas as pd

from app.core.exceptions import DocumentParsingError
from app.core.logging import get_logger

logger = get_logger(__name__)

# Mapeamento de colunas esperadas → nomes canônicos
_COLUMN_MAP = {
    "número do processo": "numero_caso",
    "numero do processo": "numero_caso",
    "uf": "uf",
    "assunto": "assunto",
    "sub-assunto": "sub_assunto",
    "subassunto": "sub_assunto",
    "resultado macro": "resultado_macro",
    "resultado_macro": "resultado_macro",
    "resultado micro": "resultado_micro",
    "resultado_micro": "resultado_micro",
    "valor da causa": "valor_causa",
    "valor_causa": "valor_causa",
    "valor da condenação": "valor_condenacao",
    "valor condenacao": "valor_condenacao",
    "valor_condenacao": "valor_condenacao",
}


def load_sentencas(path: Path) -> pd.DataFrame:
    """Carrega e normaliza o XLSX de sentenças históricas.

    Retorna DataFrame com colunas canônicas definidas em _COLUMN_MAP.
    """
    try:
        df = pd.read_excel(path, dtype=str)
    except Exception as e:
        raise DocumentParsingError(path.name, "xlsx_corrompido", recoverable=False) from e

    # Normaliza nomes de colunas
    df.columns = [c.strip().lower() for c in df.columns]
    df.rename(columns=_COLUMN_MAP, inplace=True)

    # Converte colunas numéricas
    for col in ("valor_causa", "valor_condenacao"):
        if col in df.columns:
            df[col] = (
                df[col]
                .str.replace(r"[R$\s\.]", "", regex=True)
                .str.replace(",", ".")
                .pipe(pd.to_numeric, errors="coerce")
            )

    logger.info("XLSX carregado: %d linhas de '%s'", len(df), path.name)
    return df
