from dotenv import dotenv_values


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


def get_bot_token(env_path: str = ".env") -> str:
    """
    Load BOT_TOKEN from .env.

    Raises:
        RuntimeError: If BOT_TOKEN is missing.
    """
    env = dotenv_values(env_path)
    token = env.get("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN not found in .env")
    return token
