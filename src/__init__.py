from typing import Final

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.config import CONFIG

DP: Final = Dispatcher()
BOT: Final = Bot(
    token=CONFIG.BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.MARKDOWN,
    ),
)
