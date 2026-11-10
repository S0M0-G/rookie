from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from core.config import BOT_OWNER_ID
from database import get_owner, delete_owner


async def stop_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    if not chat or chat.type != "private":
        return

    if not user:
        return

    if BOT_OWNER_ID is not None and user.id == BOT_OWNER_ID:
        await message.reply_text(
            "L'administrateur principal ne peut pas utiliser /stop."
        )
        return

    owner = get_owner(user.id)

    if not owner:
        await message.reply_text(
            "Tu n'es pas enregistré comme responsable."
        )
        return

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "Confirmer la suppression",
                callback_data=f"stop:confirm:{user.id}",
            ),
            InlineKeyboardButton(
                "Annuler",
                callback_data=f"stop:cancel:{user.id}",
            ),
        ]
    ])

    await message.reply_text(
        "ATTENTION : suppression définitive\n\n"
        "Cette opération supprimera :\n"
        "• Ton compte de responsable\n"
        "• Tous tes groupes et canaux du système de gestion\n"
        "• Les utilisateurs suivis et leurs avertissements\n"
        "• Les historiques et paramètres associés\n\n"
        "Les groupes et canaux Telegram eux-mêmes ne seront pas supprimés.\n\n"
        "Cette opération est irréversible. Confirmer ?",
        reply_markup=keyboard,
    )


async def stop_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    chat = update.effective_chat
    user = update.effective_user

    if not chat or chat.type != "private" or not user:
        await query.answer("Action autorisée uniquement en privé.", show_alert=True)
        return

    parts = (query.data or "").split(":")

    if len(parts) != 3 or parts[0] != "stop":
        await query.answer("Demande invalide.", show_alert=True)
        return

    action = parts[1]

    try:
        owner_id = int(parts[2])
    except ValueError:
        await query.answer("Identifiant invalide.", show_alert=True)
        return

    if owner_id != user.id:
        await query.answer("Tu ne peux pas effectuer cette action.", show_alert=True)
        return

    if BOT_OWNER_ID is not None and user.id == BOT_OWNER_ID:
        await query.answer("Action interdite pour l'administrateur principal.", show_alert=True)
        return

    await query.answer()

    if action == "cancel":
        await query.edit_message_text(
            "Suppression annulée. Ton compte et tes ressources sont conservés."
        )
        return

    if action != "confirm":
        await query.edit_message_text("Action inconnue.")
        return

    if not get_owner(owner_id):
        await query.edit_message_text(
            "Aucun compte responsable correspondant n'a été trouvé."
        )
        return

    deleted = delete_owner(owner_id)

    if deleted:
        await query.edit_message_text(
            "Ton compte de responsable et toutes les données associées "
            "ont été supprimés.\n\n"
            "Les groupes et canaux Telegram existent toujours, "
            "mais ne sont plus gérés par ce bot."
        )
    else:
        await query.edit_message_text(
            "La suppression n'a pas pu être effectuée."
        )


def register_stop_handlers(app):
    app.add_handler(CommandHandler("stop", stop_command))
    app.add_handler(
        CallbackQueryHandler(
            stop_callback,
            pattern=r"^stop:",
        )
    )
