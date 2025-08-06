import asyncio
import logging
import sys

import i18n

from src import BOT, DP, config, handlers
from src.features import anecdote, captcha
from src.models import DB


async def main() -> None:
    i18n.set("locale", config.LOCALE)
    i18n.set("filename_format", "{locale}.{format}")
    i18n.set("skip_locale_root_data", True)
    i18n.load_path.append("locales")

    await DB.create_tables()

    handlers.setup()

    anecdote.setup()
    captcha.setup()

    try:
        await DP.start_polling(BOT)
    except asyncio.CancelledError:
        pass
    finally:
        await DB.disconnect()
        logging.shutdown()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
