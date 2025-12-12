from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from app.bot_ui.keyboards import bottom_kb
from app.bot_ui.screens import show_categories_as_reply, show_products_as_reply


async def on_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Cancel current conversation flow and return user to the last known screen.
    """
    q = update.callback_query
    await q.answer()

    chat_id = q.message.chat.id
    await q.message.reply_text("Скасовано ✅", reply_markup=bottom_kb(chat_id))

    active_cat_id = context.user_data.get("active_cat_id")
    if active_cat_id:
        await show_products_as_reply(q.message, context, int(active_cat_id))
    else:
        await show_categories_as_reply(q.message, context)

    return ConversationHandler.END
