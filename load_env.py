import os
from pathlib import Path

from dotenv import load_dotenv

IS_LOADED = False

__all__ = ("is_loaded", "load_env", "set_loaded")


def is_loaded() -> bool:
    return IS_LOADED


def set_loaded() -> None:
    global IS_LOADED
    IS_LOADED = True


def load_env() -> None:
    if is_loaded():
        return

    load_dotenv(override=True)

    if os.environ.get("DOCKER_MODE") in {"true", "True", "TRUE", "t", "T", "1"}:
        os.environ["DB_URL"] = (
            f"postgres://postgres:{os.environ['POSTGRES_PASSWORD']}@db:5432/postgres"
        )

    file_location = Path(__file__).parent.absolute().as_posix()
    os.environ["DIRECTORY_OF_FILE"] = file_location
    os.environ["LOG_FILE_PATH"] = f"{file_location}/discord.log"

    set_loaded()
