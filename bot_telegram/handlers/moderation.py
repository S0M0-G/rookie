from telegram import Update, ChatPermissions
from telegram.ext import CommandHandler, ContextTypes

from handlers.common import is_admin, get_target_user


async def is_user_admin(chat, user_id):
    member = await chat.get_member(user_id)

    return member.status in (
        "administrator",
        "creator"
    )


async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
                pass

        try:
            await message.delete()
        except Exception:
            pass

        print(f"{deleted} message(s) supprimé(s).")
        return

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

    try:
        await context.bot.delete_message(
            chat_id=chat.id,
            message_id=message.message_id
        )
    except Exception:
        pass


def register_moderation_handlers(app):
    app.add_handler(CommandHandler("mute", mute))
    app.add_handler(CommandHandler("unmute", unmute))
    app.add_handler(CommandHandler("kick", kick))
    app.add_handler(CommandHandler("clean", clean))
