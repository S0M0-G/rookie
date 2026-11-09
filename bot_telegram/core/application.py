from telegram.ext import Application

from core.config import TOKEN


def create_application():
    if not TOKEN:
        raise ValueError(
            "BOT_TOKEN manquant dans le fichier .env"
        )

    app = Application.builder().token(TOKEN).build()

    return app
