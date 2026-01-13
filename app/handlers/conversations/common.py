from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

ACTIVE_KEYS = (
    "active_cat_id",
    "active_prod_id",
    "active_task_id",
    "active_tc_id",
    "active_tech_card_cat_id",
    "active_tech_card_type_id",
    "active_tech_card_id",
)


def reset_active_context(user_data: dict) -> None:
    for k in ACTIVE_KEYS:
        user_data.pop(k, None)


def reset_search_context(user_data: dict) -> None:
    user_data.pop("search_return_enabled", None)
    user_data.pop("search_last_results", None)
    user_data.pop("search_last_query", None)


async def on_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Cancel current conversation flow and return user to the last known screen.
    """
    from app.bot_ui.keyboards import bottom_kb
    from app.bot_ui.screens import send_categories_reply, send_category_reply, send_product_reply, send_tasks_reply, \
        send_task_reply, send_tech_cards_reply

    q = update.callback_query
    await q.answer()
    await cleanup_last_tech_photo(q, context)

    chat_id = q.message.chat.id
    await q.message.reply_text("Скасовано ✅", reply_markup=bottom_kb(chat_id))

    active_tech_cat_id = context.user_data.get("active_tech_card_cat_id")
    active_tech_type_id = context.user_data.get("active_tech_card_type_id")
    if active_tech_cat_id and active_tech_type_id:
        await send_tech_cards_reply(q.message, context, int(active_tech_cat_id), int(active_tech_type_id))
        return ConversationHandler.END

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


async def cleanup_last_tech_photo(q, context) -> None:
    msg_id = context.user_data.get("last_tech_photo_msg_id")
    chat_id = context.user_data.get("last_tech_photo_chat_id") or q.message.chat.id

    if not msg_id:
        context.user_data.pop("last_tech_photo_chat_id", None)
        context.user_data.pop("last_tech_photo_card_id", None)
        return

    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=int(msg_id))
    except Exception:
        pass

    context.user_data.pop("last_tech_photo_msg_id", None)
    context.user_data.pop("last_tech_photo_chat_id", None)
    context.user_data.pop("last_tech_photo_card_id", None)


async def cleanup_last_tech_photo_by_chat(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
    msg_id = context.user_data.get("last_tech_photo_msg_id")
    if not msg_id:
        return

    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=int(msg_id))
    except Exception:
        pass

    context.user_data.pop("last_tech_photo_msg_id", None)
    context.user_data.pop("last_tech_photo_card_id", None)
