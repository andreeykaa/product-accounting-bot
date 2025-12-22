from telegram.ext import Application

from app.config import get_bot_token
from app.handlers.conversations.tasks import register_task_conversations
from app.storage import db
from app.handlers.commands import register_command_handlers
from app.handlers.bottom_menu import register_bottom_menu_handlers
from app.handlers.callbacks import register_callback_handlers
from app.handlers.conversations.categories import register_category_conversations
from app.handlers.conversations.products import register_product_conversations


def main() -> None:
    """
    App entrypoint: initialize DB, build Telegram application, register handlers, run polling.
    """
    db.init_db()

    token = get_bot_token()
    app = Application.builder().token(token).build()

    register_command_handlers(app)
    register_bottom_menu_handlers(app)
    register_category_conversations(app)
    register_product_conversations(app)
    register_task_conversations(app)
    register_callback_handlers(app)

    app.run_polling()


if __name__ == "__main__":
    main()
