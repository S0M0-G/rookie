import os
from dotenv import load_dotenv

from database import (
    create_tables,
    save_user,
    get_user,
    get_user_by_username,
    get_all_users,
    get_users_page,
    count_users,
    set_banned,
    add_warning,
    reset_warnings,
    add_warning_history,
    get_warning_history,
    get_warning_history_page,
    count_warning_history,
    delete_warning_history,
    add_allowed_domain,
    remove_allowed_domain,
    get_allowed_domains,
    record_link_send
)

import re
import time
from urllib.parse import urlsplit
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")


# =========================
# OUTILS
# =========================

def build_user_keyboard(user_id, banned):
    """Construit les boutons d'une fiche utilisateur."""

    moderation_button = (
        InlineKeyboardButton(
            "🔓 Débannir",
            callback_data=f"confirm_unban:{user_id}"
        )
        if banned
        else
        InlineKeyboardButton(
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


# =========================
# COMMANDES DE BASE
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "Bot de gestion Telegram activé.\n\n"
        "Commandes disponibles :\n"
        "/start - Démarrer\n"
        "/help - Afficher l'aide\n"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "Commandes d'administration :\n\n"
        "/ban - Bannir un utilisateur\n"
        "/unban - Débannir un utilisateur\n"
        "/warning - Avertir un utilisateur\n"
        "/unwarning - Réinitialiser les avertissements\n"
        "/users - Voir la base de données sur les utilisateurs\n"
        "/user - Voir les infos d'un utilisateur\n"
        "/history - pour l'historique des warnings\n"
        "/mute - empeche l'envoi de message\n"
        "/unmute - retablie l'envoi de message\n"
        "/kick - expulser un utilisateur \n"
        "/clean - supprimer un message \n"
        "/stats - Afficher les statistiques du groupe\n"
        "/admins - liste et gestion des admins \n"
        "/promote - promouvoir en admin un utilisateur \n"
        "/demote - enlever les droits admins \n"
        "/permissions - voir et gerer les permissions d'un admin \n"
        "/allowdomain example.com - Autoriser un domaine (admin)\n"
        "/removedomain example.com - Retirer un domaine (admin)\n"
        "/listdomains - Afficher les domaines autorisés (admin)"
    )


# =========================
# NOUVEAUX MEMBRES
# =========================

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        save_user(update.effective_chat.id, member)

        await update.message.reply_text(
            f"Bienvenue {member.first_name} !"
        )


# =========================
# BAN / UNBAN PAR COMMANDE
# =========================

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message

    if not await is_admin(update):
        await message.reply_text(
            "❌ Tu dois être administrateur pour utiliser cette commande."
        )
        return

    # Accepte une réponse classique ou une réponse externe
    user = get_target_user(message)

    if not user:
        await message.reply_text(
            "❌ Réponds au message de l'utilisateur que tu veux bannir."
        )
        return

    save_user(update.effective_chat.id, user)

    try:
        await update.effective_chat.ban_member(user.id)
        set_banned(update.effective_chat.id, user.id, True)

        await message.reply_text(
            f"🚫 {user.first_name} a été banni."
        )

    except Exception as error:
        print("Erreur lors du bannissement :", error)

        await message.reply_text(
            "❌ Impossible de bannir cet utilisateur."
        )

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message

    if not await is_admin(update):
        await message.reply_text(
            "❌ Tu dois être administrateur pour utiliser cette commande."
        )
        return

    # Sans argument, on utilise l'utilisateur du message auquel on répond.
    if not context.args:
        target_user = get_target_user(message)

        if not target_user:
            await message.reply_text(
                "❌ Réponds au message de l'utilisateur que tu veux unban, "
                "ou utilise /unban ID ou /unban @username."
            )
            return

        save_user(update.effective_chat.id, target_user)
        user = get_user(update.effective_chat.id, target_user.id)

    else:
        target = context.args[0]

        # Recherche par username
        if target.startswith("@"):
            username = target[1:]
            user = get_user_by_username(update.effective_chat.id, username)

        # Recherche par ID
        else:
            try:
                user_id = int(target)
            except ValueError:
                await message.reply_text(
                    "❌ Utilise un ID ou un username valide."
                )
                return

            user = get_user(update.effective_chat.id, user_id)

    if not user:
        await message.reply_text(
            "❌ Cet utilisateur n'est pas dans la base."
        )
        return

    user_id = user[0]

    try:
        await update.effective_chat.unban_member(user_id)
        set_banned(update.effective_chat.id, user_id, False)

        user = get_user(update.effective_chat.id, user_id)

        await message.reply_text(
            user_card_text(user),
            reply_markup=InlineKeyboardMarkup(
                build_user_keyboard(user_id, False)
            )
        )

    except Exception as error:
        print("Erreur lors du unban :", error)

        await message.reply_text(
            "❌ Impossible de débannir cet utilisateur."
        )

# =========================
# LISTE DES UTILISATEURS
# =========================

async def users_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    if not chat or chat.type not in ("group", "supergroup"):
        await update.effective_message.reply_text(
            "❌ Cette commande doit être utilisée dans un groupe."
        )
        return

    await show_users_page(
        update.effective_message,
        chat.id,
        1
    )


async def users_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    await query.answer()

    chat = update.effective_chat
    page = int(query.data.split(":")[1])

    await edit_users_page(
        query,
        chat.id,
        page
    )


async def edit_users_page(query, chat_id, page):
    per_page = 10
    total = count_users(chat_id)
    total_pages = max(1, (total + per_page - 1) // per_page)

    if page < 1 or page > total_pages:
        return

    users = get_users_page(chat_id, page, per_page)

    text = f"👥 Utilisateurs — Page {page}/{total_pages}\n\n"

    for number, user in enumerate(
        users,
        start=(page - 1) * per_page + 1
    ):
        user_id, username, first_name, last_name, banned, warnings = user

        name = first_name or "Sans prénom"

        if last_name:
            name += f" {last_name}"

        if username:
            name += f" (@{username})"

        status = "🚫 Banni" if banned else "✅ Actif"

        text += (
            f"{number}. {name}\n"
            f"   ID : {user_id}\n"
            f"   Statut : {status}\n"
            f"   Avertissements : {warnings}\n\n"
        )

    user_buttons = []

    for user in users:
        user_id, username, first_name, last_name, banned, warnings = user

        name = first_name or "Sans prénom"

        if last_name:
            name += f" {last_name}"

        user_buttons.append([
            InlineKeyboardButton(
                f"👤 {name}",
                callback_data=f"user:{user_id}"
            )
        ])

    navigation = []

    if page > 1:
        navigation.append(
            InlineKeyboardButton(
                "⬅️",
                callback_data=f"users:{page - 1}"
            )
        )

    if page < total_pages:
        navigation.append(
            InlineKeyboardButton(
                "➡️",
                callback_data=f"users:{page + 1}"
            )
        )

    if navigation:
        user_buttons.append(navigation)

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(user_buttons)
    )


async def show_users_page(message, chat_id, page):
    per_page = 10
    total = count_users(chat_id)
    total_pages = max(1, (total + per_page - 1) // per_page)

    if page < 1:
        page = 1

    if page > total_pages:
        page = total_pages

    users = get_users_page(chat_id, page, per_page)

    text = f"👥 Utilisateurs — Page {page}/{total_pages}\n\n"

    for number, user in enumerate(
        users,
        start=(page - 1) * per_page + 1
    ):
        user_id, username, first_name, last_name, banned, warnings = user

        name = first_name or "Sans prénom"

        if last_name:
            name += f" {last_name}"

        if username:
            name += f" (@{username})"

        status = "🚫 Banni" if banned else "✅ Actif"

        text += (
            f"{number}. {name}\n"
            f"   ID : {user_id}\n"
            f"   Statut : {status}\n"
            f"   Avertissements : {warnings}\n\n"
        )

    user_buttons = []

    for user in users:
        user_id, username, first_name, last_name, banned, warnings = user

        name = first_name or "Sans prénom"

        if last_name:
            name += f" {last_name}"

        user_buttons.append([
            InlineKeyboardButton(
                f"👤 {name}",
                callback_data=f"user:{user_id}"
            )
        ])

    navigation = []

    if page > 1:
        navigation.append(
            InlineKeyboardButton(
                "⬅️",
                callback_data=f"users:{page - 1}"
            )
        )

    if page < total_pages:
        navigation.append(
            InlineKeyboardButton(
                "➡️",
                callback_data=f"users:{page + 1}"
            )
        )

    if navigation:
        user_buttons.append(navigation)

    await message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(user_buttons)
    )


# =========================
# FICHE UTILISATEUR
# =========================

async def user_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    await query.answer()

    user_id = int(query.data.split(":")[1])

    user = get_user(update.effective_chat.id, user_id)

    if not user:
        await query.edit_message_text(
            "❌ Utilisateur introuvable."
        )
        return

    _, username, first_name, last_name, banned, warnings = user

    keyboard = build_user_keyboard(user_id, banned)

    await query.edit_message_text(
        user_card_text(user),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message

    if not context.args:
        await message.reply_text(
            "❌ Utilisation : /user ID ou /user @username"
        )
        return

    target = context.args[0]

    if target.startswith("@"):
        username = target[1:]
        user = get_user_by_username(update.effective_chat.id, username)
    else:
        try:
            user_id = int(target)
        except ValueError:
            await message.reply_text(
                "❌ Utilise un ID ou un username valide."
            )
            return

        user = get_user(update.effective_chat.id, user_id)

    if not user:
        await message.reply_text(
            "❌ Cet utilisateur n'est pas dans la base."
        )
        return

    await message.reply_text(
        f"👤 Utilisateur trouvé\n\n"
        f"ID : {user[0]}\n"
        f"Username : @{user[1] if user[1] else 'aucun'}\n"
        f"Prénom : {user[2] or 'aucun'}\n"
        f"Nom : {user[3] or 'aucun'}\n"
        f"Banni : {'Oui' if user[4] else 'Non'}\n"
        f"Avertissements : {user[5]}"
    )


# =========================
# BOUTONS BAN
# =========================

async def confirm_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    await query.answer()

    user_id = int(query.data.split(":")[1])

    keyboard = [
        [
            InlineKeyboardButton(
                "🔨 Oui, bannir",
                callback_data=f"ban:{user_id}"
            ),
            InlineKeyboardButton(
                "❌ Annuler",
                callback_data=f"cancel_ban:{user_id}"
            )
        ]
    ]

    await query.edit_message_text(
        f"⚠️ Confirmer le bannissement de l'utilisateur {user_id} ?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def cancel_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    await query.answer()

    user_id = int(query.data.split(":")[1])

    user = get_user(update.effective_chat.id, user_id)

    if not user:
        await query.edit_message_text(
            "❌ Utilisateur introuvable."
        )
        return

    _, username, first_name, last_name, banned, warnings = user

    await query.edit_message_text(
        user_card_text(user),
        reply_markup=InlineKeyboardMarkup(
            build_user_keyboard(user_id, banned)
        )
    )


async def ban_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    await query.answer()

    if not await is_admin(update):
        await query.answer(
            "❌ Réservé aux administrateurs.",
            show_alert=True
        )
        return

    user_id = int(query.data.split(":")[1])

    try:
        await update.effective_chat.ban_member(user_id)
        set_banned(update.effective_chat.id, user_id, True)

        user = get_user(update.effective_chat.id, user_id)

        if not user:
            await query.edit_message_text(
                f"🚫 Utilisateur {user_id} banni."
            )
            return

        await query.edit_message_text(
            user_card_text(user),
            reply_markup=InlineKeyboardMarkup(
                build_user_keyboard(user_id, True)
            )
        )

    except Exception as error:
        print("Erreur lors du bannissement :", error)

        await query.edit_message_text(
            "❌ Impossible de bannir cet utilisateur."
        )


# =========================
# BOUTONS UNBAN
# =========================

async def confirm_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    await query.answer()

    user_id = int(query.data.split(":")[1])

    keyboard = [
        [
            InlineKeyboardButton(
                "🔓 Oui, débannir",
                callback_data=f"unban:{user_id}"
            ),
            InlineKeyboardButton(
                "❌ Annuler",
                callback_data=f"cancel_unban:{user_id}"
            )
        ]
    ]

    await query.edit_message_text(
        f"⚠️ Confirmer le débannissement de l'utilisateur {user_id} ?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def cancel_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    await query.answer()

    user_id = int(query.data.split(":")[1])

    user = get_user(update.effective_chat.id, user_id)

    if not user:
        await query.edit_message_text(
            "❌ Utilisateur introuvable."
        )
        return

    _, username, first_name, last_name, banned, warnings = user

    await query.edit_message_text(
        user_card_text(user),
        reply_markup=InlineKeyboardMarkup(
            build_user_keyboard(user_id, banned)
        )
    )


async def unban_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    await query.answer()

    if not await is_admin(update):
        await query.answer(
            "❌ Réservé aux administrateurs.",
            show_alert=True
        )
        return

    user_id = int(query.data.split(":")[1])

    try:
        await update.effective_chat.unban_member(user_id)
        set_banned(update.effective_chat.id, user_id, False)

        user = get_user(update.effective_chat.id, user_id)

        if not user:
            await query.edit_message_text(
                f"🔓 Utilisateur {user_id} débanni."
            )
            return

        await query.edit_message_text(
            user_card_text(user),
            reply_markup=InlineKeyboardMarkup(
                build_user_keyboard(user_id, False)
            )
        )

    except Exception as error:
        print("Erreur lors du débannissement :", error)

        await query.edit_message_text(
            "❌ Impossible de débannir cet utilisateur."
        )


# =========================
# AVERTISSEMENTS
# =========================

async def confirm_warning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    await query.answer()

    user_id = int(query.data.split(":")[1])

    keyboard = [
        [
            InlineKeyboardButton(
                "⚠️ Oui, avertir",
                callback_data=f"warning:{user_id}"
            ),
            InlineKeyboardButton(
                "❌ Annuler",
                callback_data=f"cancel_warning:{user_id}"
            )
        ]
    ]

    await query.edit_message_text(
        f"⚠️ Confirmer l'avertissement de l'utilisateur {user_id} ?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def cancel_warning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    await query.answer()

    user_id = int(query.data.split(":")[1])

    user = get_user(update.effective_chat.id, user_id)

    if not user:
        await query.edit_message_text(
            "❌ Utilisateur introuvable."
        )
        return

    _, username, first_name, last_name, banned, warnings = user

    await query.edit_message_text(
        user_card_text(user),
        reply_markup=InlineKeyboardMarkup(
            build_user_keyboard(user_id, banned)
        )
    )


async def warning_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    await query.answer()

    if not await is_admin(update):
        await query.answer(
            "❌ Réservé aux administrateurs.",
            show_alert=True
        )
        return

    user_id = int(query.data.split(":")[1])
    admin_id = update.effective_user.id
    reason = "Avertissement manuel"

    user = get_user(update.effective_chat.id, user_id)

    if not user:
        await query.edit_message_text(
            "❌ Utilisateur introuvable."
        )
        return

    add_warning(update.effective_chat.id, user_id)
    add_warning_history(update.effective_chat.id, user_id, reason, admin_id)

    user = get_user(update.effective_chat.id, user_id)

    _, username, first_name, last_name, banned, warnings = user

    if warnings >= 3:
        try:
            await update.effective_chat.ban_member(user_id)
            set_banned(update.effective_chat.id, user_id, True)

            user = get_user(update.effective_chat.id, user_id)

            await query.edit_message_text(
                f"🚫 {first_name or 'Utilisateur'} a été banni automatiquement.\n\n"
                f"⚠️ Nombre d'avertissements : {warnings}\n"
                f"📝 Raison : {reason}",
                reply_markup=InlineKeyboardMarkup(
                    build_user_keyboard(user_id, True)
                )
            )

        except Exception as error:
            print("Erreur lors du bannissement automatique :", error)

            await query.edit_message_text(
                f"⚠️ Avertissement ajouté.\n\n"
                f"Avertissements : {warnings}\n"
                f"📝 Raison : {reason}\n"
                f"❌ Le bannissement automatique a échoué.",
                reply_markup=InlineKeyboardMarkup(
                    build_user_keyboard(user_id, banned)
                )
            )

        return

    user = get_user(update.effective_chat.id, user_id)

    await query.edit_message_text(
        user_card_text(user),
        reply_markup=InlineKeyboardMarkup(
            build_user_keyboard(user_id, banned)
        )
    )


async def warning_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message

    if not await is_admin(update):
        await message.reply_text(
            "❌ Tu dois être administrateur pour utiliser cette commande."
        )
        return

    # Si la commande est envoyée en réponse à un message,
    # cet utilisateur devient automatiquement la cible.
    target_user = get_target_user(message)

    if target_user:
        save_user(update.effective_chat.id, target_user)
        user = get_user(update.effective_chat.id, target_user.id)
        reason = " ".join(context.args) if context.args else "Avertissement manuel"

    else:
        if not context.args:
            await message.reply_text(
                "❌ Réponds au message de l'utilisateur à avertir, "
                "ou utilise /warning ID [raison] ou /warning @username [raison]."
            )
            return

        target = context.args[0]

        if target.startswith("@"):
            username = target[1:]
            user = get_user_by_username(update.effective_chat.id, username)
            reason = " ".join(context.args[1:]) if len(context.args) > 1 else "Avertissement manuel"
        else:
            try:
                user_id = int(target)
            except ValueError:
                await message.reply_text(
                    "❌ Utilise un ID ou un username valide."
                )
                return

            user = get_user(update.effective_chat.id, user_id)
            reason = " ".join(context.args[1:]) if len(context.args) > 1 else "Avertissement manuel"

    if not user:
        await message.reply_text(
            "❌ Cet utilisateur n'est pas dans la base."
        )
        return

    user_id = user[0]
    admin_id = update.effective_user.id

    add_warning(update.effective_chat.id, user_id)
    add_warning_history(update.effective_chat.id, user_id, reason, admin_id)

    user = get_user(update.effective_chat.id, user_id)

    _, username, first_name, last_name, banned, warnings = user

    if warnings >= 3:
        try:
            await update.effective_chat.ban_member(user_id)
            set_banned(update.effective_chat.id, user_id, True)

            await message.reply_text(
                f"🚫 {first_name or 'Utilisateur'} a été banni automatiquement.\n\n"
                f"⚠️ Avertissements : {warnings}\n"
                f"📝 Raison : {reason}"
            )

        except Exception as error:
            print("Erreur lors du bannissement automatique :", error)

            await message.reply_text(
                f"⚠️ Avertissement ajouté.\n\n"
                f"Avertissements : {warnings}\n"
                f"📝 Raison : {reason}\n"
                f"❌ Le bannissement automatique a échoué."
            )

        return

    await message.reply_text(
        f"⚠️ {first_name or 'Utilisateur'} a reçu un avertissement.\n\n"
        f"Nombre d'avertissements : {warnings}\n"
        f"📝 Raison : {reason}"
    )

# ===================================
# HISTORIQUE DES AVERTISSEMENTS
# ===================================

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

    # Si user_id et page ne sont pas fournis,
    # on les récupère depuis le bouton
    if user_id is None or page is None:
        parts = query.data.split(":")

        user_id = int(parts[1])
        page = int(parts[2])

    # Récupérer l'utilisateur dans le groupe actuel
    user = get_user(
        chat_id,
        user_id
    )

    if not user:
        await query.edit_message_text(
            "❌ Utilisateur introuvable."
        )
        return

    per_page = 10

    # Historique du groupe actuel
    history = get_warning_history_page(
        chat_id,
        user_id,
        page,
        per_page
    )

    # Nombre total d'avertissements dans le groupe actuel
    total = count_warning_history(
        chat_id,
        user_id
    )

    # Aucun historique
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

    # Sécurité si on arrive sur une page qui n'existe plus
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

        # Bouton supprimer
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

    # Navigation entre les pages
    navigation = []

    if page > 1:
        navigation.append(
            InlineKeyboardButton(
                "⬅️ Précédent",
                callback_data=(
                    f"history_page:"
                    f"{user_id}:"
                    f"{page - 1}"
                )
            )
        )

    if page < total_pages:
        navigation.append(
            InlineKeyboardButton(
                "➡️ Suivant",
                callback_data=(
                    f"history_page:"
                    f"{user_id}:"
                    f"{page + 1}"
                )
            )
        )

    if navigation:
        keyboard.append(navigation)

    # Retour à la fiche utilisateur
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
                    f"{history_id}:"
                    f"{user_id}:"
                    f"{page}"
                )
            ),
            InlineKeyboardButton(
                "❌ Annuler",
                callback_data=(
                    f"history_page:"
                    f"{user_id}:"
                    f"{page}"
                )
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

    # Suppression dans le groupe actuel
    delete_warning_history(
        chat_id,
        history_id
    )

    # Réafficher l'historique
    await history_page_button(
        update,
        context,
        user_id,
        page
    )


# ===================================
# REINITIALISATION DES AVERTISSEMENTS
# ===================================

async def unwarning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message

    if not await is_admin(update):
        await message.reply_text(
            "❌ Tu dois être administrateur pour utiliser cette commande."
        )
        return

    # Sans argument, utilise l'utilisateur ciblé par la réponse.
    if not context.args:
        target_user = get_target_user(message)

        if not target_user:
            await message.reply_text(
                "❌ Réponds au message de l'utilisateur dont tu veux réinitialiser "
                "les avertissements, ou utilise /unwarning ID ou /unwarning @username."
            )
            return

        save_user(update.effective_chat.id, target_user)
        user = get_user(update.effective_chat.id, target_user.id)

    else:
        target = context.args[0]

        if target.startswith("@"):
            username = target[1:]
            user = get_user_by_username(update.effective_chat.id, username)
        else:
            try:
                user_id = int(target)
            except ValueError:
                await message.reply_text(
                    "❌ Utilise un ID ou un username valide."
                )
                return

            user = get_user(update.effective_chat.id, user_id)

    if not user:
        await message.reply_text(
            "❌ Cet utilisateur n'est pas dans la base."
        )
        return

    user_id = user[0]

    reset_warnings(update.effective_chat.id, user_id)

    await message.reply_text(
        f"✅ Les avertissements de l'utilisateur {user_id} "
        f"ont été réinitialisés."
    )

async def confirm_reset_warning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    await query.answer()

    user_id = int(query.data.split(":")[1])

    keyboard = [
        [
            InlineKeyboardButton(
                "🔄 Oui, réinitialiser",
                callback_data=f"reset_warning:{user_id}"
            ),
            InlineKeyboardButton(
                "❌ Annuler",
                callback_data=f"cancel_reset_warning:{user_id}"
            )
        ]
    ]

    await query.edit_message_text(
        f"⚠️ Réinitialiser les avertissements de l'utilisateur {user_id} ?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def cancel_reset_warning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    await query.answer()

    user_id = int(query.data.split(":")[1])

    user = get_user(update.effective_chat.id, user_id)

    if not user:
        await query.edit_message_text(
            "❌ Utilisateur introuvable."
        )
        return

    _, username, first_name, last_name, banned, warnings = user

    await query.edit_message_text(
        user_card_text(user),
        reply_markup=InlineKeyboardMarkup(
            build_user_keyboard(user_id, banned)
        )
    )


async def reset_warning_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    await query.answer()

    if not await is_admin(update):
        await query.answer(
            "❌ Réservé aux administrateurs.",
            show_alert=True
        )
        return

    user_id = int(query.data.split(":")[1])

    reset_warnings(update.effective_chat.id, user_id)

    user = get_user(update.effective_chat.id, user_id)

    if not user:
        await query.edit_message_text(
            "❌ Utilisateur introuvable."
        )
        return

    _, username, first_name, last_name, banned, warnings = user

    await query.edit_message_text(
        user_card_text(user),
        reply_markup=InlineKeyboardMarkup(
            build_user_keyboard(user_id, banned)
        )
    )

#==========================
# verification user
#==========================

async def is_user_admin(chat, user_id):
    member = await chat.get_member(user_id)

    return member.status in (
        "administrator",
        "creator"
    )

#==========================
# AUTOMODERATION
#==========================


def normalize_domain(value):
    """Nettoie un nom de domaine donné par un administrateur."""
    value = value.strip().lower()
    if not value:
        return None

    if "://" not in value:
        value = "https://" + value

    try:
        parsed = urlsplit(value)
        domain = (parsed.hostname or "").lower().rstrip(".")
    except ValueError:
        return None

    if domain.startswith("www."):
        domain = domain[4:]

    if not domain or "." not in domain:
        return None

    if not re.fullmatch(r"[a-z0-9.-]+", domain):
        return None

    if any(part == "" for part in domain.split(".")):
        return None

    return domain


def extract_message_links(message):
    """Extrait les URL visibles et les liens intégrés dans le texte."""
    text = message.text or message.caption or ""
    found = []

    entities = (
        list(message.entities or ())
        + list(message.caption_entities or ())
    )
    for entity in entities:
        if entity.type == "text_link" and entity.url:
            found.append(entity.url)

    url_pattern = (
        r"(?i)(?<![\w@])"
        r"(?:https?://|www\.|t\.me/|telegram\.me/)"
        r"[^\s<>]+"
        r"|"
        r"(?<![\w@])"
        r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
        r"[a-z]{2,}"
        r"(?:/[^\s<>]*)?"
    )

    found.extend(re.findall(url_pattern, text))

    cleaned = []
    for link in found:
        link = link.rstrip(".,!?;:)]}\"'")
        if link and link not in cleaned:
            cleaned.append(link)

    return cleaned


def parse_link(link):
    """Renvoie le domaine et une forme stable de l'URL pour compter les répétitions."""
    candidate = link.strip()
    if not re.match(r"(?i)^https?://", candidate):
        candidate = "https://" + candidate

    try:
        parsed = urlsplit(candidate)
        domain = (parsed.hostname or "").lower().rstrip(".")
        if domain.startswith("www."):
            domain = domain[4:]

        if not domain:
            return None, None

        path = parsed.path.rstrip("/")
        normalized = domain + path
        if parsed.query:
            normalized += "?" + parsed.query

        return domain, normalized.lower()
    except ValueError:
        return None, None


def domain_is_allowed(domain, allowed_domains):
    """Autorise le domaine exact et ses sous-domaines."""
    return any(
        domain == allowed or domain.endswith("." + allowed)
        for allowed in allowed_domains
    )


async def allowdomain_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat

    if not chat or chat.type not in ("group", "supergroup"):
        await message.reply_text("Cette commande doit être utilisée dans un groupe.")
        return
    if not await is_admin(update):
        await message.reply_text("❌ Réservé aux administrateurs.")
        return
    if len(context.args) != 1:
        await message.reply_text("Utilisation : /allowdomain example.com")
        return

    domain = normalize_domain(context.args[0])
    if not domain:
        await message.reply_text("❌ Domaine invalide. Exemple : /allowdomain example.com")
        return

    if add_allowed_domain(chat.id, domain):
        await message.reply_text(f"✅ Domaine autorisé : {domain}")
    else:
        await message.reply_text(f"ℹ️ {domain} est déjà dans la liste.")


async def removedomain_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat

    if not chat or chat.type not in ("group", "supergroup"):
        await message.reply_text("Cette commande doit être utilisée dans un groupe.")
        return
    if not await is_admin(update):
        await message.reply_text("❌ Réservé aux administrateurs.")
        return
    if len(context.args) != 1:
        await message.reply_text("Utilisation : /removedomain example.com")
        return

    domain = normalize_domain(context.args[0])
    if not domain:
        await message.reply_text("❌ Domaine invalide. Exemple : /removedomain example.com")
        return

    if remove_allowed_domain(chat.id, domain):
        await message.reply_text(f"✅ Domaine retiré : {domain}")
    else:
        await message.reply_text(f"ℹ️ {domain} n'était pas dans la liste.")


async def listdomains_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat

    if not chat or chat.type not in ("group", "supergroup"):
        await message.reply_text("Cette commande doit être utilisée dans un groupe.")
        return
    if not await is_admin(update):
        await message.reply_text("❌ Réservé aux administrateurs.")
        return

    domains = get_allowed_domains(chat.id)
    if not domains:
        await message.reply_text(
            "📋 Aucun domaine autorisé pour le moment.\n"
            "Les liens des domaines autorisés échappent à l'anti-spam. "
            "Les autres liens sont supprimés au 3e envoi identique en 30 minutes."
        )
        return

    await message.reply_text(
        "📋 Domaines autorisés :\n" + "\n".join(f"• {domain}" for domain in domains)
    )


async def detect_forbidden_links(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Laisse passer les deux premiers envois puis supprime le troisième lien identique en 30 minutes."""

    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if not message or not chat or not user:
        return
    if chat.type not in ("group", "supergroup"):
        return

    # Les administrateurs et le créateur sont exemptés.
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        if member.status in ("administrator", "creator"):
            return
    except Exception as error:
        print("Erreur de vérification du membre :", error)
        return

    links = extract_message_links(message)
    if not links:
        return

    # Les domaines autorisés échappent complètement à l'anti-spam.
    # Seuls les liens dont le domaine n'est pas autorisé sont comptés.
    allowed_domains = get_allowed_domains(chat.id)
    parsed_links = []

    for link in links:
        domain, normalized_link = parse_link(link)
        if not domain or not normalized_link:
            continue
        if domain_is_allowed(domain, allowed_domains):
            continue
        parsed_links.append(normalized_link)

    if not parsed_links:
        return

    # Un lien identique est compté par utilisateur et par groupe sur 30 minutes.
    now = int(time.time())
    spam_detected = False

    for normalized_link in set(parsed_links):
        count = record_link_send(
            chat.id,
            user.id,
            normalized_link,
            now,
            window_seconds=30 * 60
        )
        if count == 3:
            spam_detected = True

    if not spam_detected:
        return

    # Troisième envoi identique : supprimer puis ajouter un avertissement.
    try:
        await message.delete()
    except Exception as error:
        print("Erreur de suppression du lien répété :", error)
        return

    save_user(chat.id, user)
    add_warning(chat.id, user.id)
    add_warning_history(
        chat.id,
        user.id,
        "Spam : troisième envoi du même lien en 30 minutes",
        context.bot.id
    )

    try:
        await chat.send_message(
            f"⚠️ {user.mention_html()}, ton message a été supprimé : "
            "tu as envoyé le même lien 3 fois en 30 minutes. "
            "Un avertissement a été ajouté à ton historique.",
            parse_mode="HTML"
        )
    except Exception as error:
        print("Erreur lors de l'envoi de l'avertissement automatique :", error)

    print(
        f"Avertissement anti-spam dans {chat.id}, "
        f"utilisateur {user.id}, lien répété"
    )


#===========================
# FONCTION MUTE/UNMUTE/kick
#===========================

def get_target_user(message):
    """Récupère l'utilisateur ciblé par une réponse classique ou externe."""

    # Réponse classique à un message du groupe
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user

    # Réponse externe (notamment certains messages liés au canal)
    if message.external_reply and message.external_reply.origin:
        return message.external_reply.origin.sender_user

    return None



async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message

    # Vérifier que la commande est utilisée dans un groupe
    if not update.effective_chat or update.effective_chat.type not in (
        "group",
        "supergroup"
    ):
        await message.reply_text(
            "❌ Cette commande doit être utilisée dans un groupe."
        )
        return

    # Vérifier que la personne qui utilise /mute est administrateur
    if not await is_admin(update):
        await message.reply_text(
            "❌ Tu dois être administrateur pour utiliser cette commande."
        )
        return

    # Récupérer l'utilisateur ciblé
    target_user = get_target_user(message)

    if not target_user:
        await message.reply_text(
            "❌ Impossible d'identifier l'utilisateur ciblé."
        )
        return

    # Empêcher le mute d'un administrateur
    if await is_admin(
        Update(
            update_id=update.update_id,
            message=message
        )
    ):
        pass

    if await is_user_admin(
        update.effective_chat,
        target_user.id
    ):
        await message.reply_text(
            "❌ Impossible de mute un administrateur."
        )
        return

    await update.effective_chat.restrict_member(
        user_id=target_user.id,
        permissions=ChatPermissions(
            can_send_messages=False
        )
    )

    await message.reply_text(
        f"🔇 {target_user.first_name} a été mute."
    )


async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message

    # Vérifier que la commande est utilisée dans un groupe
    if not update.effective_chat or update.effective_chat.type not in (
        "group",
        "supergroup"
    ):
        await message.reply_text(
            "❌ Cette commande doit être utilisée dans un groupe."
        )
        return

    # Vérifier que la personne qui utilise /unmute est administrateur
    if not await is_admin(update):
        await message.reply_text(
            "❌ Tu dois être administrateur pour utiliser cette commande."
        )
        return

    # Récupérer l'utilisateur ciblé
    target_user = get_target_user(message)

    if not target_user:
        await message.reply_text(
            "❌ Impossible d'identifier l'utilisateur ciblé."
        )
        return

    # Empêcher le unmute d'un administrateur
    if await is_user_admin(
        update.effective_chat,
        target_user.id
    ):
        await message.reply_text(
            "❌ Cet utilisateur est administrateur."
        )
        return

    try:
        await update.effective_chat.restrict_member(
            user_id=target_user.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_audios=True,
                can_send_documents=True,
                can_send_photos=True,
                can_send_videos=True,
                can_send_video_notes=True,
                can_send_voice_notes=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )

        await message.reply_text(
            f"🔊 {target_user.first_name} a été unmute."
        )

    except Exception as error:
        print("Erreur lors du unmute :", error)

        await message.reply_text(
            "❌ Impossible de unmute cet utilisateur."
        )

# fonction kick

async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message

    if not update.effective_chat or update.effective_chat.type not in (
        "group",
        "supergroup"
    ):
        await message.reply_text(
            "❌ Cette commande doit être utilisée dans un groupe."
        )
        return

    if not await is_admin(update):
        await message.reply_text(
            "❌ Tu dois être administrateur pour utiliser cette commande."
        )
        return

    target_user = get_target_user(message)

    if not target_user:
        await message.reply_text(
            "❌ Impossible d'identifier l'utilisateur ciblé."
        )
        return

    if await is_user_admin(
        update.effective_chat,
        target_user.id
    ):
        await message.reply_text(
            "❌ Impossible de kick un administrateur."
        )
        return

    try:
        # Telegram n'a pas de méthode "kick" directe.
        # On bannit temporairement puis on débannit immédiatement.
        await update.effective_chat.ban_member(
            user_id=target_user.id
        )

        await update.effective_chat.unban_member(
            user_id=target_user.id
        )

        await message.reply_text(
            f"👢 {target_user.first_name} a été expulsé du groupe."
        )

    except Exception as error:
        print("Erreur lors du kick :", error)

        await message.reply_text(
            "❌ Impossible d'expulser cet utilisateur."
        )

#==========================
# NETTOYAGE DES MESSAGES
#==========================

async def clean(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat

    if not chat or chat.type not in ("group", "supergroup"):
        await message.reply_text(
            "❌ Cette commande doit être utilisée dans un groupe."
        )
        return

    if not await is_admin(update):
        await message.reply_text(
            "❌ Tu dois être administrateur pour utiliser cette commande."
        )
        return

    # ─────────────────────────────
    # MODE 1 : /clean N
    # ─────────────────────────────
    if context.args:
        try:
            count = int(context.args[0])
        except ValueError:
            await message.reply_text(
                "❌ Utilisation : /clean N\n"
                "Exemple : /clean 10"
            )
            return

        if count < 1 or count > 100:
            await message.reply_text(
                "❌ Le nombre doit être compris entre 1 et 100."
            )
            return

        deleted = 0

        first_id = message.message_id - count

        for message_id in range(first_id, message.message_id):
            try:
                await context.bot.delete_message(
                    chat_id=chat.id,
                    message_id=message_id
                )
                deleted += 1

            except Exception:
                # Message inexistant, déjà supprimé,
                # trop ancien ou impossible à supprimer.
                # On ignore simplement l'erreur.
                pass

        # Suppression de la commande /clean N
        try:
            await message.delete()
        except Exception:
            pass

        print(f"{deleted} message(s) supprimé(s).")
        return

    # ─────────────────────────────
    # MODE 2 : /clean en réponse
    # ─────────────────────────────
    if not message.reply_to_message:
        await message.reply_text(
            "❌ Réponds au message que tu veux supprimer avec /clean.\n"
            "Ou utilise /clean N pour supprimer plusieurs messages récents."
        )
        return

    target_message_id = message.reply_to_message.message_id

    try:
        await context.bot.delete_message(
            chat_id=chat.id,
            message_id=target_message_id
        )

    except Exception:
        await message.reply_text(
            "❌ Impossible de supprimer le message ciblé.\n"
            "Il est peut-être trop ancien (plus de 48 h)."
        )
        return

    # Suppression de la commande /clean
    try:
        await context.bot.delete_message(
            chat_id=chat.id,
            message_id=message.message_id
        )
    except Exception:
        pass

# =========================
# STATISTIQUES DU GROUPE
# =========================

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat

    if not chat or chat.type not in ("group", "supergroup"):
        await message.reply_text(
            "❌ Cette commande doit être utilisée dans un groupe."
        )
        return

    if not await is_admin(update):
        await message.reply_text(
            "❌ Tu dois être administrateur pour utiliser cette commande."
        )
        return

    try:
        # Nombre réel de membres du groupe
        member_count = await context.bot.get_chat_member_count(
            chat.id
        )

        # Liste des administrateurs
        administrators = await context.bot.get_chat_administrators(
            chat.id
        )

        admin_count = len(administrators)

        # Statistiques provenant de notre base
        users = get_all_users(chat.id)

        database_users = len(users)

        banned_count = sum(
            1 for user in users
            if user[4]
        )

        total_warnings = sum(
            user[5] for user in users
        )

        await message.reply_text(
            f"📊 Statistiques du groupe\n\n"
            f"👥 Membres : {member_count}\n"
            f"🛡️ Administrateurs : {admin_count}\n\n"
            f"💾 Utilisateurs dans la base : {database_users}\n"
            f"🚫 Utilisateurs bannis : {banned_count}\n"
            f"⚠️ Avertissements : {total_warnings}"
        )

    except Exception as error:
        print("Erreur lors des statistiques :", error)

        await message.reply_text(
            "❌ Impossible de récupérer les statistiques du groupe."
        )

#=======================
# ADMINS MANAGEMENT
#=======================

async def admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat

    if not chat or chat.type not in ("group", "supergroup"):
        await message.reply_text(
            "❌ Cette commande doit être utilisée dans un groupe."
        )
        return

    if not await is_admin(update):
        await message.reply_text(
            "❌ Tu dois être administrateur pour utiliser cette commande."
        )
        return

    try:
        administrators = await context.bot.get_chat_administrators(chat.id)

        text = "🛡️ Administrateurs du groupe\n\n"

        for admin in administrators:
            user = admin.user

            if admin.status == "creator":
                role = "👑 Créateur"
            else:
                role = "🛡️ Administrateur"

            name = user.full_name

            if user.username:
                name += f" (@{user.username})"

            text += f"{role}\n"
            text += f"👤 {name}\n"
            text += f"🆔 {user.id}\n\n"

        await message.reply_text(text)

    except Exception as error:
        print("Erreur lors de la récupération des administrateurs :", error)
        await message.reply_text(
            "❌ Impossible de récupérer les administrateurs."
        )

# fonction promote

async def promote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat

    if not chat or chat.type not in ("group", "supergroup"):
        await message.reply_text(
            "❌ Cette commande doit être utilisée dans un groupe."
        )
        return

    if not await is_admin(update):
        await message.reply_text(
            "❌ Tu dois être administrateur pour utiliser cette commande."
        )
        return

    if not message.reply_to_message:
        await message.reply_text(
            "❌ Réponds au message du membre que tu veux promouvoir avec /promote."
        )
        return

    target = message.reply_to_message.from_user

    if not target:
        await message.reply_text(
            "❌ Impossible d'identifier ce membre."
        )
        return

    try:
        await context.bot.promote_chat_member(
            chat_id=chat.id,
            user_id=target.id,
            can_manage_chat=True,
            can_delete_messages=True,
            can_manage_video_chats=True,
            can_restrict_members=True,
            can_pin_messages=True,
            can_promote_members=False
        )

        await message.reply_text(
            f"🛡️ {target.full_name} est maintenant administrateur."
        )

    except Exception as error:
        print("Erreur lors de la promotion :", error)
        await message.reply_text(
            "❌ Impossible de promouvoir ce membre.\n"
            "Vérifie que le bot possède les droits nécessaires."
        )

# fonction demote

async def demote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat

    if not chat or chat.type not in ("group", "supergroup"):
        await message.reply_text(
            "❌ Cette commande doit être utilisée dans un groupe."
        )
        return

    if not await is_admin(update):
        await message.reply_text(
            "❌ Tu dois être administrateur pour utiliser cette commande."
        )
        return

    if not message.reply_to_message:
        await message.reply_text(
            "❌ Réponds au message de l'administrateur que tu veux rétrograder avec /demote."
        )
        return

    target = message.reply_to_message.from_user

    if not target:
        await message.reply_text(
            "❌ Impossible d'identifier cet utilisateur."
        )
        return

    try:
        member = await chat.get_member(target.id)

        if member.status == "creator":
            await message.reply_text(
                "❌ Impossible de rétrograder le créateur du groupe."
            )
            return

        await context.bot.promote_chat_member(
            chat_id=chat.id,
            user_id=target.id,
            is_anonymous=False,
            can_manage_chat=False,
            can_delete_messages=False,
            can_manage_video_chats=False,
            can_restrict_members=False,
            can_pin_messages=False,
            can_promote_members=False,
            can_change_info=False,
            can_invite_users=False,
            can_post_messages=False,
            can_edit_messages=False
        )

        await message.reply_text(
            f"👤 {target.full_name} n'est plus administrateur."
        )

    except Exception as error:
        print("Erreur lors de la rétrogradation :", error)
        await message.reply_text(
            "❌ Impossible de rétrograder cet administrateur."
        )

# fonction permission

async def permissions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat

    if not chat or chat.type not in ("group", "supergroup"):
        await message.reply_text(
            "❌ Cette commande doit être utilisée dans un groupe."
        )
        return

    if not await is_admin(update):
        await message.reply_text(
            "❌ Tu dois être administrateur pour utiliser cette commande."
        )
        return

    if not message.reply_to_message:
        await message.reply_text(
            "❌ Réponds au message de l'administrateur avec /permissions."
        )
        return

    target = message.reply_to_message.from_user

    if not target:
        await message.reply_text(
            "❌ Impossible d'identifier cet utilisateur."
        )
        return

    try:
        member = await chat.get_member(target.id)

        if member.status == "creator":
            await message.reply_text(
                f"👑 {target.full_name} est le créateur du groupe.\n"
                "Il possède tous les droits."
            )
            return

        if member.status != "administrator":
            await message.reply_text(
                "❌ Cet utilisateur n'est pas administrateur."
            )
            return

        keyboard = [
            [
                InlineKeyboardButton(
                    f"🗑️ Supprimer {'✅' if member.can_delete_messages else '❌'}",
                    callback_data=f"perm:{target.id}:delete"
                )
            ],
            [
                InlineKeyboardButton(
                    f"🚫 Bannir {'✅' if member.can_restrict_members else '❌'}",
                    callback_data=f"perm:{target.id}:restrict"
                )
            ],
            [
                InlineKeyboardButton(
                    f"📌 Épingler {'✅' if member.can_pin_messages else '❌'}",
                    callback_data=f"perm:{target.id}:pin"
                )
            ],
            [
                InlineKeyboardButton(
                    f"👥 Inviter {'✅' if member.can_invite_users else '❌'}",
                    callback_data=f"perm:{target.id}:invite"
                )
            ],
            [
                InlineKeyboardButton(
                    f"✏️ Modifier le groupe {'✅' if member.can_change_info else '❌'}",
                    callback_data=f"perm:{target.id}:info"
                )
            ],
            [
                InlineKeyboardButton(
                    f"🛡️ Promouvoir {'✅' if member.can_promote_members else '❌'}",
                    callback_data=f"perm:{target.id}:promote"
                )
            ]
        ]

        await message.reply_text(
            f"🛡️ Permissions de {target.full_name}\n\n"
            "Appuie sur une permission pour l'activer ou la désactiver.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as error:
        print("Erreur permissions :", error)

        await message.reply_text(
            "❌ Impossible de récupérer les permissions."
        )

   # permissions bouton

async def permission_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if not await is_admin(update):
        await query.answer(
            "❌ Réservé aux administrateurs.",
            show_alert=True
        )
        return

    parts = query.data.split(":")

    user_id = int(parts[1])
    permission = parts[2]

    chat = update.effective_chat

    try:
        # Vérifier que celui qui utilise le bouton
        # possède lui-même le droit de gérer les admins.
        actor = await chat.get_member(update.effective_user.id)

        if actor.status != "creator" and not actor.can_promote_members:
            await query.answer(
                "❌ Tu n'as pas le droit de modifier les permissions.",
                show_alert=True
            )
            return

        target = await chat.get_member(user_id)

        if target.status == "creator":
            await query.answer(
                "❌ Impossible de modifier les droits du créateur.",
                show_alert=True
            )
            return

        if target.status != "administrator":
            await query.answer(
                "❌ Cet utilisateur n'est plus administrateur.",
                show_alert=True
            )
            return

        # Valeurs actuelles
        can_delete = target.can_delete_messages
        can_restrict = target.can_restrict_members
        can_pin = target.can_pin_messages
        can_invite = target.can_invite_users
        can_info = target.can_change_info
        can_promote = target.can_promote_members

        # Inverser uniquement la permission choisie
        if permission == "delete":
            can_delete = not can_delete

        elif permission == "restrict":
            can_restrict = not can_restrict

        elif permission == "pin":
            can_pin = not can_pin

        elif permission == "invite":
            can_invite = not can_invite

        elif permission == "info":
            can_info = not can_info

        elif permission == "promote":
            can_promote = not can_promote

        await context.bot.promote_chat_member(
            chat_id=chat.id,
            user_id=user_id,
            can_manage_chat=target.can_manage_chat,
            can_delete_messages=can_delete,
            can_manage_video_chats=target.can_manage_video_chats,
            can_restrict_members=can_restrict,
            can_pin_messages=can_pin,
            can_promote_members=can_promote,
            can_change_info=can_info,
            can_invite_users=can_invite
        )

        # Recharger les permissions après modification
        target = await context.bot.get_chat_member(
            chat_id=chat.id,
            user_id=user_id
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    f"🗑️ Supprimer {'✅' if target.can_delete_messages else '❌'}",
                    callback_data=f"perm:{user_id}:delete"
                )
            ],
            [
                InlineKeyboardButton(
                    f"🚫 Bannir {'✅' if target.can_restrict_members else '❌'}",
                    callback_data=f"perm:{user_id}:restrict"
                )
            ],
            [
                InlineKeyboardButton(
                    f"📌 Épingler {'✅' if target.can_pin_messages else '❌'}",
                    callback_data=f"perm:{user_id}:pin"
                )
            ],
            [
                InlineKeyboardButton(
                    f"👥 Inviter {'✅' if target.can_invite_users else '❌'}",
                    callback_data=f"perm:{user_id}:invite"
                )
            ],
            [
                InlineKeyboardButton(
                    f"✏️ Modifier le groupe {'✅' if target.can_change_info else '❌'}",
                    callback_data=f"perm:{user_id}:info"
                )
            ],
            [
                InlineKeyboardButton(
                    f"🛡️ Promouvoir {'✅' if target.can_promote_members else '❌'}",
                    callback_data=f"perm:{user_id}:promote"
                )
            ]
        ]

        await query.answer("✅ Permission modifiée.")

        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as error:
        print("Erreur modification permission :", error)

        await query.answer(
            "❌ Impossible de modifier cette permission.",
            show_alert=True
        )

# =========================
# GESTION DES ERREURS
# =========================

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    if "Message is not modified" in str(context.error):
        return

    print("========== ERREUR ==========")
    print(context.error)
    print("============================")


# =========================
# MAIN
# =========================

async def history_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "ℹ️ Ouvre la fiche d'un utilisateur puis appuie sur 📋 Historique."
    )


def main():
    if not TOKEN:
        raise ValueError(
            "BOT_TOKEN manquant dans le fichier .env"
        )

    create_tables()

    app = Application.builder().token(TOKEN).build()

    # Commandes
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("warning", warning_command))
    app.add_handler(CommandHandler("unwarning", unwarning))
    app.add_handler(CommandHandler("users", users_list))
    app.add_handler(CommandHandler("user", user_info))
    app.add_handler(CommandHandler("history", history_help))
    app.add_handler(CommandHandler("mute", mute))
    app.add_handler(CommandHandler("unmute", unmute))
    app.add_handler(CommandHandler("kick", kick))
    app.add_handler(CommandHandler("clean", clean))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("admins", admins))
    app.add_handler(CommandHandler("promote", promote))
    app.add_handler(CommandHandler("demote", demote))
    app.add_handler(CommandHandler("permissions", permissions))
    app.add_handler(CommandHandler("allowdomain", allowdomain_command))
    app.add_handler(CommandHandler("removedomain", removedomain_command))
    app.add_handler(CommandHandler("listdomains", listdomains_command))

    # Fiches utilisateurs
    app.add_handler(
        CallbackQueryHandler(
            user_button,
            pattern="^user:"
        )
    )

    # Pagination
    app.add_handler(
        CallbackQueryHandler(
            users_buttons,
            pattern="^users:"
        )
    )

    # Bannissement
    app.add_handler(
        CallbackQueryHandler(
            confirm_ban,
            pattern="^confirm_ban:"
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            cancel_ban,
            pattern="^cancel_ban:"
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            ban_button,
            pattern="^ban:"
        )
    )

    # Débannissement
    app.add_handler(
        CallbackQueryHandler(
            confirm_unban,
            pattern="^confirm_unban:"
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            cancel_unban,
            pattern="^cancel_unban:"
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            unban_button,
            pattern="^unban:"
        )
    )

    # Avertissements
    app.add_handler(
        CallbackQueryHandler(
            confirm_warning,
            pattern="^confirm_warning:"
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            cancel_warning,
            pattern="^cancel_warning:"
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            warning_button,
            pattern="^warning:"
        )
    )

    # Historique des avertissements
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

    # Réinitialisation des avertissements
    app.add_handler(
        CallbackQueryHandler(
            confirm_reset_warning,
            pattern="^confirm_reset_warning:"
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            cancel_reset_warning,
            pattern="^cancel_reset_warning:"
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            reset_warning_button,
            pattern="^reset_warning:"
        )
    )

    # Nouveaux membres
    app.add_handler(
        MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS,
            welcome
        )
    )



    # Automodération : liens interdits
    app.add_handler(
        MessageHandler(
            filters.ChatType.GROUPS
            & (filters.TEXT | filters.CAPTION)
            & ~filters.COMMAND,
            detect_forbidden_links
        )
    )

    # bouton permission
    app.add_handler(
        CallbackQueryHandler(
            permission_button,
            pattern="^perm:"
        )
    )


    # Gestion globale des erreurs
    app.add_error_handler(error_handler)

    print("Bot démarré...")
    app.run_polling()


if __name__ == "__main__":
    main()
