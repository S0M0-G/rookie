from telegram import Update
from telegram.ext import (
    ApplicationHandlerStop,
    ContextTypes,
    TypeHandler,
)

from database import get_resource_owner, get_owner, get_owner_restrictions


COMMAND_FEATURES = {
    "ban": "moderation",
    "unban": "moderation",
    "mute": "moderation",
    "unmute": "moderation",
    "kick": "moderation",
    "clean": "moderation",

    "warning": "warnings",
    "unwarning": "warnings",

    "allowdomain": "automod",
    "removedomain": "automod",
    "listdomains": "automod",

    "users": "users",
    "user": "users",

    "history": "history",

    "permissions": "permissions",

    "stats": "administration",
    "admins": "administration",
    "promote": "administration",
    "demote": "administration",
}


CALLBACK_FEATURES = {
    "ban": "moderation",
    "cancel_ban": "moderation",
    "confirm_ban": "moderation",
    "unban": "moderation",
    "cancel_unban": "moderation",
    "confirm_unban": "moderation",

    "warning": "warnings",
    "cancel_warning": "warnings",
    "confirm_warning": "warnings",
    "reset_warning": "warnings",
    "cancel_reset_warning": "warnings",
    "confirm_reset_warning": "warnings",

    "user": "users",
    "users": "users",

    "history": "history",
    "history_page": "history",
    "delete_history": "history",
    "confirm_delete_history": "history",

    "perm": "permissions",
}


def get_update_feature(update):
    """Détermine la fonctionnalité concernée par une mise à jour."""

    callback = update.callback_query

    if callback:
        data = callback.data or ""
        prefix = data.split(":", 1)[0]
        return CALLBACK_FEATURES.get(prefix)

    # Publications dans les chaînes.
    if update.channel_post or update.edited_channel_post:
        return "publishing"

    message = update.effective_message

    if not message:
        return None

    if message.new_chat_members:
        return "welcome"

    if message.text or message.caption:
        content = message.text or message.caption
        first_word = content.split()[0] if content.split() else ""

        if first_word.startswith("/"):
            command = first_word.split("@", 1)[0][1:].lower()
            return COMMAND_FEATURES.get(command)

        return "automod"

    return None

async def enforce_owner_access(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Applique les blocages et restrictions avant les autres handlers."""

    # Ne jamais bloquer les événements de présence du bot.
    if update.my_chat_member or update.chat_member:
        return

    chat = update.effective_chat

    # Les conversations privées restent accessibles.
    if not chat or chat.type == "private":
        return

    feature = get_update_feature(update)

    owner_id = get_resource_owner(chat.id)

    # Ressource non enregistrée : bloquer les fonctionnalités gérées.
    if owner_id is None:
        if feature:
            await notify_access_denied(update)
            raise ApplicationHandlerStop
        return

    owner = get_owner(owner_id)

    if not owner:
        await notify_access_denied(update)
        raise ApplicationHandlerStop

    # Un propriétaire bloqué perd toutes les fonctionnalités
    # dans chacune de ses ressources.
    if owner[3] == "blocked":
        await notify_access_denied(update)
        raise ApplicationHandlerStop

    # Une mise à jour sans fonctionnalité identifiée continue.
    if not feature:
        return

    restrictions = get_owner_restrictions(owner_id)

    restricted_features = {
        row[0]
        for row in restrictions
        if row[1]
    }

    if "all" in restricted_features or feature in restricted_features:
        await notify_access_denied(update)
        raise ApplicationHandlerStop


async def notify_access_denied(update):
    """Informe l'utilisateur lorsqu'une commande ou un bouton est bloqué."""

    if update.callback_query:
        await update.callback_query.answer(
            "Cette fonctionnalité est actuellement indisponible.",
            show_alert=True
        )
        return

    message = update.effective_message

    if message and message.text and message.text.startswith("/"):
        await message.reply_text(
            "Cette fonctionnalité est actuellement indisponible."
        )


def register_access_handlers(app):
    app.add_handler(
        TypeHandler(Update, enforce_owner_access),
        group=-1
    )
