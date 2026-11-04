from database.connection import connect

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
# AUTOMODERATION DES LIENS
# =================================

