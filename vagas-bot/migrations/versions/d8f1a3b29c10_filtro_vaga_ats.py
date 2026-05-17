"""add ats column to filtro and vaga

Revision ID: d8f1a3b29c10
Revises: c4d7e9f01a23
Create Date: 2026-05-17 15:30:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "d8f1a3b29c10"
down_revision: Union[str, Sequence[str], None] = "c4d7e9f01a23"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "filtro",
        sa.Column(
            "ats", sa.String(length=20), nullable=False, server_default="gupy"
        ),
    )
    op.add_column(
        "vaga",
        sa.Column(
            "ats", sa.String(length=20), nullable=False, server_default="gupy"
        ),
    )
    op.create_index("ix_filtro_ats", "filtro", ["ats"])
    op.create_index("ix_vaga_ats", "vaga", ["ats"])


def downgrade() -> None:
    op.drop_index("ix_vaga_ats", table_name="vaga")
    op.drop_index("ix_filtro_ats", table_name="filtro")
    op.drop_column("vaga", "ats")
    op.drop_column("filtro", "ats")
