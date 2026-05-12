"""cv_translation table

Revision ID: a1f3c7e2b801
Revises: b126b730e399
Create Date: 2026-05-12 11:50:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "a1f3c7e2b801"
down_revision: Union[str, Sequence[str], None] = "b126b730e399"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cv_translation",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cv_id", sa.Integer(), nullable=False),
        sa.Column("lang", sa.String(length=8), nullable=False),
        sa.Column("markdown_text", sa.Text(), nullable=False),
        sa.Column("pdf_path", sa.String(length=512), nullable=False),
        sa.Column(
            "criada_em",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["cv_id"], ["cv.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cv_id", "lang", name="uq_cv_translation_cv_lang"),
    )


def downgrade() -> None:
    op.drop_table("cv_translation")
