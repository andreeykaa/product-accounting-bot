import os
from dotenv import load_dotenv


load_dotenv()

TASK_PROCESSES = {
    1: {
        "key": "cold",
        "name": "Холодний процес"
    },
    2: {
        "key": "hot",
        "name": "Гарячий процес"
    },
    3: {
        "key": "delivery",
        "name": "Видача"
    }
}


def get_bot_token() -> str:
    """
    Load BOT_TOKEN from environment variables.

    Raises:
        RuntimeError: If BOT_TOKEN is missing.
    """
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN not found in environment variables")
    return token
