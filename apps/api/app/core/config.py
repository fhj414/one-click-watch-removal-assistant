import os
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip().strip('"').strip("'")


def _r2_endpoint_url(account_id: str) -> str:
    endpoint = _env("R2_ENDPOINT_URL")
    if not endpoint and account_id:
        endpoint = f"https://{account_id}.r2.cloudflarestorage.com"
    if not endpoint:
        return ""
    parsed = urlsplit(endpoint)
    if parsed.scheme and parsed.netloc:
        return urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))
    return endpoint.rstrip("/")


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
OPENROUTER_API_KEY = _env("OPENROUTER_API_KEY")
OPENROUTER_MODEL = _env("OPENROUTER_MODEL", "qwen/qwen3-30b-a3b")
OPENROUTER_BASE_URL = _env("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")
OPENROUTER_SITE_URL = _env("OPENROUTER_SITE_URL", "http://127.0.0.1:3001")
OPENROUTER_APP_NAME = _env("OPENROUTER_APP_NAME", "finance-splitter-assistant")
ALLOWED_ORIGINS = [origin.strip() for origin in _env("ALLOWED_ORIGINS").split(",") if origin.strip()]
R2_ACCOUNT_ID = _env("R2_ACCOUNT_ID")
R2_ACCESS_KEY_ID = _env("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = _env("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = _env("R2_BUCKET_NAME").strip("/")
R2_ENDPOINT_URL = _r2_endpoint_url(R2_ACCOUNT_ID)
R2_PUBLIC_BASE_URL = _env("R2_PUBLIC_BASE_URL").rstrip("/")
R2_PRESIGNED_EXPIRES = int(_env("R2_PRESIGNED_EXPIRES", "3600"))
R2_UPLOAD_PREFIX = _env("R2_UPLOAD_PREFIX", "uploads").strip("/") or "uploads"
R2_EXPORT_PREFIX = _env("R2_EXPORT_PREFIX", "exports").strip("/") or "exports"


def ensure_data_dirs() -> None:
    for path in [UPLOAD_DIR, EXPORT_DIR, TEMPLATE_DIR, HISTORY_DIR]:
        path.mkdir(parents=True, exist_ok=True)
