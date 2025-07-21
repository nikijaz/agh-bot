import os
from typing import Final

from dotenv import load_dotenv

load_dotenv()

LOCALE: Final = os.getenv("LOCALE")
if LOCALE is None:
    raise ValueError("Locale is not set. Please set the LOCALE environment variable.")

BOT_TOKEN: Final = os.getenv("BOT_TOKEN")
if BOT_TOKEN is None:
    raise ValueError("Bot token is not set. Please set the BOT_TOKEN environment variable.")

POSTGRES_HOST: Final = os.getenv("POSTGRES_HOST")
POSTGRES_USER: Final = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD: Final = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB: Final = os.getenv("POSTGRES_DB")
if None in [POSTGRES_HOST, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB]:
    raise ValueError("PostgreSQL credentials are not set. Please set all required environment variables.")

ACTIVITY_TIMEOUT_SECONDS: Final = int(os.getenv("ACTIVITY_TIMEOUT_SECONDS", 3600))
ACTIVITY_HANDLER_SCHEDULE: Final = os.getenv("ACTIVITY_HANDLER_SCHEDULE", "*/10 * * * * *")

CAPTCHA_TIMEOUT_SECONDS: Final = int(os.getenv("CAPTCHA_TIMEOUT_SECONDS", 60))
