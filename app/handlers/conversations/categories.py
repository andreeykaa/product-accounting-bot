import sqlite3
from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.storage import db
from app.bot_ui.keyboards import bottom_kb, cancel_keyboard
from app.bot_ui.screens import show_categories_as_reply
from app.handlers.conversations.common import on_cancel

CAT_ADD_NAME = 1
CAT_EDIT_NAME = 2


async def cat_add_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Entry point for adding a category via command.
    """
    await update.message.reply_text("Введи назву нової категорії:", reply_markup=cancel_keyboard("cat"))
    return CAT_ADD_NAME


async def cat_add_from_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Entry point for adding a category via inline button.
    """
    q = update.callback_query
    await q.answer()
    await q.message.reply_text("Введи назву нової категорії:", reply_markup=cancel_keyboard("cat"))
    return CAT_ADD_NAME


async def cat_add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Persist new category name into DB.
    """
    name = (update.message.text or "").strip()
    if not name:
        await update.message.reply_text("Назва не може бути порожньою. Введи ще раз:")
        return CAT_ADD_NAME

    try:
        db.add_category(name)
    except sqlite3.IntegrityError:
        await update.message.reply_text("Така категорія вже існує. Введи іншу:", reply_markup=cancel_keyboard("cat"))
        return CAT_ADD_NAME

    chat_id = update.effective_chat.id
    await update.message.reply_text(f"✅ Додано категорію: {name}", reply_markup=bottom_kb(chat_id))
    await show_categories_as_reply(update.message, context)
    return ConversationHandler.END


async def cat_edit_from_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Entry point for editing a category name.
    """
    q = update.callback_query
    await q.answer()

    cat_id = int((q.data or "").split(":")[2])
    cat = db.get_category(cat_id)
    if not cat:
        await q.message.reply_text("Категорію не знайдено (можливо видалена).")
        return ConversationHandler.END

    context.user_data["cat_edit_id"] = cat_id
    await q.message.reply_text(
        f"Поточна назва: {cat[1]}\n\nВведи нову назву:",
        reply_markup=cancel_keyboard("cat"),
    )
    return CAT_EDIT_NAME


async def cat_edit_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Update category name in DB.
    """
    new_name = (update.message.text or "").strip()
    if not new_name:
        await update.message.reply_text("Назва не може бути порожньою. Введи ще раз:")
        return CAT_EDIT_NAME

    cat_id = context.user_data.get("cat_edit_id")
    if not cat_id:
        await update.message.reply_text("Помилка стану. Відкрий категорії ще раз.")
        return ConversationHandler.END

    try:
        db.update_category(int(cat_id), new_name)
    except sqlite3.IntegrityError:
        await update.message.reply_text("Така назва вже існує. Введи іншу:")
        return CAT_EDIT_NAME

    context.user_data.pop("cat_edit_id", None)
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"✅ Категорію перейменовано на: {new_name}", reply_markup=bottom_kb(chat_id))
    await show_categories_as_reply(update.message, context)
    return ConversationHandler.END


def register_category_conversations(app: Application) -> None:
    """
    Register ConversationHandlers for category flows.
    """
    app.add_handler(ConversationHandler(
        entry_points=[
            CommandHandler("add_category", cat_add_cmd),
            CallbackQueryHandler(cat_add_from_button, pattern=r"^cat:add$"),
        ],
        states={CAT_ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, cat_add_name)]},
        fallbacks=[CallbackQueryHandler(on_cancel, pattern=r"^(cat:cancel|prod:cancel)$")],
        allow_reentry=True,
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(cat_edit_from_button, pattern=r"^cat:edit:\d+$")],
        states={CAT_EDIT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, cat_edit_name)]},
        fallbacks=[CallbackQueryHandler(on_cancel, pattern=r"^(cat:cancel|prod:cancel)$")],
        allow_reentry=True,
    ))
