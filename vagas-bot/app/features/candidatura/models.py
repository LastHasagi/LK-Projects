from datetime import datetime
from enum import StrEnum

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class CandidaturaStatus(StrEnum):
    QUEUED = "queued"
    APPLYING = "applying"
    PENDING_USER_INPUT = "pending_user_input"
    APPLIED = "applied"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Candidatura(Base):
    __tablename__ = "candidatura"

    id: Mapped[int] = mapped_column(primary_key=True)
    vaga_id: Mapped[int] = mapped_column(
        ForeignKey("vaga.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(30), default=CandidaturaStatus.QUEUED.value)
    tentativas: Mapped[int] = mapped_column(Integer, default=0)
    ultimo_erro: Mapped[str | None] = mapped_column(Text, nullable=True)
    screenshot_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    pergunta_pendente: Mapped[str | None] = mapped_column(Text, nullable=True)
    pergunta_field_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    criada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    atualizada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Evento(Base):
    __tablename__ = "evento"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidatura_id: Mapped[int | None] = mapped_column(
        ForeignKey("candidatura.id", ondelete="CASCADE"), nullable=True
    )
    vaga_id: Mapped[int | None] = mapped_column(
        ForeignKey("vaga.id", ondelete="SET NULL"), nullable=True
    )
    tipo: Mapped[str] = mapped_column(String(40), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
