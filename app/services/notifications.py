from telegram.error import BadRequest, Forbidden
from telegram.ext import ContextTypes

from app.storage import db


async def maybe_notify_limit_crossed(context: ContextTypes.DEFAULT_TYPE, product_id: int) -> None:
    """
    Notify all subscribers when product quantity crosses the limit threshold
    from above to below-or-equal.

    Uses DB flag `below_limit` to avoid repeated notifications while the item remains below the limit.
    """
    prod = db.get_product(product_id)
    if not prod:
        return

    _, cat_id, name, qty, limit_qty, below_limit = prod

    # No limit => ensure flag is reset
    if limit_qty is None:
        if below_limit:
            db.set_below_limit(product_id, 0)
        return

    is_now_below = qty <= limit_qty

    # Crossed to "below" for the first time -> notify
    if is_now_below and not below_limit:
        cat = db.get_category(cat_id)
        cat_name = cat[1] if cat else "Невідома категорія"

        text = (
            "⚠️ ПОТРІБНО ДОЗАМОВИТИ\n\n"
            f"Категорія: {cat_name}\n"
            f"Продукт: {name}\n"
            f"Кількість: {qty}\n"
            f"Ліміт: {limit_qty}"
        )

        for chat_id in db.list_subscribers():
            try:
                await context.application.bot.send_message(chat_id=chat_id, text=text)
            except Forbidden:
                db.remove_subscriber(chat_id)
            except BadRequest:
                pass

        db.set_below_limit(product_id, 1)
        return

    # Came back above limit -> reset flag
    if (not is_now_below) and below_limit:
        db.set_below_limit(product_id, 0)
