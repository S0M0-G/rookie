from telegram import Update
from core.application import create_application
from core.startup import initialize_database, register_handlers


def main():
    initialize_database()

    app = create_application()

    register_handlers(app)

    print("Bot démarré...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
