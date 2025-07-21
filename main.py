import asyncio

import i18n

from src import BOT, DP, config
from src.models import DB


async def main() -> None:
    i18n.set("locale", config.LOCALE)
    i18n.set("filename_format", "{locale}.{format}")
    i18n.set("skip_locale_root_data", True)
    i18n.load_path.append("locales")

    await DB.create_tables()

    # Register handlers
    from src import handlers  # noqa: F401

    await DP.start_polling(BOT)


if __name__ == "__main__":
    asyncio.run(main())
