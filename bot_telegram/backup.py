
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
import shutil

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "bot.db"
BACKUP_DIR = BASE_DIR / "backups"
MAX_BACKUPS = 7

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def create_backup():
    if not DB_PATH.exists():
        logging.error("Base de données introuvable.")
        return False

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_path = BACKUP_DIR / f"bot_{timestamp}.db"

    try:
        # Copie cohérente même si SQLite utilise la base.
        with sqlite3.connect(str(DB_PATH)) as source:
            with sqlite3.connect(str(backup_path)) as destination:
                source.backup(destination)

        # Vérifie l'intégrité de la sauvegarde.
        with sqlite3.connect(str(backup_path)) as check_db:
            result = check_db.execute(
                "PRAGMA integrity_check"
            ).fetchone()

        if not result or result[0] != "ok":
            backup_path.unlink(missing_ok=True)
            logging.error("Sauvegarde invalide.")
            return False

        # Conserve uniquement les 7 copies les plus récentes.
        backups = sorted(
            BACKUP_DIR.glob("bot_*.db"),
            key=lambda path: path.stat().st_mtime,
            reverse=True
        )

        for old_backup in backups[MAX_BACKUPS:]:
            old_backup.unlink()

        logging.info("Sauvegarde créée : %s", backup_path.name)
        return True

    except (sqlite3.Error, OSError) as error:
        logging.exception("Échec de la sauvegarde : %s", error)
        return False


if __name__ == "__main__":
    create_backup()

