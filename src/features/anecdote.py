import asyncio
import hashlib
import random
import time
from datetime import datetime, timedelta
from typing import Final

from aiogram.types import Message
from croniter import croniter
from i18n import t

from src import BOT, config
from src.config import ACTIVITY_HANDLER_SCHEDULE, ACTIVITY_TIMEOUT_SECONDS
from src.models import AnecdoteHistory, ChatState, OutOfAnecdotesHistory

with open("anecdotes.txt", "r") as file:  # Read anecdotes upon import
    ANECDOTES: Final = [a.strip() for a in file.read().split("***")]


async def record_message_activity(message: Message) -> None:
    await ChatState.insert(
        chat_id=message.chat.id,
        last_activity=message.date,
    ).on_conflict(
        conflict_target=[ChatState.chat_id],
        update={ChatState.last_activity: message.date},
    )


async def _monitor_chat_activity() -> None:
    while True:
        timeout_threshold = datetime.now() - timedelta(seconds=ACTIVITY_TIMEOUT_SECONDS)
        chat_states = await ChatState.select().where(
            ChatState.last_activity < timeout_threshold.timestamp(),
        )

        for chat_state in chat_states:
            await _handle_inactivity(chat_state.chat_id)

        sleep_till = croniter(ACTIVITY_HANDLER_SCHEDULE, time.time(), second_at_beginning=True).get_next()
        await asyncio.sleep(sleep_till - time.time())


if not asyncio.get_event_loop().is_running():
    raise RuntimeError("This feature should only be imported when the event loop is running.")
asyncio.create_task(_monitor_chat_activity())  # Start monitoring chat activity upon import


async def _handle_inactivity(chat_id: int) -> None:
    def hash(anecdote: str) -> str:
        return hashlib.sha1(anecdote.encode()).hexdigest()[:32]

    used_hashes = set(
        a.anecdote_hash
        for a in await AnecdoteHistory.select().where(
            AnecdoteHistory.chat_id == chat_id,
        )
    )
    unused_anecdotes = [a for a in ANECDOTES if hash(a) not in used_hashes]
    if unused_anecdotes:
        anecdote = random.choice(unused_anecdotes)
        await BOT.send_message(chat_id, anecdote)
        await AnecdoteHistory.insert(
            anecdote_hash=hash(anecdote),
            chat_id=chat_id,
        )
        return

    interval_threshold = datetime.now() - timedelta(seconds=config.OUT_OF_ANECDOTES_INTERVAL_SECONDS)
    should_notify = (
        not await OutOfAnecdotesHistory.select()
        .where(
            OutOfAnecdotesHistory.chat_id == chat_id,
            OutOfAnecdotesHistory.inserted_at > interval_threshold,
        )
        .exists()
    )

    if should_notify:
        await BOT.send_message(chat_id, t("anecdote.message.out_of_anecdotes"))
        await OutOfAnecdotesHistory.insert(chat_id=chat_id)
