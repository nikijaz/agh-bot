from typing import Any, Callable

from aiogram.dispatcher.event.handler import CallbackType
from aiogram.dispatcher.event.telegram import TelegramEventObserver
from aiogram.enums import ChatMemberStatus, ChatType, ContentType
from aiogram.filters import IS_MEMBER, IS_NOT_MEMBER, ChatMemberUpdatedFilter
from aiogram.types import CallbackQuery, ChatMemberUpdated, Message
from i18n import t

from src import BOT, DP
from src.features import anecdote, captcha
from src.features.captcha import CaptchaCallback

HANDLER_REGISTRARS: list[Callable[[], Any]] = []


def setup() -> None:
    for handler_registrar in HANDLER_REGISTRARS:
        handler_registrar()


def handler(event: TelegramEventObserver, *filters: CallbackType) -> Callable[[CallbackType], CallbackType]:
    """
    Postpone registration of a handler until the setup function is called.
    This ensures that all handlers are registered in a controlled manner.
    """

    def wrapper(callback: CallbackType) -> CallbackType:
        HANDLER_REGISTRARS.append(lambda: event.register(callback, *filters))
        return callback

    return wrapper


@handler(DP.message)
async def message_handler(message: Message) -> None:
    if message.content_type in {ContentType.NEW_CHAT_MEMBERS, ContentType.LEFT_CHAT_MEMBER}:
        await message.delete()  # Delete telegram's join/leave messages, we handle them ourselves

    if message.chat.type != ChatType.PRIVATE and message.from_user and not message.from_user.is_bot:
        await anecdote.record_message_activity(message)


@handler(DP.chat_member, ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def chat_member_join_handler(chat_member: ChatMemberUpdated) -> None:
    await captcha.send_captcha(chat_member)


@handler(DP.callback_query, CaptchaCallback.filter())
async def captcha_data_handler(callback_query: CallbackQuery, callback_data: CaptchaCallback) -> None:
    await captcha.process_captcha_response(callback_query, callback_data)


@handler(DP.chat_member, ChatMemberUpdatedFilter(IS_MEMBER >> IS_NOT_MEMBER))
async def chat_member_left_handler(chat_member: ChatMemberUpdated) -> None:
    await captcha.dismiss_pending_captcha(chat_member)
    if chat_member.new_chat_member.status != ChatMemberStatus.KICKED:
        await BOT.send_message(
            chat_member.chat.id,
            t(
                "goodbye.message.goodbye",
                user=f"@{chat_member.old_chat_member.user.username}"
                if chat_member.old_chat_member.user.username
                else f"[{chat_member.old_chat_member.user.full_name}](tg://user?id={chat_member.old_chat_member.user.id})",
            ),
        )
