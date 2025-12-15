from telegram.error import BadRequest
from telegram.ext import ContextTypes

from app.storage import db
from app.bot_ui.keyboards import categories_keyboard, products_keyboard, product_view_keyboard
from telegram import CallbackQuery


async def safe_edit_message(query: CallbackQuery, text: str, reply_markup=None) -> None:
    """
    Safely edit an inline message (CallbackQuery.message).

    This helper prevents the bot from crashing on Telegram's
    "Message is not modified" error when the new text/markup
    is identical to the current one.

    Args:
        query: CallbackQuery that owns the message to edit.
        text: New message text.
        reply_markup: Optional inline keyboard (InlineKeyboardMarkup).
    """
    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            raise


async def send_categories_reply(message, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Send the categories list as a new message.

    Behavior:
    - Fetches categories from DB
    - Builds a short screen text
    - Attaches inline keyboard with categories
    """
    rows = db.list_categories()
    text = "Категорії:" if rows else "Категорій поки немає. Натисни «Додати категорію»."
    await message.reply_text(text, reply_markup=categories_keyboard(rows))


async def render_categories_edit(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Render (update) the categories list by editing the current inline message.

    Behavior:
    - Fetches categories from DB
    - Builds a short screen text
    - Attaches inline keyboard with categories
    - Edits the current message safely (no crash on "Message is not modified")
    """
    rows = db.list_categories()
    text = "Категорії:" if rows else "Категорій поки немає. Натисни «Додати категорію»."
    await safe_edit_message(query, text, reply_markup=categories_keyboard(rows))


async def render_category_edit(query, context: ContextTypes.DEFAULT_TYPE, cat_id: int) -> None:
    """
    Render (update) a single category screen by editing the current inline message.

    Screen:
    - Title: 📦 Категорія: <name>
    - Buttons: category actions + add product + products list + back

    Behavior:
    - Loads category by id
    - Loads products for that category
    - Edits the current message with updated text and inline keyboard
    """
    cat = db.get_category(cat_id)
    if not cat:
        await query.message.reply_text("Категорію не знайдено.")
        return

    products_rows = db.list_products_by_category(cat_id)
    text = f"📦 Категорія: {cat[1]}" if products_rows else f"📦 Категорія: {cat[1]}\n\nПродуктів поки немає."
    await safe_edit_message(query, text, reply_markup=products_keyboard(cat_id, products_rows))


async def send_category_reply(message, context: ContextTypes.DEFAULT_TYPE, cat_id: int) -> None:
    """
    Send a single category screen as a new message.

    Screen:
    - Title: 📦 Категорія: <name>
    - Buttons: category actions + add product + products list + back

    Behavior:
    - Loads category by id
    - Loads products for that category
    - Sends a new message with text + inline keyboard
    """
    cat = db.get_category(cat_id)
    if not cat:
        await message.reply_text("Категорію не знайдено.")
        return

    products_rows = db.list_products_by_category(cat_id)
    text = f"📦 Категорія: {cat[1]}" if products_rows else f"📦 Категорія: {cat[1]}\n\nПродуктів поки немає."
    await message.reply_text(text, reply_markup=products_keyboard(cat_id, products_rows))


async def render_product_edit(query, context: ContextTypes.DEFAULT_TYPE, prod_id: int) -> None:
    """
    Render (update) a single product screen by editing the current inline message.

    Screen:
    - Title: 🏷️ Продукт: <name>
    - Buttons: edit/delete + qty/limit + back to category

    Behavior:
    - Loads product by id
    - Edits the current message with text + inline keyboard
    """
    row = db.get_product(prod_id)
    if not row:
        await query.answer("Продукт не знайдено.", show_alert=True)
        return

    prod_id, cat_id, name, qty, limit_qty, below_limit = row
    text = f"🏷️ Продукт: {name}"

    await safe_edit_message(
        query,
        text,
        reply_markup=product_view_keyboard(prod_id, cat_id, qty, limit_qty),
    )


async def send_product_reply(message, context: ContextTypes.DEFAULT_TYPE, prod_id: int) -> None:
    """
    Send a single product screen as a new message.

    Screen:
    - Title: 🏷️ Продукт: <name>
    - Buttons: edit/delete + qty/limit + back to category

    Behavior:
    - Loads product by id
    - Sends a new message with text + inline keyboard
    """
    row = db.get_product(prod_id)
    if not row:
        await message.reply_text("Продукт не знайдено.")
        return

    prod_id, cat_id, name, qty, limit_qty, below_limit = row
    text = f"🏷️ Продукт: {name}"

    await message.reply_text(
        text,
        reply_markup=product_view_keyboard(prod_id, cat_id, qty, limit_qty),
    )
