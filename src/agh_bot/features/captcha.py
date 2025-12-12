import asyncio
import datetime
import logging
import random
from typing import NoReturn

from aiogram.exceptions import AiogramError
from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    CallbackQuery,
    Chat,
    ChatMemberUnion,
    ChatPermissions,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from i18n import t
from cachetools import TTLCache
from peewee import SQL

from agh_bot.loader import BOT
from agh_bot.config import CONFIG
from agh_bot.models import PendingCaptcha

GRANT_ALL_PERMISSIONS = ChatPermissions(**{field: True for field in ChatPermissions.model_fields})
REVOKE_ALL_PERMISSIONS = ChatPermissions(**{field: False for field in ChatPermissions.model_fields})


class CaptchaCallback(CallbackData, prefix="captcha"):
    button_id: str


CAPTCHA_COLORS = (
    ("red", "🟥"),
    ("yellow", "🟨"),
    ("green", "🟩"),
    ("blue", "🟦"),
)
CAPTCHA_BUTTONS = [
    (color_id, InlineKeyboardButton(text=emoji, callback_data=CaptchaCallback(button_id=color_id).pack()))
    for color_id, emoji in CAPTCHA_COLORS
]


async def monitor_captcha_timeout() -> NoReturn:
    while True:
        # Delete and get expired captchas
        result: list[PendingCaptcha] = (
            await PendingCaptcha.delete()
            .where(
                PendingCaptcha.inserted_at < SQL(f"NOW() - INTERVAL '{CONFIG.CAPTCHA_TIMEOUT_SECONDS} seconds'"),
            )
            .returning(PendingCaptcha)
        )

        # Kick users who didn't solve the captcha in time
        for captcha in result:
            try:
                await BOT.delete_message(captcha.chat_id, captcha.message_id)
                await BOT.ban_chat_member(captcha.chat_id, captcha.user_id)
                await BOT.unban_chat_member(captcha.chat_id, captcha.user_id)
            except AiogramError as e:
                logging.error(
                    f"Handling expired captcha for chat {captcha.chat_id}, user {captcha.user_id} failed: {e}"
                )

        # Avoid busy-waiting
        await asyncio.sleep(1)


async def send_captcha(chat: Chat, chat_member: ChatMemberUnion) -> None:
    # Revoke all permissions initially
    await BOT.restrict_chat_member(
        chat.id,
        chat_member.user.id,
        REVOKE_ALL_PERMISSIONS,
    )

    # Prepare captcha markup
    shuffled_buttons = random.sample(CAPTCHA_BUTTONS, len(CAPTCHA_BUTTONS))
    target_button_id, _ = random.choice(shuffled_buttons[1:])  # Ensure the first button is not selected
    captcha_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [button for _, button in shuffled_buttons[:2]],
            [button for _, button in shuffled_buttons[2:]],
        ]
    )

    # Send captcha message
    message = await BOT.send_message(
        chat.id,
        t(
            "captcha.message.captcha",
            user=chat_member.user.mention_markdown(),
            button=t(f"captcha.button.{target_button_id}"),
        ),
        reply_markup=captcha_markup,
    )

    # Record pending captcha
    await PendingCaptcha.insert(
        chat_id=chat.id,
        user_id=chat_member.user.id,
        message_id=message.message_id,
        button_id=target_button_id,
    )


async def check_has_captcha(chat: Chat, chat_member: ChatMemberUnion) -> bool:
    return (
        await PendingCaptcha.select()
        .where(
            PendingCaptcha.chat_id == chat.id,
            PendingCaptcha.user_id == chat_member.user.id,
        )
        .exists()
    )


meddling_attempt_count: TTLCache[str, int] = TTLCache(maxsize=1024, ttl=CONFIG.MEDDLING_MUTE_SECONDS)


async def process_captcha_response(callback_query: CallbackQuery, callback_data: CaptchaCallback) -> None:
    if not isinstance(callback_query.message, Message):
        raise ValueError("Callback must be associated with a deletable message")

    # Delete and get pending captcha
    result: list[PendingCaptcha] = (
        await PendingCaptcha.delete()
        .where(
            PendingCaptcha.chat_id == callback_query.message.chat.id,
            PendingCaptcha.user_id == callback_query.from_user.id,
        )
        .returning(PendingCaptcha)
    )
    captcha = result[0] if result else None

    # User is meddling with someone else's captcha
    if captcha is None:
        key = f"{callback_query.from_user.id}:{callback_query.message.chat.id}:{callback_query.message.message_id}"
        if key not in meddling_attempt_count:
            meddling_attempt_count[key] = 0
        meddling_attempt = meddling_attempt_count[key] + 1
        meddling_attempt_count[key] = meddling_attempt

        # If there are no more replies configured, mute the user
        try:
            await callback_query.answer(t(f"captcha.message.meddling_reply_{meddling_attempt}"))
        except KeyError:
            await callback_query.answer(t("captcha.message.meddling_reply_final"))
            await BOT.restrict_chat_member(
                callback_query.message.chat.id,
                callback_query.from_user.id,
                REVOKE_ALL_PERMISSIONS,
                until_date=datetime.datetime.now() + datetime.timedelta(seconds=CONFIG.MEDDLING_MUTE_SECONDS),
            )
        return

    # Either solve or kick the user
    if captcha.button_id == callback_data.button_id:
        await BOT.restrict_chat_member(
            callback_query.message.chat.id,
            callback_query.from_user.id,
            GRANT_ALL_PERMISSIONS,
        )
        await callback_query.answer(t("captcha.message.solved"))
    else:
        await BOT.ban_chat_member(callback_query.message.chat.id, callback_query.from_user.id)
        await BOT.unban_chat_member(callback_query.message.chat.id, callback_query.from_user.id)

    # Delete captcha message
    await callback_query.message.delete()


async def dismiss_pending_captcha(chat: Chat, chat_member: ChatMemberUnion) -> None:
    # Delete and get pending captcha
    result: list[PendingCaptcha] = (
        await PendingCaptcha.delete()
        .where(
            PendingCaptcha.chat_id == chat.id,
            PendingCaptcha.user_id == chat_member.user.id,
        )
        .returning(PendingCaptcha)
    )
    captcha = result[0] if result else None

    # No pending captcha
    if captcha is None:
        return

    # Dismiss captcha
    await BOT.delete_message(chat.id, captcha.message_id)
    await BOT.restrict_chat_member(
        captcha.chat_id,
        captcha.user_id,
        GRANT_ALL_PERMISSIONS,
    )
