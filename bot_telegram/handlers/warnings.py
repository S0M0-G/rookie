from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

from database import (
    save_user,
    get_user,
    get_user_by_username,
    set_banned,
    add_warning,
    reset_warnings,
    add_warning_history,
)

from handlers.common import (
    build_user_keyboard,
    user_card_text,
    is_admin,
    get_target_user,
)


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
        await query.edit_message_text("❌ Utilisateur introuvable.")
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
        await query.edit_message_text("❌ Utilisateur introuvable.")
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
        await message.reply_text("❌ Cet utilisateur n'est pas dans la base.")
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


async def unwarning(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
                await message.reply_text("❌ Utilise un ID ou un username valide.")
                return

            user = get_user(update.effective_chat.id, user_id)

    if not user:
        await message.reply_text("❌ Cet utilisateur n'est pas dans la base.")
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
        await query.edit_message_text("❌ Utilisateur introuvable.")
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
        await query.edit_message_text("❌ Utilisateur introuvable.")
        return

    _, username, first_name, last_name, banned, warnings = user

    await query.edit_message_text(
        user_card_text(user),
        reply_markup=InlineKeyboardMarkup(
            build_user_keyboard(user_id, banned)
        )
    )


def register_warnings_handlers(app):
    app.add_handler(CommandHandler("warning", warning_command))
    app.add_handler(CommandHandler("unwarning", unwarning))

    app.add_handler(CallbackQueryHandler(
        confirm_warning, pattern="^confirm_warning:"
    ))
    app.add_handler(CallbackQueryHandler(
        cancel_warning, pattern="^cancel_warning:"
    ))
    app.add_handler(CallbackQueryHandler(
        warning_button, pattern="^warning:"
    ))
    app.add_handler(CallbackQueryHandler(
        confirm_reset_warning, pattern="^confirm_reset_warning:"
    ))
    app.add_handler(CallbackQueryHandler(
        cancel_reset_warning, pattern="^cancel_reset_warning:"
    ))
    app.add_handler(CallbackQueryHandler(
        reset_warning_button, pattern="^reset_warning:"
    ))
