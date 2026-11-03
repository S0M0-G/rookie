from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

from handlers.common import is_admin


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


def register_permissions_handlers(app):
    app.add_handler(CommandHandler("permissions", permissions))
    app.add_handler(
        CallbackQueryHandler(
            permission_button,
            pattern="^perm:"
        )
    )
