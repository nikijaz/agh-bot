import asyncio
import hashlib
import logging
import random
import time
from typing import NoReturn

from aiogram.exceptions import AiogramError
from aiogram.types import Message
from croniter import croniter
from i18n import t
from peewee import SQL, fn

from src import BOT
from src.config import CONFIG
from src.models import AnecdoteHistory, ChatState, OutOfAnecdotesHistory


def setup() -> None:
    asyncio.create_task(_monitor_chat_activity())


async def _monitor_chat_activity() -> NoReturn:
    while True:
        chat_states = await ChatState.select().where(
            ChatState.last_activity < SQL(f"NOW() - INTERVAL '{CONFIG.ACTIVITY_TIMEOUT_SECONDS} seconds'"),
            ~fn.EXISTS(  # Ensure we haven't sent an anecdote recently
                AnecdoteHistory.select().where(
                    AnecdoteHistory.chat_id == ChatState.chat_id,
                    AnecdoteHistory.inserted_at > SQL(f"NOW() - INTERVAL '{CONFIG.ACTIVITY_TIMEOUT_SECONDS} seconds'"),
                )
            ),
        )

        for chat_state in chat_states:
            try:
                await _handle_inactivity(chat_state.chat_id)
            except AiogramError as e:
                logging.error(f"Handling inactivity for chat {chat_state.chat_id} failed: {e}")

        current_time = time.time()
        sleep_till = croniter(CONFIG.ACTIVITY_HANDLER_SCHEDULE, current_time, second_at_beginning=True).get_next()
        await asyncio.sleep(sleep_till - current_time)


async def _handle_inactivity(chat_id: int) -> None:
    def hash(anecdote: str) -> str:
        return hashlib.sha1(anecdote.encode()).hexdigest()[:32]

    with open("anecdotes.txt", "r", encoding="utf-8") as file:  # Read anecdotes and split them by "***"
        anecdotes = [a.strip() for a in file.read().split("***")]

    used_anecdotes = await AnecdoteHistory.select().where(AnecdoteHistory.chat_id == chat_id)
    used_hashes = set(a.anecdote_hash for a in used_anecdotes)
    unused_anecdotes = [a for a in anecdotes if hash(a) not in used_hashes]

    # If there are unused anecdotes, send one and record its usage
    # Otherwise, notify that there are no new anecdotes left (but not too often)
    if unused_anecdotes:
        anecdote = random.choice(unused_anecdotes)
        await BOT.send_message(chat_id, anecdote)
        await AnecdoteHistory.insert(
            anecdote_hash=hash(anecdote),
            chat_id=chat_id,
        )
        return

    was_notified = (
        await OutOfAnecdotesHistory.select()
        .where(
            OutOfAnecdotesHistory.chat_id == chat_id,
            OutOfAnecdotesHistory.inserted_at
            > SQL(f"NOW() - INTERVAL '{CONFIG.OUT_OF_ANECDOTES_INTERVAL_SECONDS} seconds'"),
        )
        .exists()
    )

    if not was_notified:
        await BOT.send_message(chat_id, t("anecdote.message.out_of_anecdotes"))
        await OutOfAnecdotesHistory.insert(chat_id=chat_id)


async def record_message_activity(message: Message) -> None:
    await ChatState.insert(
        chat_id=message.chat.id,
        last_activity=message.date,
    ).on_conflict(
        conflict_target=[ChatState.chat_id],
        update={ChatState.last_activity: message.date},
    )
