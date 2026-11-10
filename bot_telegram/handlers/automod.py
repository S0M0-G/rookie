
import re
import time
from urllib.parse import urlsplit

from telegram import Update
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from database import (
    add_allowed_domain,
    remove_allowed_domain,
    get_allowed_domains,
    record_link_send,
    save_user,
    add_warning,
    add_warning_history,
)

from handlers.common import is_admin, is_user_admin


def normalize_domain(value):
    """Nettoie un nom de domaine donné par un administrateur."""
    value = value.strip().lower()
    if not value:
        return None

    if "://" not in value:
        value = "https://" + value

    try:
        parsed = urlsplit(value)
        domain = (parsed.hostname or "").lower().rstrip(".")
    except ValueError:
        return None

    if domain.startswith("www."):
        domain = domain[4:]

    if not domain or "." not in domain:
        return None

    if not re.fullmatch(r"[a-z0-9.-]+", domain):
        return None

    if any(part == "" for part in domain.split(".")):
        return None

    return domain


def extract_message_links(message):
    """Extrait les URL visibles et les liens intégrés dans le texte."""
    text = message.text or message.caption or ""
    found = []

    entities = (
        list(message.entities or ())
        + list(message.caption_entities or ())
    )

    for entity in entities:
        if entity.type == "text_link" and entity.url:
            found.append(entity.url)

    url_pattern = (
        r"(?i)(?<![\w@])"
        r"(?:https?://|www\.|t\.me/|telegram\.me/)"
        r"[^\s<>]+"
        r"|"
        r"(?<![\w@])"
        r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
        r"[a-z]{2,}"
        r"(?:/[^\s<>]*)?"
    )

    found.extend(re.findall(url_pattern, text))

    cleaned = []
    for link in found:
        link = link.rstrip(".,!?;:)]}\"'")
        if link and link not in cleaned:
            cleaned.append(link)

    return cleaned


def parse_link(link):
    """Renvoie le domaine et une forme stable de l'URL."""
    candidate = link.strip()

    if not re.match(r"(?i)^https?://", candidate):
        candidate = "https://" + candidate

    try:
        parsed = urlsplit(candidate)
        domain = (parsed.hostname or "").lower().rstrip(".")

        if domain.startswith("www."):
            domain = domain[4:]

        if not domain:
            return None, None

        path = parsed.path.rstrip("/")
        normalized = domain + path

        if parsed.query:
            normalized += "?" + parsed.query

        return domain, normalized.lower()

    except ValueError:
        return None, None


def domain_is_allowed(domain, allowed_domains):
    """Autorise le domaine exact et ses sous-domaines."""
    return any(
        domain == allowed or domain.endswith("." + allowed)
        for allowed in allowed_domains
    )


async def allowdomain_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat

    if not chat or chat.type not in ("group", "supergroup"):
        await message.reply_text("Cette commande doit être utilisée dans un groupe.")
        return

    if not await is_admin(update):
        await message.reply_text("❌ Réservé aux administrateurs.")
        return

    if len(context.args) != 1:
        await message.reply_text("Utilisation : /allowdomain example.com")
        return

    domain = normalize_domain(context.args[0])

    if not domain:
        await message.reply_text("❌ Domaine invalide. Exemple : /allowdomain example.com")
        return

    if add_allowed_domain(chat.id, domain):
        await message.reply_text(f"✅ Domaine autorisé : {domain}")
    else:
        await message.reply_text(f"ℹ️ {domain} est déjà dans la liste.")


async def removedomain_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat

    if not chat or chat.type not in ("group", "supergroup"):
        await message.reply_text("Cette commande doit être utilisée dans un groupe.")
        return

    if not await is_admin(update):
        await message.reply_text("❌ Réservé aux administrateurs.")
        return

    if len(context.args) != 1:
        await message.reply_text("Utilisation : /removedomain example.com")
        return

    domain = normalize_domain(context.args[0])

    if not domain:
        await message.reply_text("❌ Domaine invalide. Exemple : /removedomain example.com")
        return

    if remove_allowed_domain(chat.id, domain):
        await message.reply_text(f"✅ Domaine retiré : {domain}")
    else:
        await message.reply_text(f"ℹ️ {domain} n'était pas dans la liste.")


async def listdomains_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat

    if not chat or chat.type not in ("group", "supergroup"):
        await message.reply_text("Cette commande doit être utilisée dans un groupe.")
        return

    if not await is_admin(update):
        await message.reply_text("❌ Réservé aux administrateurs.")
        return

    domains = get_allowed_domains(chat.id)

    if not domains:
        await message.reply_text(
            "📋 Aucun domaine autorisé pour le moment.\n"
            "Les liens des domaines autorisés échappent à l'anti-spam. "
            "Les autres liens sont supprimés au 3e envoi identique en 30 minutes."
        )
        return

    await message.reply_text(
        "📋 Domaines autorisés :\n" + "\n".join(f"• {domain}" for domain in domains)
    )


async def detect_forbidden_links(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Supprime les trois envois lorsque le troisième lien identique arrive en 30 minutes."""

    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if not message or not chat or not user:
        return

    if chat.type not in ("group", "supergroup"):
        return

    # Les administrateurs et le créateur sont exemptés.
    try:
        if await is_user_admin(chat, user.id):
            return

    except Exception as error:
        print("Erreur de vérification du membre :", error)
        return

    links = extract_message_links(message)

    if not links:
        return

    # Les domaines autorisés échappent complètement à l'anti-spam.
    allowed_domains = get_allowed_domains(chat.id)
    parsed_links = []

    for link in links:
        domain, normalized_link = parse_link(link)

        if not domain or not normalized_link:
            continue

        if domain_is_allowed(domain, allowed_domains):
            continue

        parsed_links.append(normalized_link)

    if not parsed_links:
        return

    # Un lien identique est compté par utilisateur et par groupe sur 30 minutes.
    now = int(time.time())
    spam_detected = False
    messages_to_delete = set()

    for normalized_link in set(parsed_links):
        count, message_ids = record_link_send(
            chat.id,
            user.id,
            normalized_link,
            now,
            message.message_id,
            window_seconds=30 * 60
        )

        if count == 3:
            spam_detected = True
            messages_to_delete.update(message_ids)

    if not spam_detected:
        return

    # Supprimer les trois messages concernés.
    for message_id in messages_to_delete:
        try:
            await context.bot.delete_message(
                chat_id=chat.id,
                message_id=message_id
            )
        except Exception as error:
            print(
                f"Erreur de suppression du message {message_id} :",
                error
            )

    # Ajouter un seul avertissement pour le troisième envoi.
    save_user(chat.id, user)
    add_warning(chat.id, user.id)

    add_warning_history(
        chat.id,
        user.id,
        "Spam : troisième envoi du même lien en 30 minutes",
        context.bot.id
    )

    try:
        await chat.send_message(
            f"⚠️ {user.mention_html()}, tes trois messages contenant "
            "le même lien ont été supprimés : "
            "tu as envoyé ce lien 3 fois en 30 minutes. "
            "Un avertissement a été ajouté à ton historique.",
            parse_mode="HTML"
        )
    except Exception as error:
        print("Erreur lors de l'envoi de l'avertissement automatique :", error)

    print(
        f"Avertissement anti-spam dans {chat.id}, "
        f"utilisateur {user.id}, trois messages supprimés"
    )


def register_automod_handlers(app):
    """Enregistre les commandes et le filtre de l'automodération."""

    app.add_handler(CommandHandler("allowdomain", allowdomain_command))
    app.add_handler(CommandHandler("removedomain", removedomain_command))
    app.add_handler(CommandHandler("listdomains", listdomains_command))

    app.add_handler(
        MessageHandler(
            filters.ChatType.GROUPS
            & (filters.TEXT | filters.CAPTION)
            & ~filters.COMMAND,
            detect_forbidden_links
        )
    )

