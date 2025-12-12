from dataclasses import dataclass
import os
from typing import Final

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    BOT_TOKEN: str
    POSTGRES_HOST: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    LOCALE: str
    ACTIVITY_TIMEOUT_SECONDS: int
    ACTIVITY_HANDLER_SCHEDULE: str
    OUT_OF_ANECDOTES_INTERVAL_SECONDS: int
    CAPTCHA_TIMEOUT_SECONDS: int
    MEDDLING_MUTE_SECONDS: int


def _load_config() -> Config:
    load_dotenv()

    return Config(
        BOT_TOKEN=os.environ["BOT_TOKEN"],
        POSTGRES_HOST=os.environ["POSTGRES_HOST"],
        POSTGRES_USER=os.environ["POSTGRES_USER"],
        POSTGRES_PASSWORD=os.environ["POSTGRES_PASSWORD"],
        POSTGRES_DB=os.environ["POSTGRES_DB"],
        LOCALE=os.environ["LOCALE"],
        ACTIVITY_TIMEOUT_SECONDS=int(os.environ["ACTIVITY_TIMEOUT_SECONDS"]),
        ACTIVITY_HANDLER_SCHEDULE=os.environ["ACTIVITY_HANDLER_SCHEDULE"],
        OUT_OF_ANECDOTES_INTERVAL_SECONDS=int(os.environ["OUT_OF_ANECDOTES_INTERVAL_SECONDS"]),
        CAPTCHA_TIMEOUT_SECONDS=int(os.environ["CAPTCHA_TIMEOUT_SECONDS"]),
        MEDDLING_MUTE_SECONDS=int(os.environ["MEDDLING_MUTE_SECONDS"]),
    )


CONFIG: Final = _load_config()
