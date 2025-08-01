import asyncio
import hashlib
import random
import time

from aiogram.types import Message
from croniter import croniter
from i18n import t
from peewee import SQL, fn

from src import BOT, config
from src.config import ACTIVITY_HANDLER_SCHEDULE
from src.models import AnecdoteHistory, ChatState, OutOfAnecdotesHistory


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
        chat_states = await ChatState.select().where(
            ChatState.last_activity < SQL(f"NOW() - INTERVAL '{config.ACTIVITY_TIMEOUT_SECONDS} seconds'"),
            ~fn.EXISTS(  # Ensure there are no recent anecdotes
                AnecdoteHistory.select().where(
                    AnecdoteHistory.chat_id == ChatState.chat_id,
                    AnecdoteHistory.inserted_at > SQL(f"NOW() - INTERVAL '{config.ACTIVITY_TIMEOUT_SECONDS} seconds'"),
                )
            ),
        )  # fmt: skip

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

    with open("anecdotes.txt", "r") as file:
        anecdotes = [a.strip() for a in file.read().split("***")]

    used_hashes = set(
        a.anecdote_hash
        for a in await AnecdoteHistory.select().where(
            AnecdoteHistory.chat_id == chat_id,
        )
    )
    unused_anecdotes = [a for a in anecdotes if hash(a) not in used_hashes]
    if unused_anecdotes:
        anecdote = random.choice(unused_anecdotes)
        await BOT.send_message(chat_id, anecdote)
        await AnecdoteHistory.insert(
            anecdote_hash=hash(anecdote),
            chat_id=chat_id,
        )
        return

    should_notify = await OutOfAnecdotesHistory.select().where(
            OutOfAnecdotesHistory.chat_id == chat_id,
            OutOfAnecdotesHistory.inserted_at > SQL(f"NOW() - INTERVAL '{config.OUT_OF_ANECDOTES_INTERVAL_SECONDS} seconds'"),
    ).count() == 0  # fmt: skip

    if should_notify:
        await BOT.send_message(chat_id, t("anecdote.message.out_of_anecdotes"))
        await OutOfAnecdotesHistory.insert(chat_id=chat_id)
