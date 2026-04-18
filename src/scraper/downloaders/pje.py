"""Downloader para tribunais que usam o sistema PJe (Processo Judicial Eletrônico).

Cobre: TJAM, TJAL, TJCE, TJMA, TJPB, TJPE, TJPI, TJRN, TJSE, TJTO,
       TJAC, TJAP, TJRO, TJRR, TJPA, TJGO, TJMT, TJMS, TJDFT e outros.
"""
from __future__ import annotations

import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from .base import BaseDownloader

TRIBUNAIS_PJE = [
    "tjac", "tjal", "tjam", "tjap", "tjce", "tjdft", "tjgo",
    "tjma", "tjms", "tjmt", "tjpa", "tjpb", "tjpe", "tjpi",
    "tjrn", "tjro", "tjrr", "tjse", "tjto",
]

# Padrão de URL de consulta pública por tribunal
PJE_HOSTS: dict[str, str] = {
    "tjam":  "pje.tjam.jus.br",
    "tjal":  "pje.tjal.jus.br",
    "tjce":  "pje.tjce.jus.br",
    "tjma":  "pje.tjma.jus.br",
    "tjpb":  "pje.tjpb.jus.br",
    "tjpe":  "pje.tjpe.jus.br",
    "tjpi":  "pje.tjpi.jus.br",
    "tjrn":  "pje.tjrn.jus.br",
    "tjse":  "pje.tjse.jus.br",
    "tjto":  "pje.tjto.jus.br",
    "tjac":  "pje.tjac.jus.br",
    "tjap":  "pje.tjap.jus.br",
    "tjro":  "pje.tjro.jus.br",
    "tjrr":  "pje.tjrr.jus.br",
    "tjpa":  "pje.tjpa.jus.br",
    "tjgo":  "pje.tjgo.jus.br",
    "tjmt":  "pje.tjmt.jus.br",
    "tjms":  "pje.tjms.jus.br",
    "tjdft": "pje.tjdft.jus.br",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class PJeDownloader(BaseDownloader):
    TRIBUNAIS = TRIBUNAIS_PJE

    def __init__(self, output_dir: Path, delay: float = 2.0):
        super().__init__(output_dir, delay)
        self._session = requests.Session()
        self._session.headers.update(HEADERS)

    def download(self, numero_processo: str, tribunal: str) -> list[Path]:
        host = PJE_HOSTS.get(tribunal)
        if not host:
            return []

        saved: list[Path] = []
        dest_dir = self._processo_dir(numero_processo, tribunal)

        # 1. Consulta pública — obtém a lista de documentos
        numero_limpo = numero_processo.replace(".", "").replace("-", "")
        consulta_url = (
            f"https://{host}/pje/ConsultaPublica/listView.seam"
            f"?numeroProcesso={numero_processo}"
        )

        try:
            resp = self._session.get(consulta_url, timeout=20)
            resp.raise_for_status()
        except Exception as e:
            print(f"    [PJe/{tribunal}] Falha na consulta: {e}")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")

        # 2. Encontra links de documentos (PDF) na pasta digital
        doc_links = self._extract_doc_links(soup, host)
        if not doc_links:
            print(f"    [PJe/{tribunal}] Nenhum documento público encontrado")
            return []

        for i, url in enumerate(doc_links, 1):
            time.sleep(self.delay)
            try:
                pdf_resp = self._session.get(url, timeout=30, stream=True)
                pdf_resp.raise_for_status()
                content_type = pdf_resp.headers.get("Content-Type", "")
                if "pdf" not in content_type.lower() and not url.endswith(".pdf"):
                    continue
                filename = f"documento_{i:02d}.pdf"
                path = self._save(pdf_resp.content, dest_dir / filename)
                saved.append(path)
                print(f"    [PJe/{tribunal}] Salvo: {filename}")
            except Exception as e:
                print(f"    [PJe/{tribunal}] Erro ao baixar doc {i}: {e}")

        return saved

    def _extract_doc_links(self, soup: BeautifulSoup, host: str) -> list[str]:
        links: list[str] = []
        for tag in soup.find_all("a", href=True):
            href: str = tag["href"]
            if "pdf" in href.lower() or "documento" in href.lower() or "arquivo" in href.lower():
                if not href.startswith("http"):
                    href = f"https://{host}{href}"
                links.append(href)
        return links
