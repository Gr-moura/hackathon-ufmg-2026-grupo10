"""Downloader para tribunais que usam o sistema eProc.

Cobre: TJRS, TJES, TJRR (parcial).
"""
from __future__ import annotations

import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from .base import BaseDownloader

TRIBUNAIS_EPROC = ["tjrs", "tjes"]

EPROC_HOSTS: dict[str, str] = {
    "tjrs": "eproc.tjrs.jus.br",
    "tjes": "eproc.tjes.jus.br",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class EProcDownloader(BaseDownloader):
    TRIBUNAIS = TRIBUNAIS_EPROC

    def __init__(self, output_dir: Path, delay: float = 2.0):
        super().__init__(output_dir, delay)
        self._session = requests.Session()
        self._session.headers.update(HEADERS)

    def download(self, numero_processo: str, tribunal: str) -> list[Path]:
        host = EPROC_HOSTS.get(tribunal)
        if not host:
            return []

        dest_dir = self._processo_dir(numero_processo, tribunal)
        saved: list[Path] = []

        consulta_url = (
            f"https://{host}/eproc/externo_controlador.php"
            f"?acao=processo_consulta_publica&num_processo={numero_processo}"
        )

        try:
            resp = self._session.get(consulta_url, timeout=20)
            resp.raise_for_status()
        except Exception as e:
            print(f"    [eProc/{tribunal}] Falha na consulta: {e}")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        pdf_links = self._extract_pdf_links(soup, host)

        for i, url in enumerate(pdf_links, 1):
            time.sleep(self.delay)
            try:
                pdf_resp = self._session.get(url, timeout=30, stream=True)
                pdf_resp.raise_for_status()
                content_type = pdf_resp.headers.get("Content-Type", "")
                if "pdf" not in content_type.lower():
                    continue
                filename = f"documento_{i:02d}.pdf"
                path_saved = self._save(pdf_resp.content, dest_dir / filename)
                saved.append(path_saved)
                print(f"    [eProc/{tribunal}] Salvo: {filename}")
            except Exception as e:
                print(f"    [eProc/{tribunal}] Erro ao baixar doc {i}: {e}")

        return saved

    def _extract_pdf_links(self, soup: BeautifulSoup, host: str) -> list[str]:
        links: list[str] = []
        for tag in soup.find_all("a", href=True):
            href: str = tag["href"]
            if "documento" in href.lower() or "pdf" in href.lower() or "arquivo" in href.lower():
                if not href.startswith("http"):
                    href = f"https://{host}{href}"
                links.append(href)
        return links
