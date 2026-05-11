"""phase4 match_result

Revision ID: 3892e6d96392
Revises: 3ad43019cff2
Create Date: 2026-05-11 12:15:15.072901

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "3892e6d96392"
down_revision: Union[str, Sequence[str], None] = "3ad43019cff2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "match_result",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vaga_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("justificativa", sa.Text(), nullable=False),
        sa.Column("citacoes", sa.JSON(), nullable=False),
        sa.Column("modelo", sa.String(length=80), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["vaga_id"], ["vaga.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("vaga_id", name="uq_match_vaga"),
    )


def downgrade() -> None:
    op.drop_table("match_result")
