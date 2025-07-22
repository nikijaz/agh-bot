from aiogram import F
from aiogram.enums import ChatType
from aiogram.filters import IS_MEMBER, IS_NOT_MEMBER, KICKED, ChatMemberUpdatedFilter
from aiogram.types import CallbackQuery, ChatMemberUpdated, Message
from i18n import t

from src import BOT, DP
from src.features import anecdote, captcha


@DP.message(~F.from_user.is_bot & F.chat.type != ChatType.PRIVATE)
async def message_handler(message: Message) -> None:
    await anecdote.record_message_activity(message)


@DP.chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def chat_member_join_handler(chat_member: ChatMemberUpdated) -> None:
    await captcha.send_captcha(chat_member)


@DP.callback_query(F.data.startswith("captcha:"))
async def captcha_data_handler(callback_query: CallbackQuery) -> None:
    await captcha.process_captcha_response(callback_query)


@DP.chat_member(ChatMemberUpdatedFilter(IS_MEMBER >> IS_NOT_MEMBER))
async def chat_member_left_handler(chat_member: ChatMemberUpdated) -> None:
    await captcha.dismiss_pending_captcha(chat_member)
    if chat_member.new_chat_member.status != KICKED:
        await BOT.send_message(
            chat_member.chat.id, t("goodbye.message.goodbye", user=f"@{chat_member.old_chat_member.user.username}")
        )
