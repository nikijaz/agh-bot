import asyncio
import random
from datetime import datetime, timedelta
from typing import Final, cast

from aiogram.exceptions import AiogramError
from aiogram.types import (
    CallbackQuery,
    ChatMemberUpdated,
    ChatPermissions,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from i18n import t

from src import BOT, config
from src.models import PendingCaptcha

CAPTCHA_BUTTONS: Final = {
    "red": InlineKeyboardButton(text="🟥", callback_data="captcha:red"),
    "yellow": InlineKeyboardButton(text="🟨", callback_data="captcha:yellow"),
    "green": InlineKeyboardButton(text="🟩", callback_data="captcha:green"),
    "blue": InlineKeyboardButton(text="🟦", callback_data="captcha:blue"),
}


async def send_captcha(chat_member: ChatMemberUpdated) -> None:
    await BOT.restrict_chat_member(
        chat_member.chat.id,
        chat_member.new_chat_member.user.id,
        ChatPermissions(can_send_messages=False),
    )

    button_ids = list(CAPTCHA_BUTTONS.keys())
    random.shuffle(button_ids)
    button_id = random.choice(button_ids)
    shuffled_buttons = [CAPTCHA_BUTTONS[id] for id in button_ids]
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


async def _monitor_captcha_timeout() -> None:
    while True:
        current_datetime = datetime.now()

        timeout_threshold = current_datetime - timedelta(seconds=config.CAPTCHA_TIMEOUT_SECONDS)
        pending_captchas = await PendingCaptcha.select().where(
            PendingCaptcha.inserted_at < timeout_threshold,
        )

        for captcha in pending_captchas:
            try:
                await BOT.ban_chat_member(captcha.chat_id, captcha.user_id)
                await BOT.unban_chat_member(captcha.chat_id, captcha.user_id)
            except AiogramError:
                pass  # Ignore if user cannot be banned/unbanned

            try:
                await BOT.delete_message(captcha.chat_id, captcha.message_id)
            except AiogramError:
                pass  # Ignore if message does not exist or cannot be deleted
            await captcha.delete()

        closest_pending_captcha = await PendingCaptcha.select().order_by(PendingCaptcha.inserted_at).first()
        if closest_pending_captcha is None:
            await asyncio.sleep(config.CAPTCHA_TIMEOUT_SECONDS)
        else:
            sleep_till = cast(datetime, closest_pending_captcha.inserted_at) + timedelta(
                seconds=config.CAPTCHA_TIMEOUT_SECONDS
            )
            await asyncio.sleep(
                min(5, (sleep_till - current_datetime).total_seconds())  # Avoid busy-waiting
            )


if not asyncio.get_event_loop().is_running():
    raise RuntimeError("This feature should only be imported when the event loop is running.")
asyncio.create_task(_monitor_captcha_timeout())  # Start monitoring captcha timeouts upon import


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


async def process_captcha_response(callback_query: CallbackQuery) -> None:
    if callback_query.data is None:
        raise ValueError("Callback data must be provided")
    if not callback_query.data.startswith("captcha:"):
        raise ValueError("Callback data must follow 'captcha:*' format")
    if not isinstance(callback_query.message, Message):
        raise ValueError("Callback must be associated with a deletable message")

    button_id = callback_query.data.split(":")[1]

    captcha = await PendingCaptcha.get_or_none(
        PendingCaptcha.chat_id == callback_query.message.chat.id,
        PendingCaptcha.user_id == callback_query.from_user.id,
    )
    if captcha is None:
        await callback_query.answer(t("captcha.message.not_found"))
        return

    if captcha.button_id == button_id:
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
