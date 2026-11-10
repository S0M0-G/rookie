import os
from pathlib import Path
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)

TOKEN = os.getenv("BOT_TOKEN")

BOT_OWNER_ID = os.getenv("BOT_OWNER_ID")

if BOT_OWNER_ID:
    BOT_OWNER_ID = int(BOT_OWNER_ID)
