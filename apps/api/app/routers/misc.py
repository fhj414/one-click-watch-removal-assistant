from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.core.config import HISTORY_DIR, SAMPLE_FILE
from app.core.storage import read_json

router = APIRouter(prefix="/api", tags=["misc"])


@router.get("/sample-file")
def sample_file():
    return FileResponse(SAMPLE_FILE, media_type="text/csv", filename="finance_sample.csv")


@router.get("/history")
def history():
    return {
        "uploads": read_json(HISTORY_DIR / "uploads.json", [])[:20],
        "reports": read_json(HISTORY_DIR / "reports.json", [])[:20],
    }


@router.get("/health")
def health():
    return {"ok": True, "service": "finance-splitter-api"}
