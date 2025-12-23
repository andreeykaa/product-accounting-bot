from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.storage import db
from app.bot_ui.keyboards import bottom_kb, cancel_keyboard
from app.bot_ui.screens import send_tasks_reply, send_task_reply
from app.handlers.conversations.common import on_cancel

TASK_ADD_TEXT = 50
TASK_EDIT_TEXT = 51


async def task_add_from_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    tc_id = int(q.data.split(":")[2])

    context.user_data["active_tc_id"] = tc_id
    context.user_data.pop("active_task_id", None)

    await q.message.reply_text(
        "Введи текст завдання:",
        reply_markup=cancel_keyboard("task_proc")
    )
    return TASK_ADD_TEXT


async def task_add_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Persist new task into DB.
    """
    text = (update.message.text or "").strip()
    if not text:
        await update.message.reply_text("Текст завдання обов'язковий для введення. Введи ще раз:")
        return TASK_ADD_TEXT

    tc_id = context.user_data.get("active_tc_id")
    if not tc_id:
        await update.message.reply_text(
            "Помилка стану. Відкрий список завдань і спробуй ще раз."
        )
        return ConversationHandler.END

    chat_id = update.effective_chat.id
    db.add_task(chat_id, text, tc_id)

    context.user_data.pop("active_tc_id", None)

    await update.message.reply_text(f"✅ Завдання додано", reply_markup=bottom_kb(chat_id))
    await send_tasks_reply(update.message, context, tc_id)
    return ConversationHandler.END


async def task_edit_from_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Entry point for editing a task.
    """
    q = update.callback_query
    await q.answer()

    task_id = int((q.data or "").split(":")[2])
    task = db.get_task(task_id)
    if not task:
        await q.message.reply_text("Завдання не знайдено.")
        return ConversationHandler.END

    context.user_data["task_edit_id"] = task_id
    await q.message.reply_text(
        f"Введи новий текст завдання:",
        reply_markup=cancel_keyboard("task_proc"),
    )
    return TASK_EDIT_TEXT


async def task_edit_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Update category name in DB.
    """
    new_text = (update.message.text or "").strip()
    if not new_text:
        await update.message.reply_text("Завдання повинно бути введено. Введи ще раз:")
        return TASK_EDIT_TEXT

    task_id = context.user_data.get("task_edit_id")
    if not task_id:
        await update.message.reply_text("Помилка стану. Відкрий завдання ще раз.")
        return ConversationHandler.END

    db.update_task(int(task_id), new_text)
    context.user_data.pop("task_edit_id", None)
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"✅ Текст завдання змінено!", reply_markup=bottom_kb(chat_id))
    await send_task_reply(update.message, context, int(task_id))
    return ConversationHandler.END


def register_task_conversations(app: Application) -> None:
    """
    Register ConversationHandlers for category flows.
    """
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(task_add_from_button, pattern=r"^task_proc:add:\d+$"),],
        states={TASK_ADD_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, task_add_text)]},
        fallbacks=[CallbackQueryHandler(on_cancel, pattern=r"^(task_proc:cancel)$")],
        allow_reentry=True,
        per_message=True,
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(task_edit_from_button, pattern=r"^task:edit:\d+$")],
        states={TASK_EDIT_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, task_edit_text)]},
        fallbacks=[CallbackQueryHandler(on_cancel, pattern=r"^^(task_proc:cancel)$")],
        allow_reentry=True,
        per_message=True,
    ))
