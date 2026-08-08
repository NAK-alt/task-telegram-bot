"""
Configuration Manager.
Loads environment variables and sets up application runtime settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load variables from .env file if available
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
DEFAULT_LANGUAGE: str = os.getenv("DEFAULT_LANGUAGE", "km")
DEFAULT_TIMEZONE: str = os.getenv("DEFAULT_TIMEZONE", "Asia/Phnom_Penh")
FIREBASE_SERVICE_ACCOUNT_PATH: str = os.getenv(
    "FIREBASE_SERVICE_ACCOUNT_PATH", "firebase_credentials.json"
)
DAILY_BRIEFING_TIME: str = os.getenv("DAILY_BRIEFING_TIME", "08:00")

if not BOT_TOKEN:
    print("WARNING: BOT_TOKEN is not set in environment variables or .env file.")
