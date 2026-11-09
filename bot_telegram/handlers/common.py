
from telegram import Update, InlineKeyboardButton


def build_user_keyboard(user_id, banned):
    """Construit les boutons d'une fiche utilisateur."""
    moderation_button = (
        InlineKeyboardButton(
            "🔓 Débannir",
            callback_data=f"confirm_unban:{user_id}"
        )
        if banned
        else InlineKeyboardButton(
            "🔨 Bannir",
            callback_data=f"confirm_ban:{user_id}"
        )
    )

    return [
        [moderation_button],
        [
            InlineKeyboardButton(
                "⚠️ Avertir",
                callback_data=f"confirm_warning:{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "🔄 Réinitialiser",
                callback_data=f"confirm_reset_warning:{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "📋 Historique",
                callback_data=f"history:{user_id}"
            )
        ]
    ]


def user_card_text(user):
    """Construit le texte d'une fiche utilisateur."""
    user_id, username, first_name, last_name, banned, warnings = user

    return (
        f"👤 {first_name or 'Sans prénom'}\n\n"
        f"ID : {user_id}\n"
        f"Username : @{username if username else 'aucun'}\n"
        f"Prénom : {first_name or 'aucun'}\n"
        f"Nom : {last_name or 'aucun'}\n"
        f"Statut : {'🚫 Banni' if banned else '✅ Actif'}\n"
        f"Avertissements : {warnings}"
    )


async def is_admin(update: Update):
    """Vérifie si l'utilisateur qui déclenche l'action est administrateur."""
    member = await update.effective_chat.get_member(
        update.effective_user.id
    )
    return member.status in ("administrator", "creator")

async def is_user_admin(chat, user_id):
    """Vérifie si un utilisateur ciblé est administrateur."""
    member = await chat.get_member(user_id)
    return member.status in ("administrator", "creator")

def get_target_user(message):
    """Récupère l'utilisateur ciblé par une réponse classique ou externe."""

    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user

    if message.external_reply and message.external_reply.origin:
        return message.external_reply.origin.sender_user

    return None

