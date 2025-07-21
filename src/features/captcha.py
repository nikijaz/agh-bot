import random
from typing import Final

from aiogram.types import (
    CallbackQuery,
    ChatMemberUpdated,
    ChatPermissions,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from i18n import t

from src import BOT
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
            "captcha.initial_message",
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
        await BOT.delete_message(chat_member.chat.id, captcha.message_id)
        await captcha.delete()


async def process_captcha_response(callback_query: CallbackQuery) -> None:
    button_id = callback_query.data.split(":")[1]

    captcha = await PendingCaptcha.get_or_none(
        PendingCaptcha.chat_id == callback_query.message.chat.id,
        PendingCaptcha.user_id == callback_query.from_user.id,
    )
    if captcha is None:
        await callback_query.answer(t("captcha.not_found_error"))
        return

    if captcha.button_id == button_id:
        await BOT.restrict_chat_member(
            callback_query.message.chat.id,
            callback_query.from_user.id,
            ChatPermissions(can_send_messages=True),
        )
    else:
        await BOT.ban_chat_member(callback_query.message.chat.id, callback_query.from_user.id)
        await BOT.unban_chat_member(callback_query.message.chat.id, callback_query.from_user.id)

    await callback_query.message.delete()
    await captcha.delete()
    await callback_query.answer(t("captcha.solved_message"))
