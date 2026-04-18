"""Scraper principal — busca processos via DataJud e baixa PDFs dos TJs.

Uso:
    python src/scraper/main.py
    python src/scraper/main.py --max-por-tribunal 50 --output data/scraped
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.scraper.datajud import buscar_todos_tribunais
from src.scraper.downloaders.playwright_pje import PlaywrightDownloader, TRIBUNAIS_SUPORTADOS


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Scraper de processos judiciais — DataJud + TJs")
    p.add_argument("--max-por-tribunal", type=int, default=40,
                   help="Máximo de processos por tribunal (padrão: 40)")
    p.add_argument("--output", type=str, default="data/scraped",
                   help="Pasta de saída dos PDFs (padrão: data/scraped)")
    p.add_argument("--delay", type=float, default=2.0,
                   help="Segundos de espera entre requisições (padrão: 2.0)")
    p.add_argument("--so-datajud", action="store_true",
                   help="Apenas busca metadados no DataJud, sem baixar PDFs")
    p.add_argument("--json", type=str, default="",
                   help="Usa um JSON já existente do DataJud em vez de buscar novamente")
    p.add_argument("--visible", action="store_true",
                   help="Abre o browser visível (útil para debug)")
    p.add_argument("--salvar-json", type=str, default="",
                   help="Salva metadados do DataJud em arquivo JSON")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.json:
        processos = json.loads(Path(args.json).read_text())
        print(f"Carregados {len(processos)} processos de {args.json}\n")
    else:
        print(f"=== Buscando processos no DataJud ===")
        print(f"  Máximo por tribunal: {args.max_por_tribunal}")
        processos = buscar_todos_tribunais(
            max_por_tribunal=args.max_por_tribunal,
            delay=args.delay,
        )
        print(f"\nTotal encontrado: {len(processos)} processo(s)\n")

    if args.salvar_json:
        Path(args.salvar_json).write_text(json.dumps(processos, ensure_ascii=False, indent=2))
        print(f"Metadados salvos em: {args.salvar_json}\n")

    if args.so_datajud:
        return

    print("=== Baixando PDFs dos TJs via browser ===")
    suportados = [p for p in processos if p.get("_tribunal") in TRIBUNAIS_SUPORTADOS]
    ignorados = len(processos) - len(suportados)
    if ignorados:
        print(f"  {ignorados} processo(s) de tribunais não suportados ignorados")

    downloader = PlaywrightDownloader(output_dir, delay=args.delay, headless=not args.visible)
    resultados = downloader.download_batch(suportados)

    total_pdfs = sum(len(v) for v in resultados.values())
    falhas = sum(1 for v in resultados.values() if not v)

    print(f"\n=== Concluído ===")
    print(f"  PDFs baixados    : {total_pdfs}")
    print(f"  Processos sem PDF: {falhas}/{len(suportados)}")
    print(f"  Pasta de saída   : {output_dir.resolve()}")


if __name__ == "__main__":
    main()
