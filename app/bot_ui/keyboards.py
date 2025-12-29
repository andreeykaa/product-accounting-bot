from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

from app.config import PROCESSES, TARGETS_CARD
from app.storage import db


def bottom_kb(chat_id: int) -> ReplyKeyboardMarkup:
    """
    Build persistent bottom (reply) keyboard.
    """
    subscribed = db.is_subscriber(chat_id)
    sub_btn = KeyboardButton("🔕 Відписатися") if subscribed else KeyboardButton("🔔 Підписатися")

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("🏠 Категорії"), KeyboardButton("📝 Список завдань")],
            [KeyboardButton("📝 Дозамовити"), KeyboardButton("📝 Тех-карти")],
            [KeyboardButton("🔄 Оновити дані"), sub_btn]
        ],
        resize_keyboard=True,
    )


def categories_keyboard(rows):
    """
    Inline keyboard for categories list.
    """
    kb = [[InlineKeyboardButton("➕ Додати категорію", callback_data="cat:add")]]
    for cat_id, name in rows:
        kb.append([
            InlineKeyboardButton(f"📦 {name}", callback_data=f"cat:open:{cat_id}")
        ])
    return InlineKeyboardMarkup(kb)


def category_actions_keyboard(cat_id: int):
    """
    Build inline keyboard for category actions (rename/delete).
    """
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✏️ Редагувати", callback_data=f"cat:edit:{cat_id}"),
            InlineKeyboardButton("🗑️ Видалити", callback_data=f"cat:del:{cat_id}"),
        ],
        [
            InlineKeyboardButton("⬅️ Назад", callback_data=f"cat:open:{cat_id}"),
        ]
    ])


def products_keyboard(cat_id: int, products_rows):
    """
    Inline keyboard for products inside a category.
    """
    kb = [[
        InlineKeyboardButton("⚙️ Дії з категорією", callback_data=f"cat:actions:{cat_id}"),
        InlineKeyboardButton("➕ Додати продукт", callback_data=f"prod:add:{cat_id}")
    ]]

    for prod_id, name, _, _ in products_rows:
        kb.append([InlineKeyboardButton(f"🏷️ {name}", callback_data=f"prod:open:{prod_id}")])

    kb.append([InlineKeyboardButton("⬅️ Назад до категорій", callback_data="nav:cats")])
    return InlineKeyboardMarkup(kb)


def product_view_keyboard(prod_id: int, cat_id: int, qty: float, limit_qty: float | None):
    """
    Inline keyboard for a single product screen.
    Shows product actions + qty/limit controls.
    """
    limit_text = "—" if limit_qty is None else str(limit_qty)

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✏️ Редагувати", callback_data=f"prod:edit:{prod_id}"),
            InlineKeyboardButton("🗑️ Видалити", callback_data=f"prod:del:{prod_id}"),
        ],
        [
            InlineKeyboardButton(f"🔢 К-сть: {qty}", callback_data=f"prod:qty:{prod_id}"),
            InlineKeyboardButton(f"⚠️ Мін к-сть: {limit_text}", callback_data=f"prod:limit:{prod_id}"),
        ],
        [InlineKeyboardButton("⬅️ Назад до категорії", callback_data=f"cat:open:{cat_id}")]
    ])


def tasks_cat_keyboard():
    tasks_cat = PROCESSES.items()
    kb = []

    for tc_id, data in tasks_cat:
        kb.append([InlineKeyboardButton(f"{data['name']}", callback_data=f"task_proc:open:{tc_id}")])

    return InlineKeyboardMarkup(kb)


def tasks_keyboard(tc_id: int, tasks_rows):
    """
    Inline keyboard for products inside a category.
    """
    kb = [
        [InlineKeyboardButton("➕ Додати завдання", callback_data=f"task_proc:add:{tc_id}")]
    ]

    for i, (task_id, task_text, task_cat_id) in enumerate(tasks_rows, start=1):
        kb.append([InlineKeyboardButton(f"{i}. {task_text}", callback_data=f"task:open:{task_id}")])

    kb.append([InlineKeyboardButton("⬅️ Назад до процесів", callback_data="nav:task_proc")])

    return InlineKeyboardMarkup(kb)


def task_view_keyboard(task_id: int, task_cat_id: int | None):
    tasks_cat_name = PROCESSES[task_cat_id]['name']
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✏️ Редагувати", callback_data=f"task:edit:{task_id}"),
            InlineKeyboardButton("✅ Виконано", callback_data=f"task:done:{task_id}"),
        ],
        [InlineKeyboardButton(f"⬅️ Назад до {tasks_cat_name}", callback_data=f"task_proc:open:{task_cat_id}")]
    ])


def tech_cards_cat_keyboard():
    cards_cat = PROCESSES.items()
    kb = []

    for tcc_id, data in cards_cat:
        kb.append([InlineKeyboardButton(f"{data['name']}", callback_data=f"tech_cat:open:{tcc_id}")])

    return InlineKeyboardMarkup(kb)


def tech_cards_type_keyboard():
    EMOJI_BY_TARGET = {
        "dish": "🍽",
        "prep": "🥣",
    }

    cards_type = TARGETS_CARD.items()
    kb = []

    for target_id, data in cards_type:
        emoji = EMOJI_BY_TARGET.get(data["key"], "")
        kb.append([InlineKeyboardButton(f"{emoji} {data['name']}", callback_data=f"tech_type:open:{target_id}")])

    kb.append([InlineKeyboardButton("⬅️ Назад до процесів", callback_data="nav:tech_cat")])

    return InlineKeyboardMarkup(kb)


def tech_cards_keyboard(card_cat_id: int, card_type_id: int, card_rows):

    """
    Inline keyboard for products inside a category.
    """
    kb = [
        [InlineKeyboardButton("➕ Додати тех-карту", callback_data=f"tech_card:add:{card_cat_id}:{card_type_id}")]
    ]

    for card in card_rows:
        kb.append([InlineKeyboardButton(f"{card['name']}", callback_data=f"tech_card:open:{card['card_id']}")])

    kb.append([InlineKeyboardButton("⬅️ Назад до типів", callback_data="nav:tech_type")])

    return InlineKeyboardMarkup(kb)


def cancel_keyboard(prefix: str):
    """
    Inline cancel button used in conversation flows.
    """
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Скасувати", callback_data=f"{prefix}:cancel")]])
