from dataclasses import dataclass
from typing import Optional

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from app.storage import db
from app.bot_ui.screens import (
    safe_edit_message,
    render_categories_edit,
    render_category_edit,
    render_product_edit,
    send_categories_reply,
    send_category_reply, render_tasks_cat_edit, render_tasks_edit, render_task_edit, send_tasks_reply,
)
from app.bot_ui.keyboards import category_actions_keyboard


# ---------- Parsing ----------

@dataclass(frozen=True)
class Callback:
    scope: str            # nav | cat | prod
    action: str           # open | del | del_yes | actions | cats
    entity_id: Optional[int] = None


def parse_callback(data: str) -> Optional[Callback]:
    """
    Parse callback_data in format:
    - nav:cats
    - cat:open:<id>
    - cat:del:<id>
    - cat:del_yes:<id>
    - cat:actions:<id>
    - prod:open:<id>
    - prod:del:<id>
    - prod:del_yes:<id>
    """
    parts = (data or "").split(":")
    if len(parts) == 2:
        return Callback(scope=parts[0], action=parts[1], entity_id=None)

    if len(parts) == 3:
        scope, action, raw_id = parts
        if raw_id.isdigit():
            return Callback(scope=scope, action=action, entity_id=int(raw_id))

    return None


def confirm_kb(yes_cb: str, no_cb: str) -> InlineKeyboardMarkup:
    """
    Build a standard confirmation keyboard (Yes/No).
    """
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Так, видалити", callback_data=yes_cb),
        InlineKeyboardButton("❌ Ні", callback_data=no_cb),
    ]])


# ---------- Handlers ----------

async def handle_nav(q: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, cb: Callback) -> None:
    """
    Handle navigation callbacks.
    """
    if cb.action == "cats":
        context.user_data.pop("active_cat_id", None)
        await render_categories_edit(q, context)
        return

    if cb.action == "task_proc":
        context.user_data.pop("active_task_proc_id", None)
        await render_tasks_cat_edit(q, context)
        return


async def handle_cat(q: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, cb: Callback) -> None:
    """
    Handle category-related callbacks.
    """
    cat_id = cb.entity_id
    if cat_id is None:
        return

    if cb.action == "open":
        context.user_data["active_cat_id"] = cat_id
        context.user_data.pop("active_prod_id", None)
        await render_category_edit(q, context, cat_id)
        return

    if cb.action == "actions":
        cat = db.get_category(cat_id)
        if not cat:
            await q.message.reply_text("Категорію не знайдено.")
            return

        await safe_edit_message(
            q,
            text=f"📦 Категорія: {cat[1]}",
            reply_markup=category_actions_keyboard(cat_id),
        )
        return

    if cb.action == "del":
        cat = db.get_category(cat_id)
        if not cat:
            await q.message.reply_text("Категорію не знайдено.")
            return

        kb = confirm_kb(
            yes_cb=f"cat:del_yes:{cat_id}",
            no_cb="nav:cats",
        )
        await q.message.reply_text(f"Точно видалити категорію «{cat[1]}»?", reply_markup=kb)
        return

    if cb.action == "del_yes":
        db.delete_category(cat_id)

        # Remove inline keyboard from the old message to prevent further clicks
        await safe_edit_message(q, text=q.message.text or " ", reply_markup=None)

        await q.message.reply_text("🗑️ Категорію видалено.")
        await send_categories_reply(q.message, context)
        return


async def handle_prod(q: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, cb: Callback) -> None:
    """
    Handle product-related callbacks.
    """
    prod_id = cb.entity_id
    if prod_id is None:
        return

    if cb.action == "open":
        context.user_data["active_prod_id"] = prod_id
        await render_product_edit(q, context, prod_id)
        return

    if cb.action == "del":
        prod = db.get_product(prod_id)
        if not prod:
            await q.message.reply_text("Продукт не знайдено.")
            return

        _, cat_id, name, qty, _, _ = prod
        context.user_data["active_cat_id"] = cat_id

        kb = confirm_kb(
            yes_cb=f"prod:del_yes:{prod_id}",
            no_cb=f"prod:open:{prod_id}",
        )
        await q.message.reply_text(f"Точно видалити продукт «{name} — {qty}»?", reply_markup=kb)
        return

    if cb.action == "del_yes":
        prod = db.get_product(prod_id)
        if not prod:
            await q.message.reply_text("Продукт не знайдено.")
            return

        _, cat_id, _, _, _, _ = prod
        db.delete_product(prod_id)

        await q.message.reply_text("🗑️ Продукт видалено.")
        await send_category_reply(q.message, context, int(cat_id))
        return


async def handle_tasks_cat(q: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, cb: Callback) -> None:
    """
    Handle tasks category callbacks.
    """
    tc_id = cb.entity_id
    if cb.action == "open":
        context.user_data["active_tc_id"] = tc_id
        await render_tasks_edit(q, context, tc_id)
        return


async def handle_tasks(q: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, cb: Callback) -> None:
    """
    Handle tasks callbacks.
    """
    task_id = cb.entity_id
    if cb.action == "open":
        context.user_data["active_task_id"] = task_id
        await render_task_edit(q, context, task_id)
        return

    if cb.action == "done":
        task = db.get_task(task_id)
        if not task:
            await q.message.reply_text("Завдання не знайдено.")
            return

        task_id, task_text, task_cat_id = task
        db.set_task_done(task_id, 1)

        await q.message.reply_text("✅ Завдання виконано!")
        await send_tasks_reply(q.message, context, int(task_cat_id))
        return


# ---------- Entry point ----------

async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Main callback router: parses callback_data and dispatches to specific handlers.
    """
    q = update.callback_query
    await q.answer()

    cb = parse_callback(q.data or "")
    if not cb:
        return

    if cb.scope == "nav":
        await handle_nav(q, context, cb)
        return

    if cb.scope == "cat":
        await handle_cat(q, context, cb)
        return

    if cb.scope == "prod":
        await handle_prod(q, context, cb)
        return

    if cb.scope == "task_proc":
        await handle_tasks_cat(q, context, cb)
        return

    if cb.scope == "task":
        await handle_tasks(q, context, cb)
        return


def register_callback_handlers(app: Application) -> None:
    """
    Register generic callback handler.
    """
    app.add_handler(CallbackQueryHandler(callbacks))
