"""email_submission table

Revision ID: c4d7e9f01a23
Revises: a1f3c7e2b801
Create Date: 2026-05-14 18:30:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "c4d7e9f01a23"
down_revision: Union[str, Sequence[str], None] = "a1f3c7e2b801"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "email_submission",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("email_destinatario", sa.String(length=320), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("cargo", sa.String(length=255), nullable=True),
        sa.Column("empresa", sa.String(length=255), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("duplicate_of", sa.Integer(), nullable=True),
        sa.Column("pending_email_uid", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_email_submission_chat", "email_submission", ["chat_id"])
    op.create_index(
        "ix_email_submission_dedup",
        "email_submission",
        ["chat_id", "email_destinatario", "content_hash"],
    )
    op.create_index(
        "ix_email_submission_expires", "email_submission", ["expires_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_email_submission_expires", table_name="email_submission")
    op.drop_index("ix_email_submission_dedup", table_name="email_submission")
    op.drop_index("ix_email_submission_chat", table_name="email_submission")
    op.drop_table("email_submission")
