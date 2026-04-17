"""Script de seed — popula sentenca_historica a partir do CSV de 60k sentenças.

Uso:
    python scripts/seed_sentencas.py --csv /data/sentencas.csv

Idempotente: verifica se já há registros antes de rodar.
Custo estimado embeddings: ~60k × 50 tokens × $0.02/1M ≈ $0.06
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings  # noqa: E402
from app.core.logging import configure_logging, get_logger  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.models.sentenca_historica import SentencaHistorica  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.services.ingestion.xlsx import load_sentencas  # noqa: E402

configure_logging()
logger = get_logger("seed_sentencas")

BATCH_SIZE = 100


def _build_embedding_text(row: dict) -> str:
    """Monta o texto que será embeddado para RAG — inclui as features mais relevantes."""
    parts = [
        f"UF: {row.get('uf', 'N/A')}",
        f"sub_assunto: {row.get('sub_assunto', 'N/A')}",
        f"resultado_macro: {row.get('resultado_macro', 'N/A')}",
        f"resultado_micro: {row.get('resultado_micro', 'N/A')}",
        f"valor_causa: {row.get('valor_causa', 'N/A')}",
        f"valor_condenacao: {row.get('valor_condenacao', 'N/A')}",
    ]
    return " | ".join(parts)


def seed(csv_path: Path, force: bool = False) -> None:
    import openai
    import pandas as pd

    settings = get_settings()
    client = openai.OpenAI(api_key=settings.openai_api_key)

    # Garante que as tabelas existem
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        count = db.query(SentencaHistorica).count()
        if count > 0 and not force:
            logger.info("sentenca_historica já tem %d registros — pulando seed (use --force para reprocessar)", count)
            return

        logger.info("Carregando CSV: %s", csv_path)
        df = load_sentencas(csv_path)
        total = len(df)
        logger.info("Total de sentenças a processar: %d", total)

        records: list[SentencaHistorica] = []
        texts_batch: list[str] = []
        rows_batch: list[dict] = []

        for i, (_, row) in enumerate(df.iterrows()):
            row_dict = row.to_dict()
            texts_batch.append(_build_embedding_text(row_dict))
            rows_batch.append(row_dict)

            if len(texts_batch) == BATCH_SIZE or i == total - 1:
                # Gera embeddings para o batch
                resp = client.embeddings.create(
                    model=settings.openai_model_embedding,
                    input=texts_batch,
                )
                embeddings = [item.embedding for item in resp.data]

                for row_dict, embedding in zip(rows_batch, embeddings):
                    records.append(
                        SentencaHistorica(
                            numero_caso=row_dict.get("numero_caso"),
                            uf=row_dict.get("uf"),
                            assunto=row_dict.get("assunto"),
                            sub_assunto=row_dict.get("sub_assunto"),
                            resultado_macro=row_dict.get("resultado_macro"),
                            resultado_micro=row_dict.get("resultado_micro"),
                            valor_causa=row_dict.get("valor_causa"),
                            valor_condenacao=row_dict.get("valor_condenacao"),
                            embedding=embedding,
                        )
                    )

                db.bulk_save_objects(records)
                db.commit()

                logger.info("Processadas %d/%d sentenças", min(i + 1, total), total)
                records = []
                texts_batch = []
                rows_batch = []

    logger.info("Seed concluído.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=Path("/data/sentencas.csv"))
    parser.add_argument("--force", action="store_true", help="Reprocessa mesmo se já houver dados")
    args = parser.parse_args()
    seed(args.csv, force=args.force)
