from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from app.storage import db
from app.bot_ui.keyboards import bottom_kb
from app.bot_ui.screens import show_categories_as_reply
from app.handlers.bottom_menu import send_reorder_list


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Start command: add current chat to subscribers and show bottom keyboard only.
    """
    db.add_subscriber(update.effective_chat.id)
    await update.message.reply_text(
        "Бот меню ⬇️",
        reply_markup=bottom_kb(update.effective_chat.id),
    )


async def categories_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show categories list (as a new message).
    """
    await show_categories_as_reply(update.message, context)


async def reorder_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show reorder list (items below limit).
    """
    await send_reorder_list(update, context)


async def subscribe_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Subscribe current chat to notifications.
    """
    chat_id = update.effective_chat.id
    db.add_subscriber(chat_id)
    await update.message.reply_text("✅ Ти підписаний(а) на сповіщення.", reply_markup=bottom_kb(chat_id))


async def unsubscribe_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Unsubscribe current chat from notifications.
    """
    chat_id = update.effective_chat.id
    db.remove_subscriber(chat_id)
    await update.message.reply_text("🔕 Ти відписаний(а) від сповіщень.", reply_markup=bottom_kb(chat_id))


def register_command_handlers(app: Application) -> None:
    """
    Register /commands handlers.
    """
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("categories", categories_cmd))
    app.add_handler(CommandHandler("reorder", reorder_cmd))
    app.add_handler(CommandHandler("subscribe", subscribe_cmd))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe_cmd))
