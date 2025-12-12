from typing import Final

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from peewee_aio import Manager

from agh_bot.config import CONFIG

DP: Final = Dispatcher()
BOT: Final = Bot(
    token=CONFIG.BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.MARKDOWN,
    ),
)

DB: Final = Manager(
    f"postgresql://{CONFIG.POSTGRES_USER}:{CONFIG.POSTGRES_PASSWORD}@{CONFIG.POSTGRES_HOST}/{CONFIG.POSTGRES_DB}",
)
