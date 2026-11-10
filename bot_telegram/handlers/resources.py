from telegram import Update
from telegram.ext import (
    ContextTypes,
    ChatMemberHandler
)

from database import (
    register_resource,
    get_resource_owner,
    set_resource_status
)


ACTIVE_STATUSES = ("member", "administrator")


async def track_bot_membership(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    event = update.my_chat_member

    if not event:
        return

    chat = event.chat
    new_status = event.new_chat_member.status

    if new_status in ACTIVE_STATUSES:

        owner_id = get_resource_owner(chat.id)

        if owner_id is None:
            actor = event.from_user

            register_resource(
                owner_id=actor.id,
                owner_username=actor.username,
                owner_first_name=actor.first_name,
                chat_id=chat.id,
                chat_type=chat.type,
                title=chat.title,
                username=chat.username
            )

        else:
            set_resource_status(chat.id, "active")

    elif new_status in ("left", "kicked"):

        set_resource_status(chat.id, "inactive")


def register_resource_handlers(app):
    app.add_handler(
        ChatMemberHandler(
            track_bot_membership,
            ChatMemberHandler.MY_CHAT_MEMBER
        )
    )
