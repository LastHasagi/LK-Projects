"""phase5 candidatura

Revision ID: b126b730e399
Revises: 3892e6d96392
Create Date: 2026-05-11 12:34:09.801959

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "b126b730e399"
down_revision: Union[str, Sequence[str], None] = "3892e6d96392"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "candidatura",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vaga_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("tentativas", sa.Integer(), nullable=False),
        sa.Column("ultimo_erro", sa.Text(), nullable=True),
        sa.Column("screenshot_path", sa.String(length=512), nullable=True),
        sa.Column("pergunta_pendente", sa.Text(), nullable=True),
        sa.Column("pergunta_field_id", sa.String(length=160), nullable=True),
        sa.Column("criada_em", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("atualizada_em", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["vaga_id"], ["vaga.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "evento",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("candidatura_id", sa.Integer(), nullable=True),
        sa.Column("vaga_id", sa.Integer(), nullable=True),
        sa.Column("tipo", sa.String(length=40), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["candidatura_id"], ["candidatura.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vaga_id"], ["vaga.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("evento")
    op.drop_table("candidatura")
