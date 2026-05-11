"""phase2 sessao_gupy and cv

Revision ID: f75fc495084e
Revises: cc1d4ca768c4
Create Date: 2026-05-11 11:00:05.833235

"""
from typing import Sequence, Union

import pgvector.sqlalchemy
import sqlalchemy as sa
from alembic import op


revision: str = 'f75fc495084e'
down_revision: Union[str, Sequence[str], None] = 'cc1d4ca768c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "cv",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("versao", sa.Integer(), nullable=False),
        sa.Column("path_pdf", sa.String(length=512), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        sa.Column("criada_em", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "resposta_custom",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pergunta_texto", sa.Text(), nullable=False),
        sa.Column("pergunta_embedding", pgvector.sqlalchemy.Vector(1536), nullable=False),
        sa.Column("resposta_texto", sa.Text(), nullable=False),
        sa.Column("vezes_usada", sa.Integer(), nullable=False),
        sa.Column("criada_em", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("atualizada_em", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("ultima_usada_em", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "sessao_gupy",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("storage_state_enc", sa.LargeBinary(), nullable=False),
        sa.Column("rotulo", sa.String(length=64), nullable=False),
        sa.Column("criada_em", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("atualizada_em", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "cv_chunk",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cv_id", sa.Integer(), nullable=False),
        sa.Column("ordem", sa.Integer(), nullable=False),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.Column("tokens", sa.Integer(), nullable=False),
        sa.Column("embedding", pgvector.sqlalchemy.Vector(1536), nullable=False),
        sa.ForeignKeyConstraint(["cv_id"], ["cv.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_cv_chunk_embedding_hnsw "
        "ON cv_chunk USING hnsw (embedding vector_cosine_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_resposta_custom_embedding_hnsw "
        "ON resposta_custom USING hnsw (pergunta_embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_resposta_custom_embedding_hnsw")
    op.execute("DROP INDEX IF EXISTS ix_cv_chunk_embedding_hnsw")
    op.drop_table("cv_chunk")
    op.drop_table("sessao_gupy")
    op.drop_table("resposta_custom")
    op.drop_table("cv")
