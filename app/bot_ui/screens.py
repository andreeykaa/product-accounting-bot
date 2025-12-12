from telegram.error import BadRequest
from telegram.ext import ContextTypes

from app.storage import db
from app.bot_ui.keyboards import categories_keyboard, products_keyboard


async def safe_edit_message(query, text: str, reply_markup=None) -> None:
    """
    Edit a message safely: ignore "Message is not modified" errors.
    """
    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            raise


async def show_categories_as_reply(message, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Send categories list as a new message.
    """
    rows = db.list_categories()
    text = "Категорії:" if rows else "Категорій поки немає. Натисни «Додати категорію»."
    await message.reply_text(text, reply_markup=categories_keyboard(rows))


async def show_categories_as_edit(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Update categories list by editing the current inline-message.
    """
    rows = db.list_categories()
    text = "Категорії:" if rows else "Категорій поки немає. Натисни «Додати категорію»."
    await safe_edit_message(query, text, reply_markup=categories_keyboard(rows))


async def show_products_as_edit(query, context: ContextTypes.DEFAULT_TYPE, cat_id: int) -> None:
    """
    Update products list for a category by editing the current inline-message.
    """
    cat = db.get_category(cat_id)
    if not cat:
        await query.message.reply_text("Категорію не знайдено (можливо видалена).")
        return

    products_rows = db.list_products_by_category(cat_id)
    text = f"📦 Категорія: {cat[1]}" if products_rows else f"📦 Категорія: {cat[1]}\n\nПродуктів поки немає."
    await safe_edit_message(query, text, reply_markup=products_keyboard(cat_id, products_rows))


async def show_products_as_reply(message, context: ContextTypes.DEFAULT_TYPE, cat_id: int) -> None:
    """
    Send products list for a category as a new message.
    """
    cat = db.get_category(cat_id)
    if not cat:
        await message.reply_text("Категорію не знайдено (можливо видалена).")
        return

    products_rows = db.list_products_by_category(cat_id)
    text = f"📦 Категорія: {cat[1]}" if products_rows else f"📦 Категорія: {cat[1]}\n\nПродуктів поки немає."
    await message.reply_text(text, reply_markup=products_keyboard(cat_id, products_rows))
