"""Interface base para downloaders de PDF por sistema judicial."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class BaseDownloader(ABC):
    """Downloader base — cada sistema judicial herda e implementa _fetch_pdfs."""

    # Tribunais que usam este sistema (sobrescrever na subclasse)
    TRIBUNAIS: list[str] = []

    def __init__(self, output_dir: Path, delay: float = 2.0):
        self.output_dir = output_dir
        self.delay = delay

    @abstractmethod
    def download(self, numero_processo: str, tribunal: str) -> list[Path]:
        """Baixa os PDFs de um processo e retorna os caminhos salvos."""
        ...

    def _processo_dir(self, numero_processo: str, tribunal: str) -> Path:
        safe = numero_processo.replace("/", "-").replace(" ", "_")
        d = self.output_dir / tribunal.upper() / safe
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _save(self, content: bytes, dest: Path) -> Path:
        dest.write_bytes(content)
        return dest
