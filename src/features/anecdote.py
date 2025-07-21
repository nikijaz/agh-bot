import asyncio
import hashlib
import random
import time
from datetime import datetime, timedelta

from aiogram.types import Message
from croniter import croniter
from i18n import t

from src import BOT
from src.config import ACTIVITY_HANDLER_SCHEDULE, ACTIVITY_TIMEOUT_SECONDS
from src.models import AnecdoteHistory, ChatState


async def record_message_activity(message: Message) -> None:
    await ChatState.insert(
        chat_id=message.chat.id,
        last_activity=message.date,
    ).on_conflict(
        conflict_target=[ChatState.chat_id],
        update={ChatState.last_activity: message.date},
    )


async def monitor_chat_activity() -> None:
    while True:
        timeout_threshold = datetime.now() - timedelta(seconds=ACTIVITY_TIMEOUT_SECONDS)
        chat_states = await ChatState.select().where(
            ChatState.last_activity < timeout_threshold.timestamp(),
            ChatState.is_handled == False,
        )

        for chat_state in chat_states:
            await handle_inactivity(chat_state.chat_id)
            chat_state.is_handled = True
            await chat_state.save()

        sleep_till = croniter(ACTIVITY_HANDLER_SCHEDULE, datetime.now(), second_at_beginning=True).get_next()
        await asyncio.sleep(sleep_till - time.time())


if not asyncio.get_event_loop().is_running():
    raise RuntimeError("This feature should only be imported when the event loop is running.")
asyncio.create_task(monitor_chat_activity())  # Start monitoring chat activity upon import


async def handle_inactivity(chat_id: int) -> None:
    def gen_hash(anecdote: str) -> str:
        return hashlib.sha1(anecdote.encode()).hexdigest()[:32]

    with open("anecdotes.txt", "r") as file:
        anecdote = file.readlines()
    anecdote = [a for a in anecdote if a.strip()]

    used_hashes = set(
        a.anecdote_hash
        for a in await AnecdoteHistory.select().where(
            AnecdoteHistory.chat_id == chat_id,
        )
    )

    unused_anecdotes = [a for a in anecdote if gen_hash(a) not in used_hashes]
    if not unused_anecdotes:
        await BOT.send_message(chat_id, t("anecdote.no_anecdote"))
        return

    anecdote = random.choice(unused_anecdotes)
    await BOT.send_message(chat_id, anecdote)
    await AnecdoteHistory.insert(
        anecdote_hash=gen_hash(anecdote),
        chat_id=chat_id,
    )
