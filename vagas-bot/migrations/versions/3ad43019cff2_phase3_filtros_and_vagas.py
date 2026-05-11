"""phase3 filtros and vagas

Revision ID: 3ad43019cff2
Revises: f75fc495084e
Create Date: 2026-05-11 11:45:25.400775

"""
from typing import Sequence, Union

import pgvector.sqlalchemy
import sqlalchemy as sa
from alembic import op


revision: str = "3ad43019cff2"
down_revision: Union[str, Sequence[str], None] = "f75fc495084e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "filtro",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=80), nullable=False),
        sa.Column("query", sa.String(length=255), nullable=False),
        sa.Column("localidade", sa.String(length=120), nullable=True),
        sa.Column("modalidade", sa.String(length=30), nullable=True),
        sa.Column("nivel", sa.String(length=30), nullable=True),
        sa.Column("intervalo_min", sa.Integer(), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        sa.Column("ultima_busca_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("criada_em", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "vaga",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(length=1024), nullable=False),
        sa.Column("gupy_external_id", sa.String(length=80), nullable=True),
        sa.Column("empresa", sa.String(length=160), nullable=True),
        sa.Column("titulo", sa.String(length=255), nullable=False),
        sa.Column("localidade", sa.String(length=160), nullable=True),
        sa.Column("modalidade", sa.String(length=30), nullable=True),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("descricao_embedding", pgvector.sqlalchemy.Vector(1536), nullable=True),
        sa.Column("filtro_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("criada_em", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["filtro_id"], ["filtro.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url", name="uq_vaga_url"),
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vaga_descricao_embedding_hnsw "
        "ON vaga USING hnsw (descricao_embedding vector_cosine_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_filtro_ativo_ultima_busca "
        "ON filtro (ativo, ultima_busca_em)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_filtro_ativo_ultima_busca")
    op.execute("DROP INDEX IF EXISTS ix_vaga_descricao_embedding_hnsw")
    op.drop_table("vaga")
    op.drop_table("filtro")
