from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from app.storage import db
from app.bot_ui.screens import render_categories_edit, render_category_edit, safe_edit_message, \
    send_categories_reply, render_product_edit, send_category_reply
from app.bot_ui.keyboards import category_actions_keyboard


async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle non-conversation inline callbacks: navigation and delete confirmations.
    """
    q = update.callback_query
    await q.answer()

    data = q.data or ""
    parts = data.split(":")

    if data == "nav:cats":
        context.user_data.pop("active_cat_id", None)
        await render_categories_edit(q, context)
        return

    if len(parts) == 3 and parts[0] == "cat" and parts[1] == "open":
        cat_id = int(parts[2])
        context.user_data["active_cat_id"] = cat_id
        await render_category_edit(q, context, cat_id)
        return

    # Category delete confirmation
    if len(parts) == 3 and parts[0] == "cat" and parts[1] == "del":
        cat_id = int(parts[2])
        cat = db.get_category(cat_id)
        if not cat:
            await q.message.reply_text("Категорію не знайдено.")
            return

        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Так, видалити", callback_data=f"cat:del_yes:{cat_id}"),
            InlineKeyboardButton("❌ Ні", callback_data="nav:cats"),
        ]])
        await q.message.reply_text(f"Точно видалити категорію «{cat[1]}»?", reply_markup=kb)
        return

    if len(parts) == 3 and parts[0] == "cat" and parts[1] == "del_yes":
        cat_id = int(parts[2])
        db.delete_category(cat_id)

        # don't edit old message text at all, just remove its keyboard
        await safe_edit_message(q, text=q.message.text or " ", reply_markup=None)

        await q.message.reply_text("🗑️ Категорію видалено.")
        await send_categories_reply(q.message, context)
        return

    if len(parts) == 3 and parts[0] == "cat" and parts[1] == "actions":
        cat_id = int(parts[2])

        cat = db.get_category(cat_id)
        if not cat:
            await q.message.reply_text("Категорію не знайдено.")
            return

        # Show actions menu for the category (edit message in-place)
        await safe_edit_message(
            q,
            text=f"📦 Категорія: {cat[1]}",
            reply_markup=category_actions_keyboard(cat_id),
        )
        return

    if len(parts) == 3 and parts[0] == "prod" and parts[1] == "open":
        prod_id = int(parts[2])
        await render_product_edit(q, context, prod_id)
        return

    # Product delete confirmation
    if len(parts) == 3 and parts[0] == "prod" and parts[1] == "del":
        prod_id = int(parts[2])
        prod = db.get_product(prod_id)
        if not prod:
            await q.message.reply_text("Продукт не знайдено.")
            return

        _, cat_id, name, qty, _, _ = prod
        context.user_data["active_cat_id"] = cat_id

        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Так, видалити", callback_data=f"prod:del_yes:{prod_id}"),
            InlineKeyboardButton("❌ Ні", callback_data=f"cat:open:{cat_id}"),
        ]])
        await q.message.reply_text(f"Точно видалити продукт «{name} — {qty}»?", reply_markup=kb)
        return

    if len(parts) == 3 and parts[0] == "prod" and parts[1] == "del_yes":
        prod_id = int(parts[2])
        prod = db.get_product(prod_id)
        if not prod:
            await q.message.reply_text("Продукт не знайдено.")
            return

        _, cat_id, _, _, _, _ = prod
        db.delete_product(prod_id)

        await q.message.reply_text("🗑️ Продукт видалено.")
        await send_category_reply(q.message, context, int(cat_id))
        return


def register_callback_handlers(app: Application) -> None:
    """
    Register generic callback handler.
    """
    app.add_handler(CallbackQueryHandler(
        callbacks,
        pattern=r"^(nav:cats|cat:open:\d+|cat:actions:\d+|cat:del:\d+|cat:del_yes:\d+|prod:open:\d+|prod:del:\d+|prod:del_yes:\d+)$"
    ))
