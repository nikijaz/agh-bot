from aiogram import F, Router
from aiogram.enums import ChatMemberStatus, ContentType
from aiogram.filters import IS_MEMBER, IS_NOT_MEMBER, ChatMemberUpdatedFilter
from aiogram.types import CallbackQuery, ChatMemberUpdated, Message
from i18n import t

from agh_bot.features import anecdotes
from agh_bot.features import captcha
from agh_bot.features.captcha import CaptchaCallback, check_has_captcha
from agh_bot.loader import BOT

ROUTER = Router()


@ROUTER.chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def on_chat_member_join(chat_member: ChatMemberUpdated) -> None:
    await captcha.send_captcha(chat_member.chat, chat_member.new_chat_member)


@ROUTER.callback_query(CaptchaCallback.filter())
async def on_captcha_data(callback_query: CallbackQuery, callback_data: CaptchaCallback) -> None:
    await captcha.process_captcha_response(callback_query, callback_data)


@ROUTER.chat_member(ChatMemberUpdatedFilter(IS_MEMBER >> IS_NOT_MEMBER))
async def on_chat_member_left(chat_member: ChatMemberUpdated) -> None:
    has_captcha = await check_has_captcha(chat_member.chat, chat_member.old_chat_member)
    if not has_captcha and chat_member.new_chat_member.status != ChatMemberStatus.KICKED:
        await BOT.send_message(
            chat_member.chat.id,
            t(
                "goodbye.message.goodbye",
                user=chat_member.old_chat_member.user.mention_markdown(),
            ),
        )

    await captcha.dismiss_pending_captcha(chat_member.chat, chat_member.old_chat_member)


@ROUTER.message(F.text == "ping")
async def on_ping_command(message: Message) -> None:
    await message.delete()


@ROUTER.message()
async def on_message(message: Message) -> None:
    if message.content_type in {ContentType.NEW_CHAT_MEMBERS, ContentType.LEFT_CHAT_MEMBER}:
        await message.delete()  # Delete telegram's join/leave messages, we handle them ourselves

    await anecdotes.record_activity(message)
