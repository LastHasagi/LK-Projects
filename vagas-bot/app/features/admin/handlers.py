from arq.connections import ArqRedis, create_pool
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes

from app.core.config import get_settings
from app.core.db import get_session_maker
from app.core.logging import get_logger
from app.core.redis import get_redis_settings
from app.core.telegram import admin_only
from app.features.admin.service import (
    coletar_health,
    coletar_metricas,
    is_pause_scrape,
    limpar_fila,
    limpar_vagas_pendentes_do_filtro,
    listar_eventos_erro,
    resumo_filtros,
    set_pause_scrape,
)
from app.features.filtros.service import desativar_filtro, listar_filtros

log = get_logger(__name__)


def _admin_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Métricas", callback_data="admin:metrics"),
            InlineKeyboardButton("💚 Health", callback_data="admin:health"),
        ],
        [
            InlineKeyboardButton("📝 Logs", callback_data="admin:logs"),
            InlineKeyboardButton("⚙ Controles", callback_data="admin:ctrl"),
        ],
        [InlineKeyboardButton("🔎 Filtros", callback_data="admin:filtros")],
    ])


def _filtros_menu(resumo: list[dict]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for f in resumo:
        rows.append([
            InlineKeyboardButton(
                f"{f['nome']} — {f['pendentes']}/{f['total']}",
                callback_data=f"admin:f:info:{f['id']}",
            ),
        ])
        rows.append([
            InlineKeyboardButton(
                "🔍 Buscar", callback_data=f"admin:f:scrape:{f['id']}"
            ),
            InlineKeyboardButton(
                "🧹 Esvaziar", callback_data=f"admin:f:wipe:{f['id']}"
            ),
            InlineKeyboardButton(
                "🗑 Desativar", callback_data=f"admin:f:disable:{f['id']}"
            ),
        ])
    rows.append([InlineKeyboardButton("⬅ Voltar", callback_data="admin:menu")])
    return InlineKeyboardMarkup(rows)


def _ctrl_menu(paused: bool) -> InlineKeyboardMarkup:
    pause_btn = (
        InlineKeyboardButton("▶ Retomar scrape", callback_data="admin:resume")
        if paused
        else InlineKeyboardButton("⏸ Pausar scrape", callback_data="admin:pause")
    )
    return InlineKeyboardMarkup([
        [pause_btn, InlineKeyboardButton("🔄 Forçar busca", callback_data="admin:force")],
        [InlineKeyboardButton("🗑 Limpar fila", callback_data="admin:clear")],
        [InlineKeyboardButton("⬅ Voltar", callback_data="admin:menu")],
    ])


@admin_only
async def admin_handler(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Painel /admin — escolha:", reply_markup=_admin_menu()
    )


async def admin_callback(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None or not query.data or not query.data.startswith("admin:"):
        return
    if query.from_user.id != get_settings().telegram_admin_user_id:
        await query.answer("Não autorizado.", show_alert=True)
        return
    action = query.data.split(":", 1)[1]

    if action == "menu":
        await query.answer()
        await query.edit_message_text("Painel /admin:", reply_markup=_admin_menu())
        return

    if action == "metrics":
        maker = get_session_maker()
        async with maker() as session:
            m = await coletar_metricas(session)
        txt = (
            f"📊 Métricas\n"
            f"Vagas total: {m['vagas_total']} (24h: +{m['vagas_24h']})\n"
            f"Filtros ativos: {m['filtros_ativos']}\n"
            f"Aplicadas 24h: {m['aplicadas_24h']} · 7d: {m['aplicadas_7d']}\n\n"
            "Candidaturas por status:\n"
            + "\n".join(f"- {k}: {v}" for k, v in m["candidaturas"].items())
        )
        await query.answer()
        await query.edit_message_text(txt, reply_markup=_admin_menu())
        return

    if action == "health":
        h = await coletar_health()
        txt = "💚 Health\n" + "\n".join(f"- {k}: {v}" for k, v in h.items())
        await query.answer()
        await query.edit_message_text(txt, reply_markup=_admin_menu())
        return

    if action == "logs":
        maker = get_session_maker()
        async with maker() as session:
            evs = await listar_eventos_erro(session, limit=10)
        if not evs:
            txt = "📝 Logs\nNenhum erro recente."
        else:
            linhas = [
                f"{e.criado_em:%H:%M %d/%m} {e.tipo}: {str(e.payload)[:120]}"
                for e in evs
            ]
            txt = "📝 Últimos 10 erros\n\n" + "\n".join(linhas)
        await query.answer()
        await query.edit_message_text(txt, reply_markup=_admin_menu())
        return

    if action == "ctrl":
        paused = await is_pause_scrape()
        txt = f"⚙ Controles (scrape {'⏸ pausado' if paused else '▶ rodando'})"
        await query.answer()
        await query.edit_message_text(txt, reply_markup=_ctrl_menu(paused))
        return

    if action == "pause":
        await set_pause_scrape(True)
        await query.answer("Scrape pausado.")
        await query.edit_message_text(
            "⚙ Controles (scrape ⏸ pausado)", reply_markup=_ctrl_menu(True)
        )
        return

    if action == "resume":
        await set_pause_scrape(False)
        await query.answer("Scrape retomado.")
        await query.edit_message_text(
            "⚙ Controles (scrape ▶ rodando)", reply_markup=_ctrl_menu(False)
        )
        return

    if action == "force":
        maker = get_session_maker()
        async with maker() as session:
            ativos = await listar_filtros(session, ativos=True)
        if not ativos:
            await query.answer("Nenhum filtro ativo.", show_alert=True)
            return
        pool: ArqRedis = await create_pool(get_redis_settings())
        try:
            for f in ativos:
                await pool.enqueue_job("scrape_search", f.id)
        finally:
            await pool.close()
        await query.answer(f"Disparado para {len(ativos)} filtro(s).")
        return

    if action == "clear":
        removed = await limpar_fila()
        await query.answer(f"Removidas {removed} chaves arq.")
        return

    if action == "filtros":
        maker = get_session_maker()
        async with maker() as session:
            resumo = await resumo_filtros(session)
        if not resumo:
            await query.answer("Nenhum filtro ativo.", show_alert=True)
            return
        txt = (
            "🔎 Filtros ativos (pendentes/total)\n"
            "Pendentes = vagas indexadas sem candidatura."
        )
        await query.answer()
        await query.edit_message_text(txt, reply_markup=_filtros_menu(resumo))
        return

    if action.startswith("f:"):
        _, op, raw_id = action.split(":", 2)
        try:
            filtro_id = int(raw_id)
        except ValueError:
            await query.answer("ID inválido.", show_alert=True)
            return

        if op == "scrape":
            pool: ArqRedis = await create_pool(get_redis_settings())
            try:
                await pool.enqueue_job("scrape_search", filtro_id)
            finally:
                await pool.close()
            await query.answer(f"Busca disparada para filtro #{filtro_id}.")
            return

        if op == "wipe":
            maker = get_session_maker()
            async with maker() as session:
                removidas = await limpar_vagas_pendentes_do_filtro(session, filtro_id)
            await query.answer(
                f"Filtro #{filtro_id}: {removidas} vaga(s) removida(s).",
                show_alert=True,
            )
            maker = get_session_maker()
            async with maker() as session:
                resumo = await resumo_filtros(session)
            await query.edit_message_text(
                "🔎 Filtros ativos (pendentes/total)",
                reply_markup=_filtros_menu(resumo),
            )
            return

        if op == "disable":
            maker = get_session_maker()
            async with maker() as session:
                await desativar_filtro(session, filtro_id)
                resumo = await resumo_filtros(session)
            await query.answer(
                f"Filtro #{filtro_id} desativado.", show_alert=True
            )
            if not resumo:
                await query.edit_message_text(
                    "Nenhum filtro ativo.", reply_markup=_admin_menu()
                )
            else:
                await query.edit_message_text(
                    "🔎 Filtros ativos (pendentes/total)",
                    reply_markup=_filtros_menu(resumo),
                )
            return

        if op == "info":
            await query.answer(f"Filtro #{filtro_id} — use Buscar/Esvaziar/Desativar.")
            return


admin_callback_handler = CallbackQueryHandler(admin_callback, pattern=r"^admin:")
