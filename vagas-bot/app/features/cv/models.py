from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

EMBED_DIMS = 1536


class CV(Base):
    __tablename__ = "cv"

    id: Mapped[int] = mapped_column(primary_key=True)
    versao: Mapped[int] = mapped_column(Integer, default=1)
    path_pdf: Mapped[str] = mapped_column(String(512), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=False)
    criada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    chunks: Mapped[list["CVChunk"]] = relationship(
        back_populates="cv", cascade="all, delete-orphan"
    )


class CVChunk(Base):
    __tablename__ = "cv_chunk"

    id: Mapped[int] = mapped_column(primary_key=True)
    cv_id: Mapped[int] = mapped_column(ForeignKey("cv.id", ondelete="CASCADE"))
    ordem: Mapped[int] = mapped_column(Integer, nullable=False)
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    tokens: Mapped[int] = mapped_column(Integer, default=0)
    embedding = mapped_column(Vector(EMBED_DIMS), nullable=False)

    cv: Mapped["CV"] = relationship(back_populates="chunks")
