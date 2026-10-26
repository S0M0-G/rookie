from telegram import Update
from telegram.ext import ContextTypes, CommandHandler


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "Bot de gestion Telegram activé.\n\n"
        "Commandes disponibles :\n"
        "/start - Démarrer\n"
        "/help - Afficher l'aide\n"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "Commandes d'administration :\n\n"
        "/ban - Bannir un utilisateur\n"
        "/unban - Débannir un utilisateur\n"
        "/warning - Avertir un utilisateur\n"
        "/unwarning - Réinitialiser les avertissements\n"
        "/users - Voir la base de données sur les utilisateurs\n"
        "/user - Voir les infos d'un utilisateur\n"
        "/history - pour l'historique des warnings\n"
        "/mute - empeche l'envoi de message\n"
        "/unmute - retablie l'envoi de message\n"
        "/kick - expulser un utilisateur \n"
        "/clean - supprimer un message \n"
        "/stats - Afficher les statistiques du groupe\n"
        "/admins - liste et gestion des admins \n"
        "/promote - promouvoir en admin un utilisateur \n"
        "/demote - enlever les droits admins \n"
        "/permissions - voir et gerer les permissions d'un admin \n"
        "/allowdomain example.com - Autoriser un domaine (admin)\n"
        "/removedomain example.com - Retirer un domaine (admin)\n"
        "/listdomains - Afficher les domaines autorisés (admin)"
    )


async def history_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "ℹ️ Ouvre la fiche d'un utilisateur puis appuie sur 📋 Historique."
    )


def register_general_handlers(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("history", history_help))
