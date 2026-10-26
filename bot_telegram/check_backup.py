from pathlib import Path
from datetime import datetime
import logging
import subprocess
import sys

BASE_DIR = Path(__file__).resolve().parent
BACKUP_DIR = BASE_DIR / "backups"
LOG_PATH = BASE_DIR / "backup_check.log"
BACKUP_SCRIPT = BASE_DIR / "backup.py"
MAX_AGE_HOURS = 12

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

def check_backup():
    files = list(BACKUP_DIR.glob("bot_*.db"))

    if files:
        latest = max(files, key=lambda p: p.stat().st_mtime)
        age_hours = (
            datetime.now().timestamp() - latest.stat().st_mtime
        ) / 3600

        if age_hours <= MAX_AGE_HOURS:
            logging.info(
                "Sauvegarde récente : %s (%.1f heures)",
                latest.name, age_hours
            )
            return

        logging.warning(
            "Sauvegarde trop ancienne : %s (%.1f heures). "
            "Nouvelle sauvegarde demandée.",
            latest.name, age_hours
        )
    else:
        logging.warning(
            "Aucune sauvegarde trouvée. Nouvelle sauvegarde demandée."
        )

    try:
        result = subprocess.run(
            [sys.executable, str(BACKUP_SCRIPT)],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.stdout.strip():
            logging.info("Sortie backup.py : %s", result.stdout.strip())
        if result.stderr.strip():
            logging.info("Messages backup.py : %s", result.stderr.strip())

        if result.returncode != 0:
            logging.error(
                "Échec de backup.py (code %s).", result.returncode
            )
            return

        new_files = list(BACKUP_DIR.glob("bot_*.db"))
        if new_files:
            latest = max(new_files, key=lambda p: p.stat().st_mtime)
            age_hours = (
                datetime.now().timestamp() - latest.stat().st_mtime
            ) / 3600

            if age_hours <= 12:
                logging.info("Nouvelle sauvegarde vérifiée : %s", latest.name)
            else:
                logging.error("La sauvegarde créée n'est pas assez récente.")
        else:
            logging.error("Aucun fichier de sauvegarde après exécution.")

    except (OSError, subprocess.SubprocessError) as error:
        logging.exception("Impossible de lancer la sauvegarde : %s", error)

if __name__ == "__main__":
    check_backup()
