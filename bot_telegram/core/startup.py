from database import create_tables

from handlers.ban import register_ban_handlers
from handlers.warnings import register_warnings_handlers
from handlers.general import register_general_handlers
from handlers.moderation import register_moderation_handlers
from handlers.automod import register_automod_handlers
from handlers.users import register_users_handlers
from handlers.history import register_history_handlers
from handlers.admin import register_admin_handlers
from handlers.permissions import register_permissions_handlers
from handlers.welcome import register_welcome_handlers
from handlers.errors import register_error_handlers


def initialize_database():
    create_tables()


def register_handlers(app):
    register_general_handlers(app)
    register_ban_handlers(app)
    register_warnings_handlers(app)
    register_moderation_handlers(app)
    register_automod_handlers(app)
    register_users_handlers(app)
    register_history_handlers(app)
    register_admin_handlers(app)
    register_permissions_handlers(app)
    register_welcome_handlers(app)
    register_error_handlers(app)
