import os
import shutil
from database.connection import DATABASE, connect

def migrate_database():
    connection = connect()
    cursor = connection.cursor()

    # Vérifier si la table users existe
    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name = 'users'
    """)

    users_exists = cursor.fetchone()

    if not users_exists:
        connection.close()
        return

    # Vérifier si chat_id existe déjà
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]

    if "chat_id" in columns:
        connection.close()
        return

    print("Migration de la base de données en cours...")

    # Sauvegarde de sécurité
    backup_path = DATABASE + ".backup"

    if not os.path.exists(backup_path):
        shutil.copy2(DATABASE, backup_path)
        print("Sauvegarde créée :", backup_path)

    try:
        # ---------------------------------
        # ANCIENNE TABLE USERS
        # ---------------------------------

        cursor.execute("""
            ALTER TABLE users
            RENAME TO users_old
        """)

        cursor.execute("""
            CREATE TABLE users (
                chat_id INTEGER NOT NULL,
                id INTEGER NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                is_banned INTEGER DEFAULT 0,
                warnings INTEGER DEFAULT 0,
                PRIMARY KEY (chat_id, id)
            )
        """)

        # Anciennes données :
        # chat_id = 0 signifie données historiques
        cursor.execute("""
            INSERT INTO users (
                chat_id,
                id,
                username,
                first_name,
                last_name,
                is_banned,
                warnings
            )
            SELECT
                0,
                id,
                username,
                first_name,
                last_name,
                is_banned,
                warnings
            FROM users_old
        """)

        cursor.execute("DROP TABLE users_old")

        # ---------------------------------
        # ANCIENNE TABLE WARNINGS_HISTORY
        # ---------------------------------

        cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name = 'warnings_history'
        """)

        history_exists = cursor.fetchone()

        if history_exists:

            cursor.execute("PRAGMA table_info(warnings_history)")
            history_columns = [
                column[1]
                for column in cursor.fetchall()
            ]

            if "chat_id" not in history_columns:

                cursor.execute("""
                    ALTER TABLE warnings_history
                    RENAME TO warnings_history_old
                """)

                cursor.execute("""
                    CREATE TABLE warnings_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        chat_id INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        reason TEXT,
                        admin_id INTEGER,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                cursor.execute("""
                    INSERT INTO warnings_history (
                        id,
                        chat_id,
                        user_id,
                        reason,
                        admin_id,
                        created_at
                    )
                    SELECT
                        id,
                        0,
                        user_id,
                        reason,
                        admin_id,
                        created_at
                    FROM warnings_history_old
                """)

                cursor.execute(
                    "DROP TABLE warnings_history_old"
                )

        connection.commit()

        print("Migration terminée avec succès.")

    except Exception as error:
        connection.rollback()
        print("Erreur pendant la migration :", error)
        raise

    finally:
        connection.close()


# =================================
# CRÉATION DE LA BASE DE DONNÉES
# =================================

def create_tables():

    # Effectuer la migration si nécessaire
    migrate_database()

    connection = connect()
    cursor = connection.cursor()

    # ---------------------------------
    # TABLE USERS
    # ---------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            chat_id INTEGER NOT NULL,
            id INTEGER NOT NULL,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            is_banned INTEGER DEFAULT 0,
            warnings INTEGER DEFAULT 0,
            PRIMARY KEY (chat_id, id)
        )
    """)

    # ---------------------------------
    # TABLE WARNINGS HISTORY
    # ---------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS warnings_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            reason TEXT,
            admin_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ---------------------------------
    # DOMAINES AUTORISES PAR GROUPE
    # ---------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS allowed_domains (
            chat_id INTEGER NOT NULL,
            domain TEXT NOT NULL,
            PRIMARY KEY (chat_id, domain)
        )
    """)

    # ---------------------------------
    # HISTORIQUE TEMPORAIRE DES LIENS
    # ---------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS link_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            normalized_link TEXT NOT NULL,
            sent_at INTEGER NOT NULL
        )
    """)

        # Ajouter message_id aux anciennes bases si nécessaire
    cursor.execute("PRAGMA table_info(link_attempts)")
    columns = [column[1] for column in cursor.fetchall()]

    if "message_id" not in columns:
        cursor.execute(
            "ALTER TABLE link_attempts ADD COLUMN message_id INTEGER"
        )

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_link_attempts_lookup
        ON link_attempts (chat_id, user_id, normalized_link, sent_at)
    """)

    connection.commit()
    connection.close()


# =================================
# ENREGISTREMENT DES UTILISATEURS
# =================================
