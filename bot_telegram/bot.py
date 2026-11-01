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
)

from handlers.common import (
    build_user_keyboard,
    user_card_text,
    is_admin,
    get_target_user,
)
from handlers.ban import register_ban_handlers
from handlers.warnings import register_warnings_handlers
from handlers.general import register_general_handlers
from handlers.moderation import register_moderation_handlers
from handlers.automod import register_automod_handlers
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
# NOUVEAUX MEMBRES
# =========================

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        save_user(update.effective_chat.id, member)

        await update.message.reply_text(
            f"Bienvenue {member.first_name} !"
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
# AVERTISSEMENTS
# =========================

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

#==========================
# verification user
#==========================


#==========================
# AUTOMODERATION
#==========================


#===========================
# FONCTION MUTE/UNMUTE/kick
#===========================




# fonction kick


#==========================
# NETTOYAGE DES MESSAGES
#==========================


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

def main():
    if not TOKEN:
        raise ValueError(
            "BOT_TOKEN manquant dans le fichier .env"
        )

    create_tables()

    app = Application.builder().token(TOKEN).build()

    # Commandes
    register_general_handlers(app)
    register_ban_handlers(app)
    register_warnings_handlers(app)
    register_moderation_handlers(app)
    register_automod_handlers(app)
    app.add_handler(CommandHandler("users", users_list))
    app.add_handler(CommandHandler("user", user_info))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("admins", admins))
    app.add_handler(CommandHandler("promote", promote))
    app.add_handler(CommandHandler("demote", demote))
    app.add_handler(CommandHandler("permissions", permissions))

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

    # Nouveaux membres
    app.add_handler(
        MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS,
            welcome
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
