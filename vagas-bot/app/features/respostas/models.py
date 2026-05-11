from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

EMBED_DIMS = 1536


class RespostaCustom(Base):
    __tablename__ = "resposta_custom"

    id: Mapped[int] = mapped_column(primary_key=True)
    pergunta_texto: Mapped[str] = mapped_column(Text, nullable=False)
    pergunta_embedding = mapped_column(Vector(EMBED_DIMS), nullable=False)
    resposta_texto: Mapped[str] = mapped_column(Text, nullable=False)
    vezes_usada: Mapped[int] = mapped_column(Integer, default=0)
    criada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    atualizada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    ultima_usada_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
