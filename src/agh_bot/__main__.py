import asyncio
import logging
from pathlib import Path
import sys

import i18n

from agh_bot.features.anecdotes import monitor_chat_activity, prepare_anecdotes
from agh_bot.features.captcha import monitor_captcha_timeout
from agh_bot.router import ROUTER
from agh_bot.loader import BOT, DB, DP
from agh_bot.config import CONFIG


@DP.startup()
async def on_startup() -> None:
    prepare_anecdotes()
    asyncio.create_task(monitor_chat_activity())
    asyncio.create_task(monitor_captcha_timeout())


def setup_i18n() -> None:
    i18n.set("locale", CONFIG.LOCALE)
    i18n.set("filename_format", "{locale}.{format}")
    i18n.set("skip_locale_root_data", True)
    i18n.set("on_missing_translation", "error")
    i18n.load_path.append(str(Path(__file__).parent / "locales"))


async def main() -> None:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    setup_i18n()
    await DB.create_tables()
    DP.include_router(ROUTER)

    try:
        await DP.start_polling(BOT)
    except asyncio.CancelledError:
        pass
    finally:
        await DB.disconnect()
        logging.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
