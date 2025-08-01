from datetime import datetime, timezone
from typing import Final

from peewee_aio import AIOModel, Manager
from peewee_aio.fields import (
    BigIntegerField,
    CharField,
    DateTimeField,
    IdentityField,
)

from src import config

DB: Final = Manager(
    f"postgresql://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}@{config.POSTGRES_HOST}/{config.POSTGRES_DB}",
)


class DateTimeTZField(DateTimeField[datetime]):
    field_type = "TIMESTAMPTZ"


@DB.register
class ChatState(AIOModel):
    chat_id = BigIntegerField(primary_key=True)
    last_activity = DateTimeTZField()

    class Meta:
        table_name = "chat_states"


@DB.register
class AnecdoteHistory(AIOModel):
    anecdote_hash = CharField(max_length=32, primary_key=True)
    chat_id = BigIntegerField()
    inserted_at = DateTimeTZField(default=lambda: datetime.now(timezone.utc))

    class Meta:
        table_name = "anecdote_history"


@DB.register
class OutOfAnecdotesHistory(AIOModel):
    chat_id = BigIntegerField()
    inserted_at = DateTimeTZField(default=lambda: datetime.now(timezone.utc))

    class Meta:
        table_name = "out_of_anecdotes_history"


@DB.register
class PendingCaptcha(AIOModel):
    id = IdentityField()
    chat_id = BigIntegerField()
    user_id = BigIntegerField()
    message_id = BigIntegerField()
    button_id = CharField(max_length=32)
    inserted_at = DateTimeTZField(default=lambda: datetime.now(timezone.utc))

    class Meta:
        table_name = "pending_captchas"
