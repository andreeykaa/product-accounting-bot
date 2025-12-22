from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from app.bot_ui.keyboards import bottom_kb
from app.bot_ui.screens import send_categories_reply, send_category_reply, send_product_reply, send_tasks_reply, \
    send_task_reply


async def on_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Cancel current conversation flow and return user to the last known screen.
    """
    q = update.callback_query
    await q.answer()

    chat_id = q.message.chat.id
    await q.message.reply_text("Скасовано ✅", reply_markup=bottom_kb(chat_id))

    active_task_id = context.user_data.get("active_task_id")
    if active_task_id:
        await send_task_reply(q.message, context, int(active_task_id))
        return ConversationHandler.END

    active_tc_id = context.user_data.get("active_tc_id")
    if active_tc_id:
        await send_tasks_reply(q.message, context, int(active_tc_id))
        return ConversationHandler.END

    active_prod_id = context.user_data.get("active_prod_id")
    if active_prod_id:
        await send_product_reply(q.message, context, int(active_prod_id))
        return ConversationHandler.END

    active_cat_id = context.user_data.get("active_cat_id")
    if active_cat_id:
        await send_category_reply(q.message, context, int(active_cat_id))
    else:
        await send_categories_reply(q.message, context)

    return ConversationHandler.END
