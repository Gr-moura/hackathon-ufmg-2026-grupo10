from .pje import PJeDownloader, TRIBUNAIS_PJE
from .esaj import ESAJDownloader, TRIBUNAIS_ESAJ
from .eproc import EProcDownloader, TRIBUNAIS_EPROC
from .base import BaseDownloader


def get_downloader(tribunal: str, output_dir, delay: float = 2.0) -> BaseDownloader | None:
    """Retorna o downloader adequado para o tribunal, ou None se não suportado."""
    if tribunal in TRIBUNAIS_PJE:
        return PJeDownloader(output_dir, delay)
    if tribunal in TRIBUNAIS_ESAJ:
        return ESAJDownloader(output_dir, delay)
    if tribunal in TRIBUNAIS_EPROC:
        return EProcDownloader(output_dir, delay)
    return None
