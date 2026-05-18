from sqlalchemy import select
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

from app.core.config import get_settings
from app.core.db import get_session_maker
from app.core.logging import get_logger
from app.features.descoberta.models import Vaga
from app.features.matching.models import MatchResult

log = get_logger(__name__)


def _score_emoji(score: int) -> str:
    if score >= 80:
        return "🟢"
    if score >= 50:
        return "🟡"
    return "🔴"


def _format_card(v: Vaga, m: MatchResult | None) -> str:
    linhas = [f"*{v.titulo}*"]
    if v.empresa:
        linhas.append(f"🏢 {v.empresa}")
    detalhes = " · ".join(filter(None, [v.localidade, v.modalidade]))
    if detalhes:
        linhas.append(f"📍 {detalhes}")
    if m is not None:
        linhas.append(f"\n{_score_emoji(m.score)} *Score {m.score}/100*")
        linhas.append(f"_{m.justificativa}_")
        if m.citacoes:
            linhas.append("\n📋 Do seu CV:")
            for c in m.citacoes[:3]:
                linhas.append(f"• _{c}_")
    labels = {"gupy": "Abrir no Gupy", "infojobs": "Abrir no Infojobs"}
    label = labels.get(v.ats, "Abrir vaga")
    linhas.append(f"\n[{label}]({v.url})")
    return "\n".join(linhas)


async def notify_vaga(ctx: dict, vaga_id: int, chat_id: int | None = None) -> None:
    maker = get_session_maker()
    async with maker() as session:
        vaga = await session.get(Vaga, vaga_id)
        match = (
            await session.execute(
                select(MatchResult).where(MatchResult.vaga_id == vaga_id)
            )
        ).scalar_one_or_none()
    if vaga is None:
        log.warning("notify_vaga_missing", vaga_id=vaga_id)
        return

    settings = get_settings()
    destino = chat_id or settings.telegram_admin_user_id
    bot = Bot(token=settings.telegram_bot_token)
    botoes = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Candidatar", callback_data=f"vaga_candidatar:{vaga.id}"),
            InlineKeyboardButton("🚫 Ignorar", callback_data=f"vaga_ignorar:{vaga.id}"),
        ]
    ])
    try:
        await bot.send_message(
            chat_id=destino,
            text=_format_card(vaga, match),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=botoes,
            disable_web_page_preview=False,
        )
    finally:
        await bot.shutdown()
    log.info(
        "notify_vaga_sent",
        vaga_id=vaga_id,
        chat_id=destino,
        score=match.score if match else None,
    )
