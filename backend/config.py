
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "").strip()
SARVAM_MODEL = os.getenv("SARVAM_MODEL", "sarvam-105b").strip()
SARVAM_BASE_URL = os.getenv("SARVAM_BASE_URL", "https://api.sarvam.ai").rstrip("/")
MAX_FILE_MB = int(os.getenv("MAX_FILE_MB", "20"))
SARVAM_TIMEOUT_SECONDS = float(os.getenv("SARVAM_TIMEOUT_SECONDS", "45"))
SARVAM_MAX_RETRIES = int(os.getenv("SARVAM_MAX_RETRIES", "2"))
DAILY_LIMIT = int(os.getenv("DAILY_LIMIT", "20"))
ARTIFACT_DIR = backend_artifact_dir = ROOT / "backend" / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_PATH = ROOT / "backend" / "kaarkhanabot.db"
