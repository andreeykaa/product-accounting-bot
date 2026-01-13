from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from app.storage import db
from app.bot_ui.keyboards import cancel_keyboard, bottom_kb
from app.bot_ui.screens import send_product_reply, send_tech_card_reply
from app.handlers.conversations.common import reset_active_context

SEARCH_QUERY = 1


def _format_results_text(rows: list[dict]) -> str:
    if not rows:
        return "Нічого схожого не знайшов 🙁 Спробуй інший запит."
    return "🔎 Результати пошуку (натисни кнопку, щоб відкрити):"


def _results_kb(rows: list[dict]) -> InlineKeyboardMarkup:
    """
    Inline keyboard for search results.
    Shows:
      📦 <product name>
      🧾 <tech card name>
    """
    kb: list[list[InlineKeyboardButton]] = []

    for r in rows:
        t = r.get("type")   # "product" | "tech_card"
        _id = r.get("id")
        title = (r.get("title") or "Без назви").strip()

        if t not in ("product", "tech_card"):
            continue

        try:
            _id = int(_id)
        except Exception:
            continue

        icon = "📦" if t == "product" else "📝"

        kb.append([
            InlineKeyboardButton(
                text=f"{icon} {title}",
                callback_data=f"sr:open:{t}:{_id}",
            )
        ])

    kb.append([
        InlineKeyboardButton("❌ Скасувати", callback_data="search:cancel")
    ])

    return InlineKeyboardMarkup(kb)


async def search_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Entry point: user pressed reply button "🔍 Швидкий пошук"
    """
    await update.message.reply_text(
        "🔍 Введи текст для пошуку (продукти + тех-карти).\n\n"
        "Щоб вийти — натисни «❌ Скасувати».",
        reply_markup=cancel_keyboard("search"),
    )
    return SEARCH_QUERY


async def search_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Accept user query text, search, return inline buttons with results.
    """
    q = (update.message.text or "").strip()

    if len(q) < 2:
        await update.message.reply_text(
            "Введи хоча б 2 символи",
            reply_markup=cancel_keyboard("search"),
        )
        return SEARCH_QUERY

    results = db.quick_search(q, out_limit=10, min_score=60)

    context.user_data["search_last_query"] = q
    context.user_data["search_last_results"] = results

    if not results:
        await update.message.reply_text(
            _format_results_text(results) + "\n\nВведи інший запит або натисни «❌ Скасувати».",
            reply_markup=cancel_keyboard("search"),
        )
        return SEARCH_QUERY

    await update.message.reply_text(
        _format_results_text(results),
        reply_markup=_results_kb(results),
    )
    return SEARCH_QUERY


async def search_open(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle click on "Відкрити: ...", callback_data = sr:open:<type>:<id>
    """
    q = update.callback_query
    await q.answer()

    parts = (q.data or "").split(":")
    if len(parts) != 4:
        return

    _, action, entity_type, raw_id = parts
    if action != "open" or not raw_id.isdigit():
        return

    entity_id = int(raw_id)

    if entity_type == "product":
        context.user_data["search_return_enabled"] = True
        context.user_data["active_prod_id"] = entity_id
        await send_product_reply(q.message, context, entity_id)
        return

    if entity_type == "tech_card":
        context.user_data["search_return_enabled"] = True
        context.user_data["active_tech_card_id"] = entity_id
        await send_tech_card_reply(q.message, context, entity_id)
        return


async def search_show_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    results = context.user_data.get("search_last_results") or []
    if not results:
        await q.message.reply_text(
            "Немає збережених результатів пошуку. Введи новий запит 🙂",
            reply_markup=cancel_keyboard("search"),
        )
        return

    await q.message.reply_text(
        _format_results_text(results),
        reply_markup=_results_kb(results),
    )


async def search_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Cancel search: behave like "🔄 Оновити дані" -> go to main menu.
    """
    q = update.callback_query
    await q.answer()

    reset_active_context(context.user_data)
    context.user_data.pop("search_return_enabled", None)
    context.user_data.pop("search_last_results", None)
    context.user_data.pop("search_last_query", None)

    chat_id = q.message.chat.id
    await q.message.reply_text("Скасовано ✅\n\nБот меню ⬇️", reply_markup=bottom_kb(chat_id))
    return ConversationHandler.END


def register_search_conversations(app: Application) -> None:
    """
    Register quick search conversation.
    """
    app.add_handler(ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r"^🔍 Швидкий пошук$"), search_entry),
        ],
        states={
            SEARCH_QUERY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, search_query),
                CallbackQueryHandler(search_open, pattern=r"^sr:open:(product|tech_card):\d+$"),
                CallbackQueryHandler(search_cancel, pattern=r"^search:cancel$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(search_cancel, pattern=r"^search:cancel$"),
        ],
        allow_reentry=True,
    ))
    app.add_handler(CallbackQueryHandler(search_show_results, pattern=r"^sr:results$"))
