from database.connection import connect


def register_resource(
    owner_id,
    owner_username,
    owner_first_name,
    chat_id,
    chat_type,
    title,
    username
):
    """Enregistre une ressource sans remplacer son responsable initial."""

    connection = connect()
    cursor = connection.cursor()

    try:
        cursor.execute("BEGIN IMMEDIATE")

        cursor.execute("""
            SELECT owner_id
            FROM resources
            WHERE chat_id = ?
        """, (chat_id,))

        existing = cursor.fetchone()

        if existing:
            cursor.execute("""
                UPDATE resources
                SET title = ?,
                    username = ?,
                    status = 'active',
                    updated_at = CURRENT_TIMESTAMP
                WHERE chat_id = ?
            """, (title, username, chat_id))

        else:
            cursor.execute("""
                INSERT INTO owners (
                    telegram_id,
                    username,
                    first_name
                )
                VALUES (?, ?, ?)

                ON CONFLICT(telegram_id) DO UPDATE SET
                    username = excluded.username,
                    first_name = excluded.first_name
            """, (
                owner_id,
                owner_username,
                owner_first_name
            ))

            cursor.execute("""
                INSERT INTO resources (
                    chat_id,
                    owner_id,
                    chat_type,
                    title,
                    username,
                    status
                )
                VALUES (?, ?, ?, ?, ?, 'active')
            """, (
                chat_id,
                owner_id,
                chat_type,
                title,
                username
            ))

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

def get_owner(owner_id):
    connection = connect()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT telegram_id, username, first_name, status
        FROM owners
        WHERE telegram_id = ?
    """, (owner_id,))

    result = cursor.fetchone()
    connection.close()

    return result


def list_owners():
    connection = connect()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            o.telegram_id,
            o.username,
            o.first_name,
            o.status,
            COUNT(
                CASE WHEN r.chat_type IN ('group', 'supergroup')
                THEN 1 END
            ),
            COUNT(
                CASE WHEN r.chat_type = 'channel'
                THEN 1 END
            ),
            COUNT(
                CASE WHEN r.status = 'active'
                THEN 1 END
            )
        FROM owners o
        LEFT JOIN resources r
            ON r.owner_id = o.telegram_id
        GROUP BY o.telegram_id
        ORDER BY o.created_at DESC
    """)

    result = cursor.fetchall()
    connection.close()

    return result


def set_owner_status(owner_id, status):
    if status not in ("active", "blocked"):
        raise ValueError("Statut invalide")

    connection = connect()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE owners
        SET status = ?
        WHERE telegram_id = ?
    """, (status, owner_id))

    updated = cursor.rowcount > 0

    connection.commit()
    connection.close()

    return updated


def get_resource_owner(chat_id):
    connection = connect()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT owner_id
        FROM resources
        WHERE chat_id = ?
    """, (chat_id,))

    result = cursor.fetchone()
    connection.close()

    return result[0] if result else None


def get_owner_resources(owner_id):
    connection = connect()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT chat_id, chat_type, title, username, status
        FROM resources
        WHERE owner_id = ?
        ORDER BY added_at DESC
    """, (owner_id,))

    result = cursor.fetchall()
    connection.close()

    return result


def set_owner_restriction(
    owner_id,
    feature,
    restricted=True,
    reason=None
):
    connection = connect()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO owner_restrictions (
            owner_id,
            feature,
            is_restricted,
            reason,
            updated_at
        )
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)

        ON CONFLICT(owner_id, feature) DO UPDATE SET
            is_restricted = excluded.is_restricted,
            reason = excluded.reason,
            updated_at = CURRENT_TIMESTAMP
    """, (
        owner_id,
        feature,
        1 if restricted else 0,
        reason
    ))

    connection.commit()
    connection.close()


def get_owner_restrictions(owner_id):
    connection = connect()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT feature, is_restricted, reason
        FROM owner_restrictions
        WHERE owner_id = ?
    """, (owner_id,))

    result = cursor.fetchall()
    connection.close()

    return result


def delete_owner(owner_id):
    """Supprime le responsable, ses ressources et leurs données."""

    connection = connect()
    cursor = connection.cursor()

    try:
        cursor.execute("BEGIN IMMEDIATE")

        cursor.execute("""
            SELECT chat_id
            FROM resources
            WHERE owner_id = ?
        """, (owner_id,))

        chat_ids = [
            row[0] for row in cursor.fetchall()
        ]

        for chat_id in chat_ids:
            for table in (
                "users",
                "warnings_history",
                "allowed_domains",
                "link_attempts"
            ):
                cursor.execute(
                    f"DELETE FROM {table} WHERE chat_id = ?",
                    (chat_id,)
                )

        cursor.execute("""
            DELETE FROM resources
            WHERE owner_id = ?
        """, (owner_id,))

        cursor.execute("""
            DELETE FROM owners
            WHERE telegram_id = ?
        """, (owner_id,))

        deleted = cursor.rowcount > 0

        connection.commit()

        return deleted

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

def set_resource_status(chat_id, status):
    if status not in ("active", "inactive"):
        raise ValueError("Statut de ressource invalide")

    connection = connect()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE resources
        SET status = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE chat_id = ?
    """, (status, chat_id))

    updated = cursor.rowcount > 0

    connection.commit()
    connection.close()

    return updated
