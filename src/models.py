from datetime import datetime
from typing import Final

from peewee_aio import AIOModel, Manager
from peewee_aio.fields import (
    BigIntegerField,
    BooleanField,
    CharField,
    IdentityField,
    TimestampField,
)

from src import config

DB: Final = Manager(config.POSTGRES_URL)


@DB.register
class ChatState(AIOModel):
    chat_id = BigIntegerField(primary_key=True)
    last_activity = TimestampField(utc=True)
    is_handled = BooleanField(default=False)

    class Meta:
        table_name = "chat_states"


@DB.register
class AnecdoteHistory(AIOModel):
    anecdote_hash = CharField(max_length=32, primary_key=True)
    chat_id = BigIntegerField()
    inserted_at = TimestampField(utc=True, default=datetime.now)

    class Meta:
        table_name = "anecdote_history"


@DB.register
class PendingCaptcha(AIOModel):
    id = IdentityField()
    chat_id = BigIntegerField()
    user_id = BigIntegerField()
    message_id = BigIntegerField()
    button_id = CharField(max_length=32)
    inserted_at = TimestampField(utc=True, default=datetime.now)

    class Meta:
        table_name = "pending_captchas"
