from datetime import datetime
from enum import Enum

from sqlalchemy import (
    BigInteger,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class SubmissionStatus(str, Enum):
    PENDING = "pending"
    DRAFTED = "drafted"
    SENT = "sent"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class EmailSubmission(Base):
    __tablename__ = "email_submission"

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    email_destinatario: Mapped[str] = mapped_column(String(320), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    cargo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    empresa: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default=SubmissionStatus.PENDING.value, nullable=False
    )
    duplicate_of: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pending_email_uid: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    __table_args__ = (
        Index("ix_email_submission_chat", "chat_id"),
        Index(
            "ix_email_submission_dedup",
            "chat_id",
            "email_destinatario",
            "content_hash",
        ),
        Index("ix_email_submission_expires", "expires_at"),
    )
