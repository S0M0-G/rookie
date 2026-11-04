from database.connection import DATABASE, connect
from database.migrations import migrate_database, create_tables
from database.users import save_user, get_user, get_user_by_username, get_all_users, get_users_page, count_users
from database.moderation import set_banned, add_warning, reset_warnings
from database.history import add_warning_history, get_warning_history, get_warning_history_page, count_warning_history, delete_warning_history
from database.automod import add_allowed_domain, remove_allowed_domain, get_allowed_domains, record_link_send


# =================================
# ENREGISTREMENT DES UTILISATEURS
# =================================

# =================================



# =================================
# TEST DIRECT
# =================================

if __name__ == "__main__":

    create_tables()

    print("Base de données créée/migrée avec succès.")
    print("Emplacement :", DATABASE)
