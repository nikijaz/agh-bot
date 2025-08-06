import asyncio
import random
from typing import Final

from aiogram.exceptions import AiogramError
from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    CallbackQuery,
    ChatMemberUpdated,
    ChatPermissions,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from i18n import t
from peewee import SQL

from src import BOT, config
from src.models import PendingCaptcha


class CaptchaCallback(CallbackData, prefix="captcha"):
    button_id: str


CAPTCHA_BUTTONS: Final = {
    "red": InlineKeyboardButton(text="🟥", callback_data=CaptchaCallback(button_id="red").pack()),
    "yellow": InlineKeyboardButton(text="🟨", callback_data=CaptchaCallback(button_id="yellow").pack()),
    "green": InlineKeyboardButton(text="🟩", callback_data=CaptchaCallback(button_id="green").pack()),
    "blue": InlineKeyboardButton(text="🟦", callback_data=CaptchaCallback(button_id="blue").pack()),
}


def setup() -> None:
    asyncio.create_task(_monitor_captcha_timeout())


async def _monitor_captcha_timeout() -> None:
    while True:
        expired_captchas = await PendingCaptcha.select().where(
            PendingCaptcha.inserted_at < SQL(f"NOW() - INTERVAL '{config.CAPTCHA_TIMEOUT_SECONDS} seconds'")
        )  # fmt: skip

        for captcha in expired_captchas:
            try:
                await BOT.ban_chat_member(captcha.chat_id, captcha.user_id)
                await BOT.unban_chat_member(captcha.chat_id, captcha.user_id)

                await BOT.delete_message(captcha.chat_id, captcha.message_id)
            except AiogramError:
                pass  # Ignore if user cannot be kicked or message does not exist
            await captcha.delete()

        await asyncio.sleep(1)  # Avoid busy-waiting


async def send_captcha(chat_member: ChatMemberUpdated) -> None:
    await BOT.restrict_chat_member(
        chat_member.chat.id,
        chat_member.new_chat_member.user.id,
        ChatPermissions(can_send_messages=False),
    )

    button_id = random.choice(list(CAPTCHA_BUTTONS.keys())[1:])  # Ensure the first button is not selected
    shuffled_buttons = random.sample(list(CAPTCHA_BUTTONS.values()), len(CAPTCHA_BUTTONS))
    captcha_markup = InlineKeyboardMarkup(inline_keyboard=[shuffled_buttons[:2], shuffled_buttons[2:]])

    message = await BOT.send_message(
        chat_member.chat.id,
        t(
            "captcha.message.captcha",
            user=f"@{chat_member.new_chat_member.user.username}",
            button=t(f"captcha.button.{button_id}"),
        ),
        reply_markup=captcha_markup,
    )

    await PendingCaptcha.insert(
        chat_id=chat_member.chat.id,
        user_id=chat_member.new_chat_member.user.id,
        message_id=message.message_id,
        button_id=button_id,
    )


async def dismiss_pending_captcha(chat_member: ChatMemberUpdated) -> None:
    captcha = await PendingCaptcha.get_or_none(
        PendingCaptcha.chat_id == chat_member.chat.id,
        PendingCaptcha.user_id == chat_member.new_chat_member.user.id,
    )
    if captcha is not None:
        try:
            await BOT.delete_message(chat_member.chat.id, captcha.message_id)
        except AiogramError:
            pass  # Ignore if message does not exist
        await captcha.delete()


async def process_captcha_response(callback_query: CallbackQuery, callback_data: CaptchaCallback) -> None:
    if not isinstance(callback_query.message, Message):
        raise ValueError("Callback must be associated with a deletable message")

    captcha = await PendingCaptcha.get_or_none(
        PendingCaptcha.chat_id == callback_query.message.chat.id,
        PendingCaptcha.user_id == callback_query.from_user.id,
    )
    if captcha is None:
        await callback_query.answer(t("captcha.message.not_found"))
        return

    if captcha.button_id == callback_data.button_id:
        await BOT.restrict_chat_member(
            callback_query.message.chat.id,
            callback_query.from_user.id,
            ChatPermissions(can_send_messages=True),
        )
        await callback_query.answer(t("captcha.message.solved"))
    else:
        await BOT.ban_chat_member(callback_query.message.chat.id, callback_query.from_user.id)
        await BOT.unban_chat_member(callback_query.message.chat.id, callback_query.from_user.id)

    await callback_query.message.delete()
    await captcha.delete()
