from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from app.bot_ui.keyboards import bottom_kb
from app.bot_ui.screens import send_categories_reply, send_category_reply


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
        await send_category_reply(q.message, context, int(active_cat_id))
    else:
        await send_categories_reply(q.message, context)

    return ConversationHandler.END
