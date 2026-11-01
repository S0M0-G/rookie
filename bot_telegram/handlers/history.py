from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import (
    get_user,
    get_warning_history_page,
    count_warning_history,
    delete_warning_history,
)

from handlers.common import is_admin


async def history_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ouvre l'historique d'un utilisateur sur la première page."""

    query = update.callback_query
    await query.answer()

    if not await is_admin(update):
        await query.answer(
            "❌ Réservé aux administrateurs.",
            show_alert=True
        )
        return

    parts = query.data.split(":")
    user_id = int(parts[1])

    await history_page_button(
        update,
        context,
        user_id,
        1
    )


async def history_page_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_id=None,
    page=None
):
    """Affiche une page de l'historique des avertissements."""

    query = update.callback_query
    await query.answer()

    if not await is_admin(update):
        await query.answer(
            "❌ Réservé aux administrateurs.",
            show_alert=True
        )
        return

    chat_id = update.effective_chat.id

    if user_id is None or page is None:
        parts = query.data.split(":")
        user_id = int(parts[1])
        page = int(parts[2])

    user = get_user(chat_id, user_id)

    if not user:
        await query.edit_message_text(
            "❌ Utilisateur introuvable."
        )
        return

    per_page = 10

    history = get_warning_history_page(
        chat_id,
        user_id,
        page,
        per_page
    )

    total = count_warning_history(
        chat_id,
        user_id
    )

    if total == 0:
        text = (
            "📋 HISTORIQUE DES AVERTISSEMENTS\n\n"
            f"👤 {user[2] or 'Utilisateur'}\n"
            f"🆔 ID : {user_id}\n\n"
            "Aucun avertissement enregistré."
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "⬅️ Retour à la fiche",
                    callback_data=f"user:{user_id}"
                )
            ]
        ]

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    total_pages = (
        total + per_page - 1
    ) // per_page

    if page > total_pages:
        page = total_pages

        history = get_warning_history_page(
            chat_id,
            user_id,
            page,
            per_page
        )

    text = (
        "📋 HISTORIQUE DES AVERTISSEMENTS\n\n"
        f"👤 {user[2] or 'Utilisateur'}\n"
        f"🆔 ID : {user_id}\n"
        f"📄 Page {page}/{total_pages}\n\n"
    )

    keyboard = []

    start_number = (
        (page - 1) * per_page + 1
    )

    for number, record in enumerate(
        history,
        start=start_number
    ):
        history_id, reason, admin_id, created_at = record

        text += (
            f"⚠️ Avertissement #{number}\n"
            f"📌 Raison : {reason or 'Aucune raison'}\n"
            f"👮 Admin : {admin_id or 'Inconnu'}\n"
            f"🕐 Date : {created_at}\n\n"
        )

        keyboard.append([
            InlineKeyboardButton(
                f"🗑️ Supprimer l'avertissement #{number}",
                callback_data=(
                    f"delete_history:"
                    f"{history_id}:"
                    f"{user_id}:"
                    f"{page}"
                )
            )
        ])

    navigation = []

    if page > 1:
        navigation.append(
            InlineKeyboardButton(
                "⬅️ Précédent",
                callback_data=f"history_page:{user_id}:{page - 1}"
            )
        )

    if page < total_pages:
        navigation.append(
            InlineKeyboardButton(
                "➡️ Suivant",
                callback_data=f"history_page:{user_id}:{page + 1}"
            )
        )

    if navigation:
        keyboard.append(navigation)

    keyboard.append([
        InlineKeyboardButton(
            "⬅️ Retour à la fiche",
            callback_data=f"user:{user_id}"
        )
    ])

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def delete_history_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Demande confirmation avant de supprimer un avertissement."""

    query = update.callback_query
    await query.answer()

    if not await is_admin(update):
        await query.answer(
            "❌ Réservé aux administrateurs.",
            show_alert=True
        )
        return

    parts = query.data.split(":")

    history_id = int(parts[1])
    user_id = int(parts[2])
    page = int(parts[3])

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Confirmer",
                callback_data=(
                    f"confirm_delete_history:"
                    f"{history_id}:{user_id}:{page}"
                )
            ),
            InlineKeyboardButton(
                "❌ Annuler",
                callback_data=f"history_page:{user_id}:{page}"
            )
        ]
    ]

    await query.edit_message_text(
        "⚠️ Veux-tu vraiment supprimer cet avertissement ?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def confirm_delete_history(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Supprime définitivement l'avertissement."""

    query = update.callback_query
    await query.answer()

    if not await is_admin(update):
        await query.answer(
            "❌ Réservé aux administrateurs.",
            show_alert=True
        )
        return

    parts = query.data.split(":")

    history_id = int(parts[1])
    user_id = int(parts[2])
    page = int(parts[3])

    chat_id = update.effective_chat.id

    delete_warning_history(
        chat_id,
        history_id
    )

    await history_page_button(
        update,
        context,
        user_id,
        page
    )


def register_history_handlers(app):
    from telegram.ext import CallbackQueryHandler

    app.add_handler(
        CallbackQueryHandler(
            history_button,
            pattern="^history:"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            history_page_button,
            pattern="^history_page:"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            delete_history_button,
            pattern="^delete_history:"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            confirm_delete_history,
            pattern="^confirm_delete_history:"
        )
    )
