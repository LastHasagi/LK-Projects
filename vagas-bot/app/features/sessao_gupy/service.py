from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import decrypt, encrypt
from app.features.sessao_gupy.models import SessaoGupy


async def save_storage_state(
    session: AsyncSession, plaintext: bytes, *, rotulo: str = "default"
) -> SessaoGupy:
    encrypted = encrypt(plaintext)
    await session.execute(delete(SessaoGupy).where(SessaoGupy.rotulo == rotulo))
    row = SessaoGupy(storage_state_enc=encrypted, rotulo=rotulo)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def load_storage_state(
    session: AsyncSession, *, rotulo: str = "default"
) -> bytes | None:
    stmt = select(SessaoGupy).where(SessaoGupy.rotulo == rotulo)
    row = (await session.execute(stmt)).scalar_one_or_none()
    if row is None:
        return None
    return decrypt(row.storage_state_enc)
