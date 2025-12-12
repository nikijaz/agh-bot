import asyncio
import hashlib
import logging
from pathlib import Path
import random
import time
from typing import NoReturn

from aiogram.enums import ChatType, ContentType
from aiogram.exceptions import AiogramError
from aiogram.types import Message
from croniter import croniter
from i18n import t
from peewee import SQL, fn

from agh_bot.loader import BOT
from agh_bot.config import CONFIG
from agh_bot.models import AnecdoteHistory, ChatState, OutOfAnecdotesHistory

ANECDOTE_MAP: dict[str, str] = dict()
ANECDOTE_HASHES: set[str] = set()


def prepare_anecdotes() -> None:
    def hash(anecdote: str) -> str:
        return hashlib.sha1(anecdote.encode()).hexdigest()[:32]

    global ANECDOTE_MAP, ANECDOTE_HASHES
    content = Path("anecdotes.txt").read_text(encoding="utf-8")
    anecdotes = [anecdote.strip() for anecdote in content.split("***")]
    ANECDOTE_MAP = {hash(anecdote): anecdote for anecdote in anecdotes}
    ANECDOTE_HASHES = set(ANECDOTE_MAP.keys())


CRON = croniter(CONFIG.ACTIVITY_HANDLER_SCHEDULE, second_at_beginning=True)


async def monitor_chat_activity() -> NoReturn:
    while True:
        # Get inactive chats
        result = await ChatState.select().where(
            ChatState.last_activity < SQL(f"NOW() - INTERVAL '{CONFIG.ACTIVITY_TIMEOUT_SECONDS} seconds'"),
            ~fn.EXISTS(  # Ensure we haven't sent an anecdote recently
                AnecdoteHistory.select().where(
                    AnecdoteHistory.chat_id == ChatState.chat_id,
                    AnecdoteHistory.inserted_at > SQL(f"NOW() - INTERVAL '{CONFIG.ACTIVITY_TIMEOUT_SECONDS} seconds'"),
                )
            ),
        )

        # Handle each inactive chat
        for chat_state in result:
            try:
                await handle_inactivity(chat_state.chat_id)
            except AiogramError as e:
                logging.error(f"Handling inactivity for chat {chat_state.chat_id} failed: {e}")

        # Wait until the next scheduled check
        current_time = time.time()
        await asyncio.sleep(CRON.get_next(start_time=current_time) - current_time)


async def handle_inactivity(chat_id: int) -> None:
    # Get unused anecdotes' hashes for this chat
    result = await AnecdoteHistory.select().where(AnecdoteHistory.chat_id == chat_id)
    used_hashes = {record.anecdote_hash for record in result}
    unused_hashes = list(ANECDOTE_HASHES - used_hashes)

    # If there is an unused anecdote, send it
    if unused_hashes:
        anecdote_hash = random.choice(unused_hashes)
        await BOT.send_message(chat_id, ANECDOTE_MAP[anecdote_hash])
        await AnecdoteHistory.insert(
            anecdote_hash=anecdote_hash,
            chat_id=chat_id,
        )
        return

    # Check if we have already notified about running out of anecdotes recently
    was_notified = (
        await OutOfAnecdotesHistory.select()
        .where(
            OutOfAnecdotesHistory.chat_id == chat_id,
            OutOfAnecdotesHistory.inserted_at
            > SQL(f"NOW() - INTERVAL '{CONFIG.OUT_OF_ANECDOTES_INTERVAL_SECONDS} seconds'"),
        )
        .exists()
    )

    # If not, notify the chat and record the notification
    if not was_notified:
        await BOT.send_message(chat_id, t("anecdote.message.out_of_anecdotes"))
        await OutOfAnecdotesHistory.insert(chat_id=chat_id)


async def record_activity(message: Message) -> None:
    if message.chat.type == ChatType.PRIVATE:
        return

    if not message.from_user or message.from_user.is_bot:
        return

    if message.content_type != ContentType.TEXT:
        return

    await ChatState.insert(
        chat_id=message.chat.id,
        last_activity=message.date,
    ).on_conflict(
        conflict_target=[ChatState.chat_id],
        update={ChatState.last_activity: message.date},
    )
