import os
from dotenv import load_dotenv

from database import (
    create_tables,
    save_user,
)

from handlers.common import (
    is_admin,
    get_target_user,
)

from handlers.ban import register_ban_handlers
from handlers.warnings import register_warnings_handlers
from handlers.general import register_general_handlers
from handlers.moderation import register_moderation_handlers
from handlers.automod import register_automod_handlers
from handlers.users import register_users_handlers
from handlers.history import register_history_handlers
from handlers.admin import register_admin_handlers
from handlers.permissions import register_permissions_handlers
from telegram import Update

from telegram.ext import (
    Application,
    MessageHandler,
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

# fonction permission

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
    register_users_handlers(app)
    register_history_handlers(app)
    register_admin_handlers(app)
    register_permissions_handlers(app)

    # Nouveaux membres
    app.add_handler(
        MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS,
            welcome
        )
    )

    # Gestion globale des erreurs
    app.add_error_handler(error_handler)

    print("Bot démarré...")
    app.run_polling()


if __name__ == "__main__":
    main()
