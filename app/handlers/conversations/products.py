import sqlite3
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
from app.bot_ui.screens import show_products_as_reply
from app.handlers.conversations.common import on_cancel
from app.utils.parsing import parse_qty, parse_limit
from app.services.notifications import maybe_notify_limit_crossed

PROD_ADD_NAME = 10
PROD_ADD_QTY = 11

PROD_EDIT_NAME = 20
PROD_EDIT_QTY = 30
PROD_EDIT_LIMIT = 40


async def prod_add_from_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Entry point for adding a product from inline button.
    """
    q = update.callback_query
    await q.answer()

    cat_id = int((q.data or "").split(":")[2])
    cat = db.get_category(cat_id)
    if not cat:
        await q.message.reply_text("Категорію не знайдено (можливо видалена).")
        return ConversationHandler.END

    context.user_data["active_cat_id"] = cat_id
    context.user_data["prod_add_cat_id"] = cat_id

    await q.message.reply_text(
        f"Категорія: {cat[1]}\n\nВведи назву продукту:",
        reply_markup=cancel_keyboard("prod"),
    )
    return PROD_ADD_NAME


async def prod_add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Collect product name for the add flow.
    """
    name = (update.message.text or "").strip()
    if not name:
        await update.message.reply_text("Назва не може бути порожньою. Введи ще раз:")
        return PROD_ADD_NAME

    context.user_data["prod_add_name"] = name
    await update.message.reply_text("Введи кількість (наприклад 2 або 2.5):", reply_markup=cancel_keyboard("prod"))
    return PROD_ADD_QTY


async def prod_add_qty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Persist a new product into DB.
    """
    cat_id = context.user_data.get("prod_add_cat_id")
    name = context.user_data.get("prod_add_name")
    if not cat_id or not name:
        await update.message.reply_text("Помилка стану. Відкрий категорію і натисни «Додати продукт».")
        return ConversationHandler.END

    try:
        qty = parse_qty(update.message.text)
    except Exception:
        await update.message.reply_text("Кількість має бути числом > 0. Приклад: 3 або 1.5. Введи ще раз:")
        return PROD_ADD_QTY

    try:
        db.add_product(int(cat_id), name, qty, None)
    except sqlite3.IntegrityError:
        await update.message.reply_text(
            "Такий продукт вже існує в цій категорії. Введи іншу назву:",
            reply_markup=cancel_keyboard("prod"),
        )
        return PROD_ADD_NAME

    context.user_data.pop("prod_add_cat_id", None)
    context.user_data.pop("prod_add_name", None)

    chat_id = update.effective_chat.id
    await update.message.reply_text(f"✅ Додано продукт: {name} — {qty}", reply_markup=bottom_kb(chat_id))
    await show_products_as_reply(update.message, context, int(cat_id))
    return ConversationHandler.END


async def prod_rename_from_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Entry point for renaming a product.
    """
    q = update.callback_query
    await q.answer()

    prod_id = int((q.data or "").split(":")[2])
    prod = db.get_product(prod_id)
    if not prod:
        await q.message.reply_text("Продукт не знайдено (можливо видалений).")
        return ConversationHandler.END

    _, cat_id, name, qty, limit_qty, _ = prod
    context.user_data["active_cat_id"] = cat_id
    context.user_data["prod_rename_id"] = prod_id

    limit_text = "—" if limit_qty is None else str(limit_qty)
    await q.message.reply_text(
        f"Поточна назва: {name}\nКількість: {qty}\nЛіміт: {limit_text}\n\nВведи НОВУ назву продукту:",
        reply_markup=cancel_keyboard("prod"),
    )
    return PROD_EDIT_NAME


async def prod_rename_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Persist product rename.
    """
    new_name = (update.message.text or "").strip()
    if not new_name:
        await update.message.reply_text("Назва не може бути порожньою. Введи ще раз:")
        return PROD_EDIT_NAME

    prod_id = context.user_data.get("prod_rename_id")
    cat_id = context.user_data.get("active_cat_id")
    if not prod_id or not cat_id:
        await update.message.reply_text("Помилка стану. Відкрий категорію і спробуй ще раз.")
        return ConversationHandler.END

    try:
        db.update_product_name(int(prod_id), new_name)
    except sqlite3.IntegrityError:
        await update.message.reply_text(
            "Продукт з такою назвою вже існує в цій категорії. Введи іншу назву:",
            reply_markup=cancel_keyboard("prod"),
        )
        return PROD_EDIT_NAME

    context.user_data.pop("prod_rename_id", None)
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"✅ Назву змінено на: {new_name}", reply_markup=bottom_kb(chat_id))
    await show_products_as_reply(update.message, context, int(cat_id))
    return ConversationHandler.END


async def prod_qty_from_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Entry point for updating product quantity.
    """
    q = update.callback_query
    await q.answer()

    prod_id = int((q.data or "").split(":")[2])
    prod = db.get_product(prod_id)
    if not prod:
        await q.message.reply_text("Продукт не знайдено (можливо видалений).")
        return ConversationHandler.END

    _, cat_id, name, qty, limit_qty, _ = prod
    context.user_data["active_cat_id"] = cat_id
    context.user_data["prod_qty_id"] = prod_id

    limit_text = "—" if limit_qty is None else str(limit_qty)
    await q.message.reply_text(
        f"Продукт: {name}\nПоточна кількість: {qty}\nЛіміт: {limit_text}\n\nВведи НОВУ кількість:",
        reply_markup=cancel_keyboard("prod"),
    )
    return PROD_EDIT_QTY


async def prod_qty_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Persist product quantity and trigger limit-cross notification logic.
    """
    prod_id = context.user_data.get("prod_qty_id")
    cat_id = context.user_data.get("active_cat_id")
    if not prod_id or not cat_id:
        await update.message.reply_text("Помилка стану. Відкрий категорію і спробуй ще раз.")
        return ConversationHandler.END

    try:
        new_qty = parse_qty(update.message.text)
    except Exception:
        await update.message.reply_text("Кількість має бути числом > 0. Приклад: 3 або 1.5. Введи ще раз:")
        return PROD_EDIT_QTY

    db.update_product_qty(int(prod_id), new_qty)
    await maybe_notify_limit_crossed(context, int(prod_id))

    context.user_data.pop("prod_qty_id", None)
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"✅ Кількість оновлено: {new_qty}", reply_markup=bottom_kb(chat_id))
    await show_products_as_reply(update.message, context, int(cat_id))
    return ConversationHandler.END


async def prod_limit_from_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Entry point for updating product limit.
    """
    q = update.callback_query
    await q.answer()

    prod_id = int((q.data or "").split(":")[2])
    prod = db.get_product(prod_id)
    if not prod:
        await q.message.reply_text("Продукт не знайдено (можливо видалений).")
        return ConversationHandler.END

    _, cat_id, name, qty, limit_qty, _ = prod
    context.user_data["active_cat_id"] = cat_id
    context.user_data["prod_limit_id"] = prod_id

    limit_text = "—" if limit_qty is None else str(limit_qty)
    await q.message.reply_text(
        f"Продукт: {name}\nКількість: {qty}\nПоточний ліміт: {limit_text}\n\n"
        "Введи НОВИЙ ліміт (число > 0).\n"
        "Щоб прибрати ліміт — введи '-' або 0:",
        reply_markup=cancel_keyboard("prod"),
    )
    return PROD_EDIT_LIMIT


async def prod_limit_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Persist product limit and trigger limit-cross notification logic.
    """
    prod_id = context.user_data.get("prod_limit_id")
    cat_id = context.user_data.get("active_cat_id")
    if not prod_id or not cat_id:
        await update.message.reply_text("Помилка стану. Відкрий категорію і спробуй ще раз.")
        return ConversationHandler.END

    new_limit = parse_limit(update.message.text)
    db.update_product_limit(int(prod_id), new_limit)
    await maybe_notify_limit_crossed(context, int(prod_id))

    context.user_data.pop("prod_limit_id", None)
    chat_id = update.effective_chat.id

    msg = "✅ Ліміт прибрано." if new_limit is None else f"✅ Ліміт встановлено: {new_limit}"
    await update.message.reply_text(msg, reply_markup=bottom_kb(chat_id))
    await show_products_as_reply(update.message, context, int(cat_id))
    return ConversationHandler.END


def register_product_conversations(app: Application) -> None:
    """
    Register ConversationHandlers for product flows.
    """
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(prod_add_from_button, pattern=r"^prod:add:\d+$")],
        states={
            PROD_ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, prod_add_name)],
            PROD_ADD_QTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, prod_add_qty)],
        },
        fallbacks=[CallbackQueryHandler(on_cancel, pattern=r"^(cat:cancel|prod:cancel)$")],
        allow_reentry=True,
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(prod_rename_from_button, pattern=r"^prod:rename:\d+$")],
        states={PROD_EDIT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, prod_rename_name)]},
        fallbacks=[CallbackQueryHandler(on_cancel, pattern=r"^(cat:cancel|prod:cancel)$")],
        allow_reentry=True,
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(prod_qty_from_button, pattern=r"^prod:qty:\d+$")],
        states={PROD_EDIT_QTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, prod_qty_value)]},
        fallbacks=[CallbackQueryHandler(on_cancel, pattern=r"^(cat:cancel|prod:cancel)$")],
        allow_reentry=True,
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(prod_limit_from_button, pattern=r"^prod:limit:\d+$")],
        states={PROD_EDIT_LIMIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, prod_limit_value)]},
        fallbacks=[CallbackQueryHandler(on_cancel, pattern=r"^(cat:cancel|prod:cancel)$")],
        allow_reentry=True,
    ))
