from datetime import datetime

from sqlalchemy import DateTime, LargeBinary, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class SessaoGupy(Base):
    __tablename__ = "sessao_gupy"

    id: Mapped[int] = mapped_column(primary_key=True)
    storage_state_enc: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    rotulo: Mapped[str] = mapped_column(String(64), default="default")
    criada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    atualizada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
