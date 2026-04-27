import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")
IS_VERCEL = os.getenv("VERCEL") == "1"
DATA_ROOT = Path(os.getenv("DATA_ROOT", "/tmp/finance-splitter" if IS_VERCEL else str(BASE_DIR / "data")))
DATA_DIR = DATA_ROOT
UPLOAD_DIR = DATA_DIR / "uploads"
EXPORT_DIR = DATA_DIR / "exports"
TEMPLATE_DIR = DATA_DIR / "templates"
HISTORY_DIR = DATA_DIR / "history"
SAMPLE_FILE = BASE_DIR.parents[1] / "sample_data" / "finance_sample.csv"

ALLOWED_EXTENSIONS = {".xlsx", ".xls", ".csv"}
PREVIEW_LIMIT = 20
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "qwen/qwen-2.5-72b-instruct")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")
OPENROUTER_SITE_URL = os.getenv("OPENROUTER_SITE_URL", "http://127.0.0.1:3001")
OPENROUTER_APP_NAME = os.getenv("OPENROUTER_APP_NAME", "finance-splitter-assistant")
ALLOWED_ORIGINS = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "").split(",") if origin.strip()]


def ensure_data_dirs() -> None:
    for path in [UPLOAD_DIR, EXPORT_DIR, TEMPLATE_DIR, HISTORY_DIR]:
        path.mkdir(parents=True, exist_ok=True)
