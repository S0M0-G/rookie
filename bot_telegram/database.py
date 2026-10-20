import os
import shutil
import sqlite3


# =================================
# CHEMIN DE LA BASE DE DONNÉES
# =================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "bot.db")


def connect():
    return sqlite3.connect(DATABASE)


# =================================
# MIGRATION DE L'ANCIENNE BASE
# =================================

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

    connection.commit()
    connection.close()


# =================================
# ENREGISTREMENT DES UTILISATEURS
# =================================

def save_user(chat_id, user):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO users (
            chat_id,
            id,
            username,
            first_name,
            last_name
        )
        VALUES (?, ?, ?, ?, ?)

        ON CONFLICT(chat_id, id) DO UPDATE SET
            username = excluded.username,
            first_name = excluded.first_name,
            last_name = excluded.last_name
    """, (
        chat_id,
        user.id,
        user.username,
        user.first_name,
        user.last_name
    ))

    connection.commit()
    connection.close()


# =================================
# BANNISSEMENT
# =================================

def set_banned(chat_id, user_id, status):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE users
        SET is_banned = ?
        WHERE chat_id = ?
        AND id = ?
    """, (
        1 if status else 0,
        chat_id,
        user_id
    ))

    connection.commit()
    connection.close()


# =================================
# AVERTISSEMENTS
# =================================

def add_warning(chat_id, user_id):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE users
        SET warnings = warnings + 1
        WHERE chat_id = ?
        AND id = ?
    """, (
        chat_id,
        user_id
    ))

    connection.commit()
    connection.close()


def reset_warnings(chat_id, user_id):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE users
        SET warnings = 0
        WHERE chat_id = ?
        AND id = ?
    """, (
        chat_id,
        user_id
    ))

    connection.commit()
    connection.close()


# =================================
# HISTORIQUE DES AVERTISSEMENTS
# =================================

def add_warning_history(
    chat_id,
    user_id,
    reason,
    admin_id
):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO warnings_history (
            chat_id,
            user_id,
            reason,
            admin_id
        )
        VALUES (?, ?, ?, ?)
    """, (
        chat_id,
        user_id,
        reason,
        admin_id
    ))

    connection.commit()
    connection.close()


def get_warning_history(chat_id, user_id):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            reason,
            admin_id,
            created_at
        FROM warnings_history
        WHERE chat_id = ?
        AND user_id = ?
        ORDER BY id ASC
    """, (
        chat_id,
        user_id
    ))

    history = cursor.fetchall()

    connection.close()

    return history


def get_warning_history_page(
    chat_id,
    user_id,
    page,
    per_page=10
):

    connection = connect()
    cursor = connection.cursor()

    offset = (page - 1) * per_page

    cursor.execute("""
        SELECT
            id,
            reason,
            admin_id,
            created_at
        FROM warnings_history
        WHERE chat_id = ?
        AND user_id = ?
        ORDER BY id DESC
        LIMIT ? OFFSET ?
    """, (
        chat_id,
        user_id,
        per_page,
        offset
    ))

    history = cursor.fetchall()

    connection.close()

    return history


def count_warning_history(chat_id, user_id):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM warnings_history
        WHERE chat_id = ?
        AND user_id = ?
    """, (
        chat_id,
        user_id
    ))

    count = cursor.fetchone()[0]

    connection.close()

    return count


def delete_warning_history(chat_id, history_id):

    connection = connect()
    cursor = connection.cursor()

    # Récupérer l'utilisateur et le groupe
    cursor.execute("""
        SELECT
            user_id,
            chat_id
        FROM warnings_history
        WHERE id = ?
        AND chat_id = ?
    """, (
        history_id,
        chat_id
    ))

    result = cursor.fetchone()

    if not result:
        connection.close()
        return False

    user_id = result[0]

    # Supprimer l'avertissement
    cursor.execute("""
        DELETE FROM warnings_history
        WHERE id = ?
        AND chat_id = ?
    """, (
        history_id,
        chat_id
    ))

    # Diminuer le compteur du même utilisateur
    # dans le même groupe
    cursor.execute("""
        UPDATE users
        SET warnings = CASE
            WHEN warnings > 0 THEN warnings - 1
            ELSE 0
        END
        WHERE chat_id = ?
        AND id = ?
    """, (
        chat_id,
        user_id
    ))

    connection.commit()
    connection.close()

    return True


# =================================
# OBTENIR UN UTILISATEUR
# =================================

def get_user(chat_id, user_id):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            username,
            first_name,
            last_name,
            is_banned,
            warnings
        FROM users
        WHERE chat_id = ?
        AND id = ?
    """, (
        chat_id,
        user_id
    ))

    user = cursor.fetchone()

    connection.close()

    return user


def get_user_by_username(chat_id, username):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            username,
            first_name,
            last_name,
            is_banned,
            warnings
        FROM users
        WHERE chat_id = ?
        AND username = ?
    """, (
        chat_id,
        username
    ))

    user = cursor.fetchone()

    connection.close()

    return user


# =================================
# TOUS LES UTILISATEURS DU GROUPE
# =================================

def get_all_users(chat_id):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            username,
            first_name,
            last_name,
            is_banned,
            warnings
        FROM users
        WHERE chat_id = ?
        ORDER BY first_name COLLATE NOCASE
    """, (
        chat_id,
    ))

    users = cursor.fetchall()

    connection.close()

    return users


def get_users_page(
    chat_id,
    page,
    per_page=10
):

    connection = connect()
    cursor = connection.cursor()

    offset = (page - 1) * per_page

    cursor.execute("""
        SELECT
            id,
            username,
            first_name,
            last_name,
            is_banned,
            warnings
        FROM users
        WHERE chat_id = ?
        ORDER BY first_name COLLATE NOCASE
        LIMIT ? OFFSET ?
    """, (
        chat_id,
        per_page,
        offset
    ))

    users = cursor.fetchall()

    connection.close()

    return users


def count_users(chat_id):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE chat_id = ?
    """, (
        chat_id,
    ))

    count = cursor.fetchone()[0]

    connection.close()

    return count


# =================================
# TEST DIRECT
# =================================

if __name__ == "__main__":

    create_tables()

    print("Base de données créée/migrée avec succès.")
    print("Emplacement :", DATABASE)
