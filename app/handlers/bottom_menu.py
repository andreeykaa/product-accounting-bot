from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from app.bot_ui.keyboards import bottom_kb
from app.bot_ui.screens import send_categories_reply, send_tasks_cat_reply
from app.storage import db


async def bottom_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Bottom button: show categories.
    """
    await send_categories_reply(update.message, context)


async def bottom_refresh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Bottom button: reset active category context and show categories.
    """
    chat_id = update.effective_chat.id
    context.user_data.pop("active_cat_id", None)
    await update.message.reply_text("🔄 Оновлено.", reply_markup=bottom_kb(chat_id))
    await send_categories_reply(update.message, context)


async def bottom_reorder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Bottom button: show reorder list.
    """
    await send_reorder_list(update, context)


async def bottom_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Bottom button: subscribe.
    """
    chat_id = update.effective_chat.id
    db.add_subscriber(chat_id)
    await update.message.reply_text("✅ Ти підписаний(а) на сповіщення.", reply_markup=bottom_kb(chat_id))


async def bottom_unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Bottom button: unsubscribe.
    """
    chat_id = update.effective_chat.id
    db.remove_subscriber(chat_id)
    await update.message.reply_text("🔕 Ти відписаний(а) від сповіщень.", reply_markup=bottom_kb(chat_id))


async def bottom_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Bottom button: show categories.
    """
    await send_tasks_cat_reply(update.message, context)


async def send_reorder_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Render reorder list based on current DB state.
    """
    chat_id = update.effective_chat.id
    rows = db.list_reorder_items()

    if not rows:
        await update.message.reply_text("✅ Немає позицій для дозамовлення.", reply_markup=bottom_kb(chat_id))
        return

    msg_lines = ["📝 Список дозамовлення:"]
    current_cat = None

    for _, cat_name, _, prod_name, qty, limit_qty in rows:
        if current_cat != cat_name:
            current_cat = cat_name
            msg_lines.append(f"\n📦 {cat_name}:")
        msg_lines.append(f" • {prod_name} — {qty} (ліміт {limit_qty})")

    await update.message.reply_text("\n".join(msg_lines), reply_markup=bottom_kb(chat_id))


def register_bottom_menu_handlers(app: Application) -> None:
    """
    Register handlers for ReplyKeyboardMarkup buttons.
    """
    app.add_handler(MessageHandler(filters.Regex(r"^🏠 Категорії$"), bottom_categories))
    app.add_handler(MessageHandler(filters.Regex(r"^🔄 Оновити базу$"), bottom_refresh))
    app.add_handler(MessageHandler(filters.Regex(r"^📝 Дозамовити$"), bottom_reorder))
    app.add_handler(MessageHandler(filters.Regex(r"^🔔 Підписатися$"), bottom_subscribe))
    app.add_handler(MessageHandler(filters.Regex(r"^🔕 Відписатися$"), bottom_unsubscribe))
    app.add_handler(MessageHandler(filters.Regex(r"^📝 Список завдань$"), bottom_tasks))
