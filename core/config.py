from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

APP_NAME = "Jarvis"
SESSION_LOG_FILE = LOGS_DIR / "session.log"