"""Downloader de PDFs via Playwright para portais PJe e eSAJ.

Usa automação de browser (Chromium headless) para navegar nos portais dos TJs
e baixar PDFs publicamente acessíveis dos processos.
"""
from __future__ import annotations

import time
from pathlib import Path

from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeout

from .base import BaseDownloader

# Mapeamento tribunal → URL base de consulta pública
CONSULTA_URLS: dict[str, str] = {
    # PJe
    "tjam":  "https://pje.tjam.jus.br/pje/ConsultaPublica/listView.seam",
    "tjal":  "https://pje.tjal.jus.br/pje/ConsultaPublica/listView.seam",
    "tjce":  "https://pje.tjce.jus.br/pje/ConsultaPublica/listView.seam",
    "tjma":  "https://pje.tjma.jus.br/pje/ConsultaPublica/listView.seam",
    "tjpb":  "https://pje.tjpb.jus.br/pje/ConsultaPublica/listView.seam",
    "tjpe":  "https://pje.tjpe.jus.br/pje/ConsultaPublica/listView.seam",
    "tjpi":  "https://pje.tjpi.jus.br/pje/ConsultaPublica/listView.seam",
    "tjrn":  "https://pje.tjrn.jus.br/pje/ConsultaPublica/listView.seam",
    "tjse":  "https://pje.tjse.jus.br/pje/ConsultaPublica/listView.seam",
    "tjto":  "https://pje.tjto.jus.br/pje/ConsultaPublica/listView.seam",
    "tjac":  "https://pje.tjac.jus.br/pje/ConsultaPublica/listView.seam",
    "tjap":  "https://pje.tjap.jus.br/pje/ConsultaPublica/listView.seam",
    "tjro":  "https://pje.tjro.jus.br/pje/ConsultaPublica/listView.seam",
    "tjrr":  "https://pje.tjrr.jus.br/pje/ConsultaPublica/listView.seam",
    "tjpa":  "https://pje.tjpa.jus.br/pje/ConsultaPublica/listView.seam",
    "tjgo":  "https://pje.tjgo.jus.br/pje/ConsultaPublica/listView.seam",
    "tjmt":  "https://pje.tjmt.jus.br/pje/ConsultaPublica/listView.seam",
    "tjms":  "https://pje.tjms.jus.br/pje/ConsultaPublica/listView.seam",
    "tjdft": "https://pje.tjdft.jus.br/pje/ConsultaPublica/listView.seam",
    # eSAJ
    "tjsp":  "https://esaj.tjsp.jus.br/cpopg/open.do",
    "tjba":  "https://esaj.tjba.jus.br/cpopg/open.do",
    "tjsc":  "https://esaj.tjsc.jus.br/cpopg/open.do",
    # eProc
    "tjrs":  "https://eproc.tjrs.jus.br/eproc/externo_controlador.php",
    "tjes":  "https://eproc.tjes.jus.br/eproc/externo_controlador.php",
    # PROJUDI / portal próprio
    "tjmg":  "https://www4.tjmg.jus.br/juridico/sf/proc_resultado2.jsp",
    "tjpr":  "https://projudi.tjpr.jus.br/projudi/",
    "tjrj":  "https://www4.tjrj.jus.br/consultaProcessoWebV2/consultaMov.do",
}

TRIBUNAIS_SUPORTADOS = list(CONSULTA_URLS.keys())


class PlaywrightDownloader(BaseDownloader):
    TRIBUNAIS = TRIBUNAIS_SUPORTADOS

    def __init__(self, output_dir: Path, delay: float = 2.0, headless: bool = True):
        super().__init__(output_dir, delay)
        self.headless = headless

    def download_batch(self, processos: list[dict]) -> dict[str, list[Path]]:
        """Baixa PDFs de uma lista de processos usando uma única sessão do browser."""
        resultados: dict[str, list[Path]] = {}

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=self.headless)
            context = browser.new_context(accept_downloads=True)

            for proc in processos:
                numero = proc.get("numeroProcesso", "")
                tribunal = proc.get("_tribunal", "")
                if not numero or tribunal not in CONSULTA_URLS:
                    continue

                page = context.new_page()
                try:
                    pdfs = self._download_processo(page, numero, tribunal)
                    resultados[numero] = pdfs
                except Exception as e:
                    print(f"  [{tribunal.upper()}] {numero} — erro: {e}")
                    resultados[numero] = []
                finally:
                    page.close()
                    time.sleep(self.delay)

            browser.close()

        return resultados

    def download(self, numero_processo: str, tribunal: str) -> list[Path]:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=self.headless)
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()
            try:
                return self._download_processo(page, numero_processo, tribunal)
            finally:
                browser.close()

    def _download_processo(self, page: Page, numero: str, tribunal: str) -> list[Path]:
        dest_dir = self._processo_dir(numero, tribunal)
        base_url = CONSULTA_URLS[tribunal]
        saved: list[Path] = []

        if tribunal in ("tjsp", "tjba", "tjsc"):
            saved = self._download_esaj(page, numero, tribunal, base_url, dest_dir)
        elif tribunal in ("tjrs", "tjes"):
            saved = self._download_eproc(page, numero, tribunal, base_url, dest_dir)
        else:
            saved = self._download_pje(page, numero, tribunal, base_url, dest_dir)

        return saved

    # ── PJe ──────────────────────────────────────────────────────────────────

    def _download_pje(self, page: Page, numero: str, tribunal: str, base_url: str, dest_dir: Path) -> list[Path]:
        saved: list[Path] = []
        try:
            page.goto(base_url, timeout=20_000, wait_until="domcontentloaded")
            # Preenche o campo de número do processo
            campo = page.locator("input[id*='numeroProcesso'], input[name*='numeroProcesso']").first
            campo.fill(numero)
            page.keyboard.press("Enter")
            page.wait_for_timeout(3000)

            # Clica no processo encontrado
            resultado = page.locator("a[href*='detalhe'], a[href*='processo']").first
            resultado.click(timeout=8000)
            page.wait_for_timeout(2000)

            # Busca links de documentos
            pdf_links = page.locator("a[href*='pdf'], a[href*='documento'], a[href*='arquivo']").all()
            for i, link in enumerate(pdf_links[:10], 1):
                href = link.get_attribute("href") or ""
                if not href:
                    continue
                if not href.startswith("http"):
                    from urllib.parse import urljoin
                    href = urljoin(base_url, href)
                with page.expect_download(timeout=15_000) as dl_info:
                    link.click()
                download = dl_info.value
                dest = dest_dir / f"documento_{i:02d}.pdf"
                download.save_as(str(dest))
                saved.append(dest)
                print(f"    [PJe/{tribunal}] Salvo: documento_{i:02d}.pdf")
                page.wait_for_timeout(int(self.delay * 1000))

        except PlaywrightTimeout:
            print(f"    [PJe/{tribunal}] Timeout — portal lento ou processo não encontrado")
        except Exception as e:
            print(f"    [PJe/{tribunal}] {e}")

        return saved

    # ── eSAJ ─────────────────────────────────────────────────────────────────

    def _download_esaj(self, page: Page, numero: str, tribunal: str, base_url: str, dest_dir: Path) -> list[Path]:
        saved: list[Path] = []
        try:
            url = f"{base_url}?processo.numero={numero}"
            page.goto(url, timeout=20_000, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

            # Botão da pasta digital
            pasta = page.locator("a[href*='pastadigital'], a:has-text('Autos Digitais'), a:has-text('Pasta Digital')").first
            pasta.click(timeout=8000)
            page.wait_for_timeout(2000)

            pdf_links = page.locator("a[href*='getPDF'], a[href*='getArquivo']").all()
            for i, link in enumerate(pdf_links[:10], 1):
                with page.expect_download(timeout=15_000) as dl_info:
                    link.click()
                download = dl_info.value
                dest = dest_dir / f"documento_{i:02d}.pdf"
                download.save_as(str(dest))
                saved.append(dest)
                print(f"    [eSAJ/{tribunal}] Salvo: documento_{i:02d}.pdf")
                page.wait_for_timeout(int(self.delay * 1000))

        except PlaywrightTimeout:
            print(f"    [eSAJ/{tribunal}] Timeout")
        except Exception as e:
            print(f"    [eSAJ/{tribunal}] {e}")

        return saved

    # ── eProc ────────────────────────────────────────────────────────────────

    def _download_eproc(self, page: Page, numero: str, tribunal: str, base_url: str, dest_dir: Path) -> list[Path]:
        saved: list[Path] = []
        try:
            url = f"{base_url}?acao=processo_consulta_publica&num_processo={numero}"
            page.goto(url, timeout=20_000, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

            pdf_links = page.locator("a[href*='documento'], a[href*='pdf']").all()
            for i, link in enumerate(pdf_links[:10], 1):
                with page.expect_download(timeout=15_000) as dl_info:
                    link.click()
                download = dl_info.value
                dest = dest_dir / f"documento_{i:02d}.pdf"
                download.save_as(str(dest))
                saved.append(dest)
                print(f"    [eProc/{tribunal}] Salvo: documento_{i:02d}.pdf")
                page.wait_for_timeout(int(self.delay * 1000))

        except PlaywrightTimeout:
            print(f"    [eProc/{tribunal}] Timeout")
        except Exception as e:
            print(f"    [eProc/{tribunal}] {e}")

        return saved
