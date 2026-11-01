from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

from database import (
    get_user,
    get_user_by_username,
    get_users_page,
    count_users,
)

from handlers.common import (
    build_user_keyboard,
    user_card_text,
)


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

    keyboard = build_user_keyboard(user_id, user[4])

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


def register_users_handlers(app):
    app.add_handler(CommandHandler("users", users_list))
    app.add_handler(CommandHandler("user", user_info))

    app.add_handler(
        CallbackQueryHandler(
            user_button,
            pattern="^user:"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            users_buttons,
            pattern="^users:"
        )
    )
