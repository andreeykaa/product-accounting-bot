import sqlite3
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.bot_ui.screens import send_tech_cards_reply, send_tech_card_reply
from app.storage import db
from app.bot_ui.keyboards import bottom_kb, cancel_keyboard
from app.handlers.conversations.common import on_cancel

CARD_ADD_NAME = 1
CARD_ADD_PHOTO = 2

CARD_EDIT_NAME = 10
CARD_EDIT_PHOTO = 20


def tech_photo_skip_keyboard() -> InlineKeyboardMarkup:
    """
    Inline keyboard for optional limit input during product creation.
    - Skip: create tech card with photo_file_id = NULL
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏭ Пропустити", callback_data="tech_card:skip_photo")],
        [InlineKeyboardButton("❌ Скасувати", callback_data="tech_card:cancel")],
    ])


def tech_photo_edit_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🗑 Видалити фото", callback_data="tech_card:remove_photo")],
        [InlineKeyboardButton("❌ Скасувати", callback_data="tech_card:cancel")],
    ])


async def card_add_from_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    tech_card_cat_id = context.user_data.get("active_tech_card_cat_id")
    tech_card_type_id = context.user_data.get("active_tech_card_type_id")

    if not tech_card_cat_id or not tech_card_type_id:
        await q.message.reply_text("Помилка стану. Відкрий «Тех карти» і вибери процес та тип ще раз.")
        return ConversationHandler.END

    await q.message.reply_text("Введи назву нової технічної карти:", reply_markup=cancel_keyboard("tech_card"))
    return CARD_ADD_NAME


async def card_add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = (update.message.text or "").strip()
    if not name:
        await update.message.reply_text("Назва не може бути порожньою. Введи ще раз:")
        return CARD_ADD_NAME

    context.user_data["new_card_name"] = name

    await update.message.reply_text(
        "Надішли фото для тех-карти (або натисни «Пропустити»):",
        reply_markup=tech_photo_skip_keyboard(),
    )
    return CARD_ADD_PHOTO


async def card_add_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text(
            "Потрібно надіслати фото або натисни «Пропустити».",
            reply_markup=tech_photo_skip_keyboard(),
        )
        return CARD_ADD_PHOTO

    photo_file_id = update.message.photo[-1].file_id

    name = context.user_data.get("new_card_name")
    tech_card_cat_id = context.user_data.get("active_tech_card_cat_id")
    tech_card_type_id = context.user_data.get("active_tech_card_type_id")

    if not name or not tech_card_cat_id or not tech_card_type_id:
        await update.message.reply_text("Помилка стану. Відкрий «Тех карти» ще раз.")
        return ConversationHandler.END

    db.add_card(
        name=name,
        process_id=int(tech_card_cat_id),
        target_type=int(tech_card_type_id),
        photo_file_id=photo_file_id
    )

    context.user_data.pop("new_card_name", None)

    chat_id = update.effective_chat.id
    await update.message.reply_text("✅ Тех-карту додано", reply_markup=bottom_kb(chat_id))

    await send_tech_cards_reply(update.message, context, int(tech_card_cat_id), int(tech_card_type_id))
    return ConversationHandler.END


async def card_edit_name_from_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    card_id = int(q.data.split(":")[2])
    card = db.get_card(card_id)
    if not card:
        await q.answer("Тех-карту не знайдено.", show_alert=True)
        return ConversationHandler.END

    context.user_data["edit_card_id"] = card_id
    await q.message.reply_text(
        "Введи нову назву тех-карти:",
        reply_markup=cancel_keyboard("tech_card")
    )
    return CARD_EDIT_NAME


async def card_edit_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_name = (update.message.text or "").strip()
    if not new_name:
        await update.message.reply_text("Назва не може бути порожньою. Введи ще раз:")
        return CARD_EDIT_NAME

    card_id = context.user_data.get("edit_card_id")
    if not card_id:
        await update.message.reply_text("Помилка стану. Відкрий тех-карту ще раз.")
        return ConversationHandler.END

    db.update_card_name(int(card_id), new_name)
    context.user_data.pop("edit_card_id", None)

    chat_id = update.effective_chat.id
    await update.message.reply_text("✅ Назву змінено", reply_markup=bottom_kb(chat_id))

    await send_tech_card_reply(update.message, context, int(card_id))

    return ConversationHandler.END


async def card_edit_photo_from_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    card_id = int(q.data.split(":")[2])
    card = db.get_card(card_id)
    if not card:
        await q.answer("Тех-карту не знайдено.", show_alert=True)
        return ConversationHandler.END

    context.user_data["edit_card_id"] = card_id

    await q.message.reply_text(
        "Надішли нове фото для тех-карти (або вибери дію нижче):",
        reply_markup=tech_photo_edit_keyboard()
    )
    return CARD_EDIT_PHOTO


async def card_edit_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text(
            "Потрібно надіслати фото або обери дію нижче.",
            reply_markup=tech_photo_edit_keyboard()
        )
        return CARD_EDIT_PHOTO

    photo_file_id = update.message.photo[-1].file_id

    card_id = context.user_data.get("edit_card_id")
    if not card_id:
        await update.message.reply_text("Помилка стану. Відкрий тех-карту ще раз.")
        return ConversationHandler.END

    db.update_card_photo(int(card_id), photo_file_id)
    context.user_data.pop("edit_card_id", None)

    chat_id = update.effective_chat.id
    await update.message.reply_text("✅ Фото оновлено", reply_markup=bottom_kb(chat_id))

    await send_tech_card_reply(update.message, context, int(card_id))

    return ConversationHandler.END


async def card_remove_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    card_id = context.user_data.get("edit_card_id")
    if not card_id:
        await q.message.reply_text("Помилка стану. Відкрий тех-карту ще раз.")
        return ConversationHandler.END

    db.update_card_photo(int(card_id), None)
    context.user_data.pop("edit_card_id", None)

    chat_id = q.message.chat.id
    await q.message.reply_text("✅ Фото прибрано", reply_markup=bottom_kb(chat_id))

    tech_card_cat_id = context.user_data.get("active_tech_card_cat_id")
    tech_card_type_id = context.user_data.get("active_tech_card_type_id")
    if tech_card_cat_id and tech_card_type_id:
        await send_tech_card_reply(q.message, context, int(card_id))
    return ConversationHandler.END


async def card_skip_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    name = context.user_data.get("new_card_name")
    tech_card_cat_id = context.user_data.get("active_tech_card_cat_id")
    tech_card_type_id = context.user_data.get("active_tech_card_type_id")

    if not name or not tech_card_cat_id or not tech_card_type_id:
        await q.message.reply_text("Помилка стану. Відкрий «Тех карти» ще раз.")
        return ConversationHandler.END

    db.add_card(
        name=name,
        process_id=int(tech_card_cat_id),
        target_type=int(tech_card_type_id),
        photo_file_id=None,
    )

    context.user_data.pop("new_card_name", None)

    chat_id = q.message.chat_id
    await q.message.reply_text("✅ Тех-карту додано (без фото)", reply_markup=bottom_kb(chat_id))

    await send_tech_cards_reply(q.message, context, int(tech_card_cat_id), int(tech_card_type_id))
    return ConversationHandler.END


def register_tech_card_conversations(app: Application) -> None:
    app.add_handler(ConversationHandler(
        entry_points=[
            CallbackQueryHandler(card_add_from_button, pattern=r"^tech_card:add:\d+:\d+$")
        ],
        states={
            CARD_ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, card_add_name)],
            CARD_ADD_PHOTO: [
                MessageHandler(filters.PHOTO, card_add_photo),
                CallbackQueryHandler(card_skip_photo, pattern=r"^tech_card:skip_photo$"),
            ],
        },
        fallbacks=[CallbackQueryHandler(on_cancel, pattern=r"^tech_card:cancel$")],
        allow_reentry=True,
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(card_edit_name_from_button, pattern=r"^tech_card:edit_name:\d+$")],
        states={
            CARD_EDIT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, card_edit_name)],
        },
        fallbacks=[CallbackQueryHandler(on_cancel, pattern=r"^tech_card:cancel$")],
        allow_reentry=True,
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(card_edit_photo_from_button, pattern=r"^tech_card:edit_photo:\d+$")],
        states={
            CARD_EDIT_PHOTO: [
                MessageHandler(filters.PHOTO, card_edit_photo),
                CallbackQueryHandler(card_remove_photo, pattern=r"^tech_card:remove_photo$"),
            ],
        },
        fallbacks=[CallbackQueryHandler(on_cancel, pattern=r"^tech_card:cancel$")],
        allow_reentry=True,
    ))
