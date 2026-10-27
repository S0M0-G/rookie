
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

from database import (
    save_user,
    get_user,
    get_user_by_username,
    set_banned,
)

from handlers.common import (
    is_admin,
    get_target_user,
    user_card_text,
    build_user_keyboard,
)


async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message

    if not await is_admin(update):
        await message.reply_text(
            "❌ Tu dois être administrateur pour utiliser cette commande."
        )
        return

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

        if target.startswith("@"):
            username = target[1:]
            user = get_user_by_username(
                update.effective_chat.id, username
            )
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


async def confirm_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = int(query.data.split(":")[1])

    keyboard = [[
        InlineKeyboardButton(
            "🔨 Oui, bannir",
            callback_data=f"ban:{user_id}"
        ),
        InlineKeyboardButton(
            "❌ Annuler",
            callback_data=f"cancel_ban:{user_id}"
        )
    ]]

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
        await query.edit_message_text("❌ Utilisateur introuvable.")
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


async def confirm_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = int(query.data.split(":")[1])

    keyboard = [[
        InlineKeyboardButton(
            "🔓 Oui, débannir",
            callback_data=f"unban:{user_id}"
        ),
        InlineKeyboardButton(
            "❌ Annuler",
            callback_data=f"cancel_unban:{user_id}"
        )
    ]]

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
        await query.edit_message_text("❌ Utilisateur introuvable.")
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


def register_ban_handlers(app):
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))

    app.add_handler(
        CallbackQueryHandler(confirm_ban, pattern="^confirm_ban:")
    )
    app.add_handler(
        CallbackQueryHandler(cancel_ban, pattern="^cancel_ban:")
    )
    app.add_handler(
        CallbackQueryHandler(ban_button, pattern="^ban:")
    )
    app.add_handler(
        CallbackQueryHandler(confirm_unban, pattern="^confirm_unban:")
    )
    app.add_handler(
        CallbackQueryHandler(cancel_unban, pattern="^cancel_unban:")
    )
    app.add_handler(
        CallbackQueryHandler(unban_button, pattern="^unban:")
    )

