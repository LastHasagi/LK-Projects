import hashlib
import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.email_submission.models import (
    EmailSubmission,
    SubmissionStatus,
)

_TTL_DAYS = 30
_WS_RE = re.compile(r"\s+")
_LEADING_TIMESTAMP_RE = re.compile(
    r"^\s*\d{4}-\d{1,2}-\d{1,2}[T\s]\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?"
    r"(?:Z|[+-]\d{2}:?\d{2})?\s*"
)
_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F9FF"  # symbols & pictographs
    "\U0001FA00-\U0001FAFF"  # extended-A
    "\U00002600-\U000027BF"  # misc symbols + dingbats
    "\U0001F000-\U0001F0FF"  # mahjong, dominoes, cards
    "\U0001F100-\U0001F2FF"  # enclosed alphanumeric supplement
    "\U0000FE0F"             # variation selector
    "\U0000200D"             # zero-width joiner
    "]+",
    flags=re.UNICODE,
)
_QUOTE_RE = re.compile(r"[‘’“”«»]")
_DASH_RE = re.compile(r"[–—−]")
_PUNCT_NOISE_RE = re.compile(r"[•·●◦▪▫■□◾◽★☆]")


def _normalize_for_hash(text: str) -> str:
    t = text
    t = _LEADING_TIMESTAMP_RE.sub("", t)
    t = _EMOJI_RE.sub(" ", t)
    t = _QUOTE_RE.sub('"', t)
    t = _DASH_RE.sub("-", t)
    t = _PUNCT_NOISE_RE.sub(" ", t)
    t = t.lower()
    t = _WS_RE.sub(" ", t).strip()
    return t


def content_hash(text: str) -> str:
    return hashlib.sha256(_normalize_for_hash(text).encode("utf-8")).hexdigest()


async def buscar_duplicata(
    session: AsyncSession,
    *,
    chat_id: int,
    email: str,
    chash: str,
) -> EmailSubmission | None:
    stmt = (
        select(EmailSubmission)
        .where(
            EmailSubmission.chat_id == chat_id,
            EmailSubmission.email_destinatario == email.lower(),
            EmailSubmission.content_hash == chash,
        )
        .order_by(desc(EmailSubmission.created_at))
        .limit(1)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def criar_submissao(
    session: AsyncSession,
    *,
    chat_id: int,
    email: str,
    raw_text: str,
    cargo: str | None = None,
    empresa: str | None = None,
) -> tuple[EmailSubmission, EmailSubmission | None]:
    """Cria submissão e retorna (nova, duplicata_anterior_ou_None)."""
    chash = content_hash(raw_text)
    dup = await buscar_duplicata(
        session, chat_id=chat_id, email=email, chash=chash
    )
    now = datetime.now(timezone.utc)
    sub = EmailSubmission(
        chat_id=chat_id,
        email_destinatario=email.lower(),
        content_hash=chash,
        cargo=cargo,
        empresa=empresa,
        raw_text=raw_text,
        status=SubmissionStatus.PENDING.value,
        duplicate_of=dup.id if dup is not None else None,
        expires_at=now + timedelta(days=_TTL_DAYS),
    )
    session.add(sub)
    await session.commit()
    await session.refresh(sub)
    return sub, dup


async def marcar_status(
    session: AsyncSession,
    *,
    submission_id: int,
    status: SubmissionStatus,
    pending_email_uid: str | None = None,
) -> None:
    values: dict = {"status": status.value}
    if pending_email_uid is not None:
        values["pending_email_uid"] = pending_email_uid
    await session.execute(
        update(EmailSubmission)
        .where(EmailSubmission.id == submission_id)
        .values(**values)
    )
    await session.commit()


async def marcar_status_por_uid(
    session: AsyncSession,
    *,
    pending_email_uid: str,
    status: SubmissionStatus,
) -> None:
    await session.execute(
        update(EmailSubmission)
        .where(EmailSubmission.pending_email_uid == pending_email_uid)
        .values(status=status.value)
    )
    await session.commit()


async def listar_recentes(
    session: AsyncSession,
    *,
    chat_id: int,
    limit: int = 20,
) -> list[EmailSubmission]:
    stmt = (
        select(EmailSubmission)
        .where(EmailSubmission.chat_id == chat_id)
        .order_by(desc(EmailSubmission.created_at))
        .limit(limit)
    )
    return list((await session.execute(stmt)).scalars().all())


async def cleanup_expired(session: AsyncSession) -> int:
    now = datetime.now(timezone.utc)
    result = await session.execute(
        update(EmailSubmission)
        .where(
            EmailSubmission.expires_at < now,
            EmailSubmission.status.in_(
                [
                    SubmissionStatus.PENDING.value,
                    SubmissionStatus.DRAFTED.value,
                ]
            ),
        )
        .values(status=SubmissionStatus.EXPIRED.value)
    )
    await session.commit()
    return result.rowcount or 0
