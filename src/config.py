import os
from typing import Final

import toml
from dotenv import load_dotenv

CONFIG_PATH: Final = "config.toml"


class Config:
    def __init__(self) -> None:
        self._load_env()
        self._load_config()

    def _load_env(self) -> None:
        load_dotenv()

        self.BOT_TOKEN: str = os.environ["BOT_TOKEN"]

        self.POSTGRES_HOST: str = os.environ["POSTGRES_HOST"]
        self.POSTGRES_USER: str = os.environ["POSTGRES_USER"]
        self.POSTGRES_PASSWORD: str = os.environ["POSTGRES_PASSWORD"]
        self.POSTGRES_DB: str = os.environ["POSTGRES_DB"]

    def _load_config(self) -> None:
        with open(CONFIG_PATH, "r") as file:
            data = toml.load(file)

        self.LOCALE: str = data["LOCALE"]

        self.ACTIVITY_TIMEOUT_SECONDS: int = data["ACTIVITY_TIMEOUT_SECONDS"]
        self.ACTIVITY_HANDLER_SCHEDULE: str = data["ACTIVITY_HANDLER_SCHEDULE"]
        self.OUT_OF_ANECDOTES_INTERVAL_SECONDS: int = data["OUT_OF_ANECDOTES_INTERVAL_SECONDS"]

        self.CAPTCHA_TIMEOUT_SECONDS: int = data["CAPTCHA_TIMEOUT_SECONDS"]


CONFIG: Final = Config()
