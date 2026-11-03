from telegram.ext import ContextTypes


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    if "Message is not modified" in str(context.error):
        return

    print("========== ERREUR ==========")
    print(context.error)
    print("============================")


def register_error_handlers(app):
    app.add_error_handler(error_handler)
