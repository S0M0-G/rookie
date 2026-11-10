
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from database import get_all_users
from handlers.common import is_admin, get_target_user


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
        member_count = await context.bot.get_chat_member_count(chat.id)
        administrators = await context.bot.get_chat_administrators(chat.id)
        admin_count = len(administrators)

        users = get_all_users(chat.id)
        database_users = len(users)

        banned_count = sum(1 for user in users if user[4])
        total_warnings = sum(user[5] for user in users)

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

    target = get_target_user(message)

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

    target = get_target_user(message)

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


def register_admin_handlers(app):
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("admins", admins))
    app.add_handler(CommandHandler("promote", promote))
    app.add_handler(CommandHandler("demote", demote))

