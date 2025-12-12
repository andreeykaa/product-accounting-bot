from dotenv import dotenv_values


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
