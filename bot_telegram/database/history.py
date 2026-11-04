from database.connection import connect


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
