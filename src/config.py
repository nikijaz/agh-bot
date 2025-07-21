import os
from typing import Final

from dotenv import load_dotenv

load_dotenv()

LOCALE: Final = os.getenv("LOCALE", "")
if not LOCALE:
    raise ValueError("Locale is not set. Please set the LOCALE environment variable.")

BOT_TOKEN: Final = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise ValueError("Bot token is not set. Please set the BOT_TOKEN environment variable.")

POSTGRES_URL: Final = os.getenv("POSTGRES_URL", "")
if not POSTGRES_URL:
    raise ValueError("Postgres URL is not set. Please set the POSTGRES_URL environment variable.")

ACTIVITY_TIMEOUT_SECONDS: Final = int(os.getenv("ACTIVITY_TIMEOUT_SECONDS", 3600))
ACTIVITY_HANDLER_SCHEDULE: Final = os.getenv("ACTIVITY_HANDLER_SCHEDULE", "* * * * * */10")

CAPTCHA_TIMEOUT_SECONDS: Final = int(os.getenv("CAPTCHA_TIMEOUT_SECONDS", 60))
