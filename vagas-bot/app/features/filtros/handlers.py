from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.core.config import get_settings
from app.core.db import get_session_maker
from app.core.logging import get_logger
from app.core.telegram import admin_only
from app.features.filtros.service import (
    criar_filtro,
    desativar_filtro,
    listar_filtros,
)

log = get_logger(__name__)

NOME, QUERY, LOCAL, MOD, NIVEL, INTERVALO = range(6)


@admin_only
async def filtros_handler(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    maker = get_session_maker()
    async with maker() as session:
        ativos = await listar_filtros(session, ativos=True)
        inativos = await listar_filtros(session, ativos=False)
    if not ativos and not inativos:
        await update.message.reply_text(
            "Nenhum filtro. Use /filtros_add para criar."
        )
        return
    linhas = []
    botoes = []
    for f in ativos:
        linhas.append(
            f"✅ #{f.id} *{f.nome}* — `{f.query}` "
            f"({f.modalidade or 'qq'} · {f.localidade or 'qq local'} · {f.nivel or 'qq nível'}) "
            f"a cada {f.intervalo_min}min"
        )
        botoes.append([InlineKeyboardButton(f"⏸ pausar #{f.id}", callback_data=f"filtro_off:{f.id}")])
    for f in inativos:
        linhas.append(f"⏸ #{f.id} {f.nome} (inativo)")
    await update.message.reply_text(
        "\n".join(linhas),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(botoes) if botoes else None,
    )


@admin_only
async def add_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data["novo_filtro"] = {}
    await update.message.reply_text("Nome curto do filtro? (ex: backend-remoto)")
    return NOME


async def add_nome(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data["novo_filtro"]["nome"] = update.message.text.strip()
    await update.message.reply_text("Query de busca? (ex: python backend)")
    return QUERY


async def add_query(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data["novo_filtro"]["query"] = update.message.text.strip()
    await update.message.reply_text(
        "Localidade? (ex: São Paulo, ou /skip para qualquer)"
    )
    return LOCAL


async def add_local(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    txt = update.message.text.strip()
    ctx.user_data["novo_filtro"]["localidade"] = None if txt == "/skip" else txt
    await update.message.reply_text(
        "Modalidade? (remoto / hibrido / presencial / /skip)"
    )
    return MOD


async def add_mod(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    txt = update.message.text.strip().lower()
    ctx.user_data["novo_filtro"]["modalidade"] = None if txt == "/skip" else txt
    await update.message.reply_text(
        "Nível? (junior / pleno / senior / staff / /skip)"
    )
    return NIVEL


async def add_nivel(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    txt = update.message.text.strip().lower()
    ctx.user_data["novo_filtro"]["nivel"] = None if txt == "/skip" else txt
    await update.message.reply_text(
        "Intervalo de busca em minutos? (ex: 120)"
    )
    return INTERVALO


async def add_intervalo(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        intervalo = int(update.message.text.strip())
        if intervalo < 15:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Número inteiro ≥ 15. Tente de novo:")
        return INTERVALO
    data = ctx.user_data["novo_filtro"]
    data["intervalo_min"] = intervalo

    maker = get_session_maker()
    async with maker() as session:
        f = await criar_filtro(session, **data)
    await update.message.reply_text(
        f"Filtro #{f.id} *{f.nome}* criado. "
        f"Próxima busca em até {f.intervalo_min}min.",
        parse_mode="Markdown",
    )
    log.info("filtro_created", filtro_id=f.id, nome=f.nome)
    return ConversationHandler.END


@admin_only
async def add_cancel(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Cancelado.")
    return ConversationHandler.END


async def filtros_callback(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None or not query.data or not query.data.startswith("filtro_off:"):
        return
    if query.from_user.id != get_settings().telegram_admin_user_id:
        await query.answer("Não autorizado.", show_alert=True)
        return
    fid = int(query.data.split(":", 1)[1])
    maker = get_session_maker()
    async with maker() as session:
        await desativar_filtro(session, fid)
    await query.answer("Filtro pausado.")
    await query.edit_message_text(f"Filtro #{fid} pausado.")


filtros_add_conversation = ConversationHandler(
    entry_points=[CommandHandler("filtros_add", add_start)],
    states={
        NOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_nome)],
        QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_query)],
        LOCAL: [MessageHandler(filters.TEXT, add_local)],
        MOD: [MessageHandler(filters.TEXT, add_mod)],
        NIVEL: [MessageHandler(filters.TEXT, add_nivel)],
        INTERVALO: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_intervalo)],
    },
    fallbacks=[CommandHandler("cancel", add_cancel)],
)

filtros_off_handler = CallbackQueryHandler(filtros_callback, pattern=r"^filtro_off:\d+$")
