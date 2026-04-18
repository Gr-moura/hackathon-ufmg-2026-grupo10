"""Script de teste do extrator — roda sobre os PDFs de data/ sem precisar do banco ou Docker.

Uso:
    OPENAI_API_KEY=sk-... python scripts/test_extractor.py
    # ou com .env na raiz do back/:
    python scripts/test_extractor.py
"""
import os
import sys
from pathlib import Path

# Adiciona o src/back ao path para importar app.*
sys.path.insert(0, str(Path(__file__).parent.parent))

# Carrega .env se existir
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Garante que OPENAI_API_KEY está definida
if not os.environ.get("OPENAI_API_KEY"):
    print("ERRO: defina OPENAI_API_KEY no ambiente ou em .env")
    sys.exit(1)

from app.services.ingestion.pdf import ingest_pdf
from app.services.ai.extractor import extract_from_documents, ProcessMetadata

DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"


def process_group(label: str, pdf_files: list[Path]) -> None:
    print(f"\n{'='*50}")
    print(f"PROCESSO: {label}")
    print(f"{'='*50}")
    for p in pdf_files:
        print(f"  {p.name}")

    docs = []
    print("\nIngerindo documentos...")
    for pdf_path in pdf_files:
        try:
            doc = ingest_pdf(pdf_path)
            docs.append(doc)
            print(f"  [{doc.doc_type}] {pdf_path.name} — {len(doc.raw_text)} chars")
        except Exception as e:
            print(f"  ERRO ao ingerir {pdf_path.name}: {e}")

    if not docs:
        print("  Nenhum documento ingerido com sucesso.")
        return

    print("\nChamando OpenAI para extração de metadados...")
    result: ProcessMetadata = extract_from_documents(docs)

    print("\n--- RESULTADO ---")
    print(f"  UF:             {result.uf or 'não identificado'}")
    print(f"  Valor da causa: R$ {result.valor_da_causa:,.2f}" if result.valor_da_causa else "  Valor da causa: não identificado")
    print(f"  Sub-assunto:    {result.sub_assunto.value if result.sub_assunto else 'não identificado'}")


def main() -> None:
    # PDFs soltos na raiz de data/ = processo raiz
    groups: dict[str, list[Path]] = {}

    root_pdfs = sorted(DATA_DIR.glob("*.pdf"))
    if root_pdfs:
        groups[DATA_DIR.name] = root_pdfs

    # Cada subpasta = um processo separado
    for subdir in sorted(DATA_DIR.iterdir()):
        if subdir.is_dir():
            pdfs = sorted(subdir.glob("*.pdf"))
            if pdfs:
                groups[subdir.name] = pdfs

    if not groups:
        print(f"Nenhum PDF encontrado em {DATA_DIR}")
        sys.exit(1)

    for label, pdf_files in groups.items():
        process_group(label, pdf_files)


if __name__ == "__main__":
    main()
