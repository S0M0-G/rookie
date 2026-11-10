from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from core.config import BOT_OWNER_ID
from database import (
    list_owners,
    get_owner,
    get_owner_restrictions,
    set_owner_status,
    set_owner_restriction,
)


FEATURES = {
    "moderation": "Modération",
    "warnings": "Avertissements",
    "automod": "Anti-spam et liens",
    "users": "Utilisateurs",
    "history": "Historique",
    "permissions": "Permissions",
    "administration": "Administration",
    "welcome": "Messages de bienvenue",
    "publishing": "Publications",
    "all": "Toutes les fonctionnalités",
}


def is_principal_admin(update):
    chat = update.effective_chat
    user = update.effective_user

    return (
        chat is not None
        and chat.type == "private"
        and user is not None
        and BOT_OWNER_ID is not None
        and user.id == BOT_OWNER_ID
    )


def owner_name(owner):
    name = owner[2] or "Sans nom"

    if owner[1]:
        name += f" (@{owner[1]})"

    return name


def owners_keyboard():
    owners_list = list_owners()
    keyboard = []

    for owner in owners_list:
        telegram_id = owner[0]
        name = owner_name(owner)

        keyboard.append([
            InlineKeyboardButton(
                name,
                callback_data=f"owners:detail:{telegram_id}",
            )
        ])

    return InlineKeyboardMarkup(keyboard)


async def owners(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message

    if not is_principal_admin(update):
        if update.effective_chat and update.effective_chat.type == "private":
            await message.reply_text("Accès refusé.")
        return

    owners_list = list_owners()

    if not owners_list:
        await message.reply_text(
            "Aucun responsable n'est actuellement enregistré."
        )
        return

    await message.reply_text(
        "ADMINISTRATION GLOBALE\n\n"
        "Sélectionne un responsable :",
        reply_markup=owners_keyboard(),
    )


async def show_owner(query, owner_id):
    owner = get_owner(owner_id)

    if not owner:
        await query.edit_message_text(
            "Ce responsable n'existe plus.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    "Retour à la liste",
                    callback_data="owners:list",
                )
            ]]),
        )
        return

    # Récupération des compteurs sans afficher de données privées.
    owner_data = next(
        (item for item in list_owners() if item[0] == owner_id),
        None,
    )

    if not owner_data:
        await query.edit_message_text("Responsable introuvable.")
        return

    _, _, _, status, groups, channels, active = owner_data
    total = groups + channels

    restrictions = get_owner_restrictions(owner_id)
    active_restrictions = [
        (feature, reason)
        for feature, restricted, reason in restrictions
        if restricted
    ]

    text = (
        "FICHE DU RESPONSABLE\n\n"
        f"Nom : {owner_name(owner)}\n"
        f"ID : {owner_id}\n"
        f"Statut : {'Actif' if status == 'active' else 'Bloqué'}\n"
        f"Groupes : {groups}\n"
        f"Canaux : {channels}\n"
        f"Ressources actives : {active}/{total}\n\n"
        "Restrictions actives :\n"
    )

    if active_restrictions:
        for feature, reason in active_restrictions:
            label = FEATURES.get(feature, feature)
            text += f"• {label}"

            if reason:
                text += f" — {reason}"

            text += "\n"
    else:
        text += "Aucune\n"

    keyboard = []

    if owner_id == BOT_OWNER_ID:
        text += "\nCe compte est l'administrateur principal."
    elif status == "active":
        keyboard.append([
            InlineKeyboardButton(
                "Bloquer",
                callback_data=f"owners:ask:block:{owner_id}",
            )
        ])
    else:
        keyboard.append([
            InlineKeyboardButton(
                "Débloquer",
                callback_data=f"owners:ask:unblock:{owner_id}",
            )
        ])

    if owner_id != BOT_OWNER_ID:
        keyboard.extend([
            [InlineKeyboardButton(
                "Restreindre une fonctionnalité",
                callback_data=f"owners:features:{owner_id}",
            )],
            [InlineKeyboardButton(
                "Lever une restriction",
                callback_data=f"owners:unrestrict:{owner_id}",
            )],
        ])

    keyboard.append([
        InlineKeyboardButton(
            "Retour à la liste",
            callback_data="owners:list",
        )
    ])

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def show_features(query, owner_id, action):
    if not get_owner(owner_id) or owner_id == BOT_OWNER_ID:
        return

    restrictions = get_owner_restrictions(owner_id)
    restricted_features = {
        feature
        for feature, restricted, _ in restrictions
        if restricted
    }

    feature_buttons = []

    for feature, label in FEATURES.items():
        if action == "restrict" and feature in restricted_features:
            continue

        if action == "unrestrict" and feature not in restricted_features:
            continue

        feature_buttons.append([
            InlineKeyboardButton(
                label,
                callback_data=(
                    f"owners:ask:{action}:{owner_id}:{feature}"
                ),
            )
        ])

    if not feature_buttons:
        await query.edit_message_text(
            "Aucune fonctionnalité disponible pour cette action.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    "Retour",
                    callback_data=f"owners:detail:{owner_id}",
                )
            ]]),
        )
        return

    keyboard = feature_buttons + [[
        InlineKeyboardButton(
            "Retour",
            callback_data=f"owners:detail:{owner_id}",
        )
    ]]

    title = (
        "Choisis la fonctionnalité à restreindre :"
        if action == "restrict"
        else "Choisis la restriction à lever :"
    )

    await query.edit_message_text(
        title,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def confirm_action(query, action, owner_id, feature=None):
    owner = get_owner(owner_id)

    if not owner or owner_id == BOT_OWNER_ID:
        return

    if action == "block":
        description = "Bloquer ce responsable ?"
    elif action == "unblock":
        description = "Débloquer ce responsable ?"
    elif action == "restrict":
        description = (
            f"Restreindre : {FEATURES[feature]} ?"
        )
    else:
        description = (
            f"Lever la restriction : {FEATURES[feature]} ?"
        )

    if action in ("block", "unblock"):
        yes_data = f"owners:do:{action}:{owner_id}"
    else:
        yes_data = (
            f"owners:do:{action}:{owner_id}:{feature}"
        )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "Confirmer",
                callback_data=yes_data,
            ),
            InlineKeyboardButton(
                "Annuler",
                callback_data=f"owners:detail:{owner_id}",
            ),
        ]
    ])

    await query.edit_message_text(
        description,
        reply_markup=keyboard,
    )


async def execute_action(query, action, owner_id, feature=None):
    owner = get_owner(owner_id)

    if not owner or owner_id == BOT_OWNER_ID:
        return

    if action == "block":
        set_owner_status(owner_id, "blocked")
        result = "Responsable bloqué."
    elif action == "unblock":
        set_owner_status(owner_id, "active")
        result = "Responsable débloqué."
    elif action == "restrict":
        set_owner_restriction(
            owner_id,
            feature,
            restricted=True,
            reason="Restriction appliquée par l'administrateur principal.",
        )
        result = f"Restriction appliquée : {FEATURES[feature]}."
    elif action == "unrestrict":
        set_owner_restriction(
            owner_id,
            feature,
            restricted=False,
            reason=None,
        )
        result = f"Restriction levée : {FEATURES[feature]}."
    else:
        return

    await show_owner(query, owner_id)


async def owners_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not is_principal_admin(update):
        await query.answer("Accès refusé.", show_alert=True)
        return

    await query.answer()

    parts = (query.data or "").split(":")
    if len(parts) < 2 or parts[0] != "owners":
        return

    action = parts[1]

    try:
        if action == "list":
            owners_list = list_owners()

            if not owners_list:
                await query.edit_message_text(
                    "Aucun responsable n'est actuellement enregistré."
                )
                return

            await query.edit_message_text(
                "ADMINISTRATION GLOBALE\n\n"
                "Sélectionne un responsable :",
                reply_markup=owners_keyboard(),
            )

        elif action == "detail" and len(parts) == 3:
            await show_owner(query, int(parts[2]))

        elif action == "features" and len(parts) == 3:
            await show_features(
                query,
                int(parts[2]),
                "restrict",
            )

        elif action == "unrestrict" and len(parts) == 3:
            await show_features(
                query,
                int(parts[2]),
                "unrestrict",
            )

        elif action == "ask" and len(parts) in (4, 5):
            operation = parts[2]
            owner_id = int(parts[3])
            feature = parts[4] if len(parts) == 5 else None

            if operation not in (
                "block",
                "unblock",
                "restrict",
                "unrestrict",
            ):
                return

            if operation in ("restrict", "unrestrict"):
                if feature not in FEATURES:
                    return

            await confirm_action(
                query,
                operation,
                owner_id,
                feature,
            )

        elif action == "do" and len(parts) in (4, 5):
            operation = parts[2]
            owner_id = int(parts[3])
            feature = parts[4] if len(parts) == 5 else None

            if operation not in (
                "block",
                "unblock",
                "restrict",
                "unrestrict",
            ):
                return

            if operation in ("restrict", "unrestrict"):
                if feature not in FEATURES:
                    return

            await execute_action(
                query,
                operation,
                owner_id,
                feature,
            )

    except (ValueError, IndexError):
        await query.edit_message_text("Demande invalide.")


def register_owners_handlers(app):
    app.add_handler(CommandHandler("owners", owners))
    app.add_handler(
        CallbackQueryHandler(
            owners_callback,
            pattern=r"^owners:",
        )
    )
