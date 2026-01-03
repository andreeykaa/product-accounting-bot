from telegram.error import BadRequest
from telegram.ext import ContextTypes

from app.config import PROCESSES, TARGETS_CARD
from app.handlers.conversations.common import cleanup_last_tech_photo, cleanup_last_tech_photo_by_chat
from app.storage import db
from app.bot_ui.keyboards import categories_keyboard, products_keyboard, product_view_keyboard, tasks_cat_keyboard, \
    tasks_keyboard, task_view_keyboard, tech_cards_cat_keyboard, tech_cards_type_keyboard, tech_cards_keyboard, \
    tech_card_view_keyboard
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


async def send_tasks_cat_reply(message, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Send the tasks categories list as a new message.

    Behavior:
    - Builds a short screen text
    - Attaches inline keyboard with tasks categories
    """
    text = "Категорії списку завдань:"
    await message.reply_text(text, reply_markup=tasks_cat_keyboard())


async def render_tasks_cat_edit(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Render (update) a tasks category screen by editing the current inline message.

    Behavior:
    - Edits the current message with updated text and inline keyboard
    """
    text = "Категорії списку завдань:"
    await safe_edit_message(query, text, reply_markup=tasks_cat_keyboard())


async def send_tasks_reply(message, context: ContextTypes.DEFAULT_TYPE, tc_id) -> None:
    tasks_cat = PROCESSES[tc_id]['name']
    tasks_rows = db.list_all_tasks_by_category(tc_id)

    if tasks_rows:
        text = f"📋 Список завдань: {tasks_cat}\n\n"
    else:
        text = f"📦 Процес: {tasks_cat}\n\nЗавдань поки немає."

    await message.reply_text(text, reply_markup=tasks_keyboard(tc_id, tasks_rows))


async def render_tasks_edit(query, context: ContextTypes.DEFAULT_TYPE, tc_id) -> None:
    tasks_cat = PROCESSES[tc_id]['name']
    tasks_rows = db.list_all_tasks_by_category(tc_id)

    if tasks_rows:
        text = f"📋 Список завдань: {tasks_cat}\n\n"
    else:
        text = f"📦 Процес: {tasks_cat}\n\nЗавдань поки немає."

    await safe_edit_message(
        query,
        text,
        reply_markup=tasks_keyboard(tc_id, tasks_rows)
    )


async def render_task_edit(query, context: ContextTypes.DEFAULT_TYPE, task_id: int) -> None:
    task = db.get_task(task_id)
    if not task:
        await query.answer("Завдання не знайдено.", show_alert=True)
        return

    task_id, task_text, task_cat_id = task
    text = f"🏷️ Завдання:\n {task_text}"

    await safe_edit_message(
        query,
        text,
        reply_markup=task_view_keyboard(task_id, task_cat_id),
    )


async def send_task_reply(message, context: ContextTypes.DEFAULT_TYPE, task_id: int) -> None:
    task = db.get_task(task_id)
    if not task:
        await message.answer("Завдання не знайдено.", show_alert=True)
        return

    task_id, task_text, task_cat_id = task
    text = f"🏷️ Завдання:\n {task_text}"

    await message.reply_text(
        text,
        reply_markup=task_view_keyboard(task_id, task_cat_id),
    )


async def send_tech_cards_cat_reply(message, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Send the tech cards categories list as a new message.

    Behavior:
    - Builds a short screen text
    - Attaches inline keyboard with tech cards categories
    """
    text = "Категорії технічних карт:"
    await message.reply_text(text, reply_markup=tech_cards_cat_keyboard())


async def render_tech_cards_cat_edit(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Render (update) a tech cards category screen by editing the current inline message.

    Behavior:
    - Edits the current message with updated text and inline keyboard
    """
    text = "Категорії технічних карт:"
    await safe_edit_message(query, text, reply_markup=tech_cards_cat_keyboard())


async def send_tech_cards_type_reply(message, context: ContextTypes.DEFAULT_TYPE, tech_card_cat_id) -> None:
    """
    Send the tech cards types list as a new message.

    Behavior:
    - Builds a short screen text
    - Attaches inline keyboard with tech cards categories
    """
    tech_card_cat = PROCESSES[tech_card_cat_id]['name']
    text = f"{tech_card_cat}\nТехнічні карти для:"
    await message.reply_text(text, reply_markup=tech_cards_type_keyboard())


async def render_tech_cards_type_edit(query, context: ContextTypes.DEFAULT_TYPE, tech_card_cat_id) -> None:
    """
    Render (update) a tech cards types screen by editing the current inline message.

    Behavior:
    - Edits the current message with updated text and inline keyboard
    """
    tech_card_cat = PROCESSES[tech_card_cat_id]['name']
    text = f"{tech_card_cat}\nТехнічні карти для:"
    await safe_edit_message(query, text, reply_markup=tech_cards_type_keyboard())


async def send_tech_cards_reply(message, context: ContextTypes.DEFAULT_TYPE, tech_card_cat_id, tech_card_type_id) -> None:
    card_cat = PROCESSES[tech_card_cat_id]['name']
    card_type = TARGETS_CARD[tech_card_type_id]['name']
    card_rows = db.list_tech_cards(tech_card_cat_id, tech_card_type_id)

    type_emoji = "🍽" if TARGETS_CARD[tech_card_type_id]["key"] == "dish" else "🥣"
    if card_rows:
        text = f"📋 Технічні карти\n{card_cat} · {type_emoji} {card_type}"
    else:
        text = f"📋 Технічні карти\n{card_cat} · {type_emoji} {card_type}\n\nТехнічних карт поки немає."

    await message.reply_text(text, reply_markup=tech_cards_keyboard(tech_card_cat_id, tech_card_type_id, card_rows))


async def render_tech_cards_edit(query, context: ContextTypes.DEFAULT_TYPE, tech_card_cat_id, tech_card_type_id) -> None:
    card_cat = PROCESSES[tech_card_cat_id]['name']
    card_type = TARGETS_CARD[tech_card_type_id]['name']
    card_rows = db.list_tech_cards(tech_card_cat_id, tech_card_type_id)

    type_emoji = "🍽" if TARGETS_CARD[tech_card_type_id]["key"] == "dish" else "🥣"
    if card_rows:
        text = f"📋 Технічні карти\n{card_cat} · {type_emoji} {card_type}"
    else:
        text = f"📋 Технічні карти\n{card_cat} · {type_emoji} {card_type}\n\nТехнічних карт поки немає."

    await safe_edit_message(
        query,
        text,
        reply_markup=tech_cards_keyboard(tech_card_cat_id, tech_card_type_id, card_rows)
    )


async def send_tech_card_reply(message, context: ContextTypes.DEFAULT_TYPE, card_id: int) -> None:
    """
    Send a single tech card screen as a new message.
    Behavior:
    - Loads tech card by id
    - Sends a new message with text + inline keyboard
    - Deletes previously shown tech photo (if any)
    - Sends photo (if exists) and stores its message_id for later deletion
    """
    card = db.get_card(card_id)
    if not card:
        await message.reply_text("Тех-карту не знайдено.")
        return

    _, name, photo_file_id, process_id, target_type = card
    card_cat = PROCESSES[process_id]['name']
    card_type = TARGETS_CARD[target_type]['name']
    type_emoji = "🍽" if TARGETS_CARD[target_type]["key"] == "dish" else "🥣"

    header = f"🗂 Технічні карти\n{card_cat} · {type_emoji} {card_type}"
    text = header + f"\n\nТех-карта: {name}"

    await cleanup_last_tech_photo_by_chat(context, message.chat.id)

    screen_msg = await message.reply_text(
        text,
        reply_markup=tech_card_view_keyboard(card_id, target_type),
    )

    context.user_data["tech_card_screen_chat_id"] = screen_msg.chat.id
    context.user_data["tech_card_screen_message_id"] = screen_msg.message_id
    context.user_data["active_tech_card_id"] = card_id

    if photo_file_id:
        msg = await message.reply_photo(photo=photo_file_id)
        context.user_data["last_tech_photo_card_id"] = card_id
        context.user_data["last_tech_photo_msg_id"] = msg.message_id


async def render_tech_card_edit(query, context: ContextTypes.DEFAULT_TYPE, card_id: int) -> None:
    """
    Render (update) a single tech card screen by editing the current inline message.

    Behavior:
    - Loads tech card by id
    - Edits the current message with text + inline keyboard
    """
    card = db.get_card(card_id)
    if not card:
        await query.answer("Тех-карту не знайдено.", show_alert=True)
        return

    _, name, photo_file_id, process_id, target_type = card
    card_cat = PROCESSES[process_id]['name']
    card_type = TARGETS_CARD[target_type]['name']
    type_emoji = "🍽" if TARGETS_CARD[target_type]["key"] == "dish" else "🥣"

    header = f"🗂 Технічні карти\n{card_cat} · {type_emoji} {card_type}"
    text = header + f"\n\nТех-карта: {name}"

    await safe_edit_message(
        query,
        text,
        reply_markup=tech_card_view_keyboard(card_id, target_type),
    )

    await cleanup_last_tech_photo(query, context)
    if photo_file_id:
        msg = await query.message.reply_photo(photo=photo_file_id)
        context.user_data["last_tech_photo_card_id"] = card_id
        context.user_data["last_tech_photo_msg_id"] = msg.message_id
