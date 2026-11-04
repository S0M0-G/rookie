from database.connection import connect

def add_allowed_domain(chat_id, domain):
    connection = connect()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO allowed_domains (chat_id, domain) VALUES (?, ?)",
        (chat_id, domain)
    )
    added = cursor.rowcount > 0
    connection.commit()
    connection.close()
    return added


def remove_allowed_domain(chat_id, domain):
    connection = connect()
    cursor = connection.cursor()
    cursor.execute(
        "DELETE FROM allowed_domains WHERE chat_id = ? AND domain = ?",
        (chat_id, domain)
    )
    removed = cursor.rowcount > 0
    connection.commit()
    connection.close()
    return removed


def get_allowed_domains(chat_id):
    connection = connect()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT domain FROM allowed_domains WHERE chat_id = ? ORDER BY domain COLLATE NOCASE",
        (chat_id,)
    )
    domains = [row[0] for row in cursor.fetchall()]
    connection.close()
    return domains


def record_link_send(
    chat_id,
    user_id,
    normalized_link,
    sent_at,
    message_id,
    window_seconds=1800
):
    """Enregistre un lien et renvoie son nombre d'envois et les IDs des messages."""
    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM link_attempts WHERE sent_at < ?",
        (sent_at - window_seconds,)
    )

    cursor.execute("""
        SELECT message_id
        FROM link_attempts
        WHERE chat_id = ?
          AND user_id = ?
          AND normalized_link = ?
          AND sent_at >= ?
        ORDER BY sent_at ASC
    """, (
        chat_id,
        user_id,
        normalized_link,
        sent_at - window_seconds
    ))

    previous_messages = [
        row[0] for row in cursor.fetchall()
        if row[0] is not None
    ]

    cursor.execute("""
        SELECT COUNT(*)
        FROM link_attempts
        WHERE chat_id = ?
          AND user_id = ?
          AND normalized_link = ?
          AND sent_at >= ?
    """, (
        chat_id,
        user_id,
        normalized_link,
        sent_at - window_seconds
    ))

    previous_count = cursor.fetchone()[0]

    cursor.execute("""
        INSERT INTO link_attempts (
            chat_id, user_id, normalized_link, sent_at, message_id
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        chat_id,
        user_id,
        normalized_link,
        sent_at,
        message_id
    ))

    connection.commit()
    connection.close()

    message_ids = previous_messages + [message_id]

    return previous_count + 1, message_ids
