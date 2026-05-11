from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Filtro(Base):
    __tablename__ = "filtro"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(80), nullable=False)
    query: Mapped[str] = mapped_column(String(255), nullable=False)
    localidade: Mapped[str | None] = mapped_column(String(120), nullable=True)
    modalidade: Mapped[str | None] = mapped_column(String(30), nullable=True)
    nivel: Mapped[str | None] = mapped_column(String(30), nullable=True)
    intervalo_min: Mapped[int] = mapped_column(Integer, default=120)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    ultima_busca_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    criada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
