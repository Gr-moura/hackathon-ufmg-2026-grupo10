"""Downloader para tribunais que usam o sistema eSAJ (e-SAJ / SAJ).

Cobre: TJSP, TJBA, TJSC, TJMG (parcial), TJPR, TJRJ.
"""
from __future__ import annotations

import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from .base import BaseDownloader

TRIBUNAIS_ESAJ = ["tjsp", "tjba", "tjsc", "tjmg", "tjpr", "tjrj"]

ESAJ_HOSTS: dict[str, str] = {
    "tjsp": "esaj.tjsp.jus.br",
    "tjba": "esaj.tjba.jus.br",
    "tjsc": "esaj.tjsc.jus.br",
    "tjmg": "www4.tjmg.jus.br",
    "tjpr": "projudi.tjpr.jus.br",
    "tjrj": "www4.tjrj.jus.br",
}

# Caminhos de consulta pública por sistema
CONSULTA_PATHS: dict[str, str] = {
    "tjsp": "/cpopg/open.do",
    "tjba": "/cpopg/open.do",
    "tjsc": "/cpopg/open.do",
    "tjmg": "/juridico/procmov/movimentacaoProcesso.do",
    "tjpr": "/projudi/grau1/processo.do",
    "tjrj": "/consulta/processo/ListaMovimentos.do",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class ESAJDownloader(BaseDownloader):
    TRIBUNAIS = TRIBUNAIS_ESAJ

    def __init__(self, output_dir: Path, delay: float = 2.5):
        super().__init__(output_dir, delay)
        self._session = requests.Session()
        self._session.headers.update(HEADERS)

    def download(self, numero_processo: str, tribunal: str) -> list[Path]:
        host = ESAJ_HOSTS.get(tribunal)
        path = CONSULTA_PATHS.get(tribunal)
        if not host or not path:
            return []

        dest_dir = self._processo_dir(numero_processo, tribunal)
        saved: list[Path] = []

        # 1. Consulta pública
        params = {"processo.codigo": numero_processo, "processo.foro": "1"}
        consulta_url = f"https://{host}{path}"

        try:
            resp = self._session.get(consulta_url, params=params, timeout=20)
            resp.raise_for_status()
        except Exception as e:
            print(f"    [eSAJ/{tribunal}] Falha na consulta: {e}")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")

        # 2. Pasta digital — link para documentos
        pasta_link = self._find_pasta_link(soup, host)
        if not pasta_link:
            print(f"    [eSAJ/{tribunal}] Pasta digital não encontrada")
            return []

        time.sleep(self.delay)
        try:
            pasta_resp = self._session.get(pasta_link, timeout=20)
            pasta_resp.raise_for_status()
            pasta_soup = BeautifulSoup(pasta_resp.text, "html.parser")
        except Exception as e:
            print(f"    [eSAJ/{tribunal}] Falha ao abrir pasta digital: {e}")
            return []

        # 3. Download dos PDFs listados na pasta digital
        pdf_links = self._extract_pdf_links(pasta_soup, host)
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
                print(f"    [eSAJ/{tribunal}] Salvo: {filename}")
            except Exception as e:
                print(f"    [eSAJ/{tribunal}] Erro ao baixar doc {i}: {e}")

        return saved

    def _find_pasta_link(self, soup: BeautifulSoup, host: str) -> str | None:
        for tag in soup.find_all("a", href=True):
            href: str = tag["href"]
            if "pastadigital" in href or "pasta" in href.lower():
                if not href.startswith("http"):
                    href = f"https://{host}{href}"
                return href
        return None

    def _extract_pdf_links(self, soup: BeautifulSoup, host: str) -> list[str]:
        links: list[str] = []
        for tag in soup.find_all("a", href=True):
            href: str = tag["href"]
            if "getPDF" in href or "getArquivo" in href or href.endswith(".pdf"):
                if not href.startswith("http"):
                    href = f"https://{host}{href}"
                links.append(href)
        return links
