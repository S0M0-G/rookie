from database.connection import connect


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
