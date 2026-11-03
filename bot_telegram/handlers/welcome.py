from telegram import Update
from telegram.ext import MessageHandler, ContextTypes, filters

from database import save_user


async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        save_user(update.effective_chat.id, member)

        await update.message.reply_text(
            f"Bienvenue {member.first_name} !"
        )


def register_welcome_handlers(app):
    app.add_handler(
        MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS,
            welcome
        )
    )
