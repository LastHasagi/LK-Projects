from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

EMBED_DIMS = 1536


class Vaga(Base):
    __tablename__ = "vaga"
    __table_args__ = (UniqueConstraint("url", name="uq_vaga_url"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    gupy_external_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    empresa: Mapped[str | None] = mapped_column(String(160), nullable=True)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    localidade: Mapped[str | None] = mapped_column(String(160), nullable=True)
    modalidade: Mapped[str | None] = mapped_column(String(30), nullable=True)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    descricao_embedding = mapped_column(Vector(EMBED_DIMS), nullable=True)
    filtro_id: Mapped[int | None] = mapped_column(
        ForeignKey("filtro.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), default="novo")
    criada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
