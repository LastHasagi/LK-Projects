from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class MatchResult(Base):
    __tablename__ = "match_result"
    __table_args__ = (UniqueConstraint("vaga_id", name="uq_match_vaga"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    vaga_id: Mapped[int] = mapped_column(
        ForeignKey("vaga.id", ondelete="CASCADE"), nullable=False
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    justificativa: Mapped[str] = mapped_column(Text, nullable=False)
    citacoes: Mapped[list[str]] = mapped_column(JSON, default=list)
    modelo: Mapped[str] = mapped_column(String(80), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
