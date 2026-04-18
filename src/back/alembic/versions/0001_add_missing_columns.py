"""add missing columns to all tables

Revision ID: 0001
Revises:
Create Date: 2026-04-18
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # ── processo ────────────────────────────────────────────────────────────
    conn.execute(sa.text(
        "ALTER TABLE processo ADD COLUMN IF NOT EXISTS metadata_extraida JSONB"
    ))

    # ── documento ───────────────────────────────────────────────────────────
    conn.execute(sa.text(
        "ALTER TABLE documento ADD COLUMN IF NOT EXISTS original_filename VARCHAR(255) NOT NULL DEFAULT ''"
    ))
    conn.execute(sa.text(
        "ALTER TABLE documento ADD COLUMN IF NOT EXISTS parse_errors JSONB"
    ))

    # ── analise_ia ──────────────────────────────────────────────────────────
    conn.execute(sa.text(
        "ALTER TABLE analise_ia ADD COLUMN IF NOT EXISTS fatores_pro_acordo JSONB"
    ))
    conn.execute(sa.text(
        "ALTER TABLE analise_ia ADD COLUMN IF NOT EXISTS fatores_pro_defesa JSONB"
    ))
    conn.execute(sa.text(
        "ALTER TABLE analise_ia ADD COLUMN IF NOT EXISTS requires_supervisor BOOLEAN NOT NULL DEFAULT FALSE"
    ))
    conn.execute(sa.text(
        "ALTER TABLE analise_ia ADD COLUMN IF NOT EXISTS variaveis_extraidas JSONB"
    ))
    conn.execute(sa.text(
        "ALTER TABLE analise_ia ADD COLUMN IF NOT EXISTS casos_similares JSONB"
    ))
    conn.execute(sa.text(
        "ALTER TABLE analise_ia ADD COLUMN IF NOT EXISTS trechos_chave JSONB"
    ))

    # ── proposta_acordo ──────────────────────────────────────────────────────
    conn.execute(sa.text(
        "ALTER TABLE proposta_acordo ADD COLUMN IF NOT EXISTS valor_base_estatistico NUMERIC(12,2)"
    ))
    conn.execute(sa.text(
        "ALTER TABLE proposta_acordo ADD COLUMN IF NOT EXISTS modulador_llm FLOAT"
    ))
    conn.execute(sa.text(
        "ALTER TABLE proposta_acordo ADD COLUMN IF NOT EXISTS custo_estimado_litigar NUMERIC(12,2)"
    ))
    conn.execute(sa.text(
        "ALTER TABLE proposta_acordo ADD COLUMN IF NOT EXISTS n_casos_similares INTEGER NOT NULL DEFAULT 0"
    ))

    # ── decisao_advogado ────────────────────────────────────────────────────
    conn.execute(sa.text(
        "ALTER TABLE decisao_advogado ADD COLUMN IF NOT EXISTS valor_advogado NUMERIC(12,2)"
    ))
    conn.execute(sa.text(
        "ALTER TABLE decisao_advogado ADD COLUMN IF NOT EXISTS justificativa TEXT"
    ))
    conn.execute(sa.text(
        "ALTER TABLE decisao_advogado ADD COLUMN IF NOT EXISTS advogado_id VARCHAR(60)"
    ))
    conn.execute(sa.text(
        "ALTER TABLE decisao_advogado ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT now()"
    ))


def downgrade() -> None:
    pass
