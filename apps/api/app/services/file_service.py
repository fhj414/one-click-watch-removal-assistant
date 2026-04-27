from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import HTTPException, UploadFile

from app.core.config import ALLOWED_EXTENSIONS, HISTORY_DIR, UPLOAD_DIR
from app.core.storage import append_record, now_iso, read_json, write_json
from app.services.field_detector import detect_mapping


UPLOAD_INDEX = HISTORY_DIR / "uploads.json"


def read_dataframe(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path, dtype=str, keep_default_na=False)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path, dtype=str, keep_default_na=False)
    raise HTTPException(status_code=400, detail="仅支持 xlsx、xls、csv 文件")


def _json_safe_rows(df: pd.DataFrame, limit: int = 20) -> list[dict[str, Any]]:
    rows = df.head(limit).where(pd.notna(df), "").to_dict(orient="records")
    return [{str(k): ("" if v is None else v) for k, v in row.items()} for row in rows]


async def save_upload(file: UploadFile) -> dict[str, Any]:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="仅支持 xlsx、xls、csv 文件")

    upload_id = str(uuid.uuid4())
    stored_path = UPLOAD_DIR / f"{upload_id}{suffix}"
    with stored_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    df = read_dataframe(stored_path)
    columns = [str(column) for column in df.columns]
    sample_rows = _json_safe_rows(df)
    suggested_mapping = detect_mapping(columns, sample_rows)

    record = {
        "id": upload_id,
        "original_name": file.filename,
        "stored_path": str(stored_path),
        "file_type": suffix.lstrip("."),
        "rows_count": int(len(df)),
        "columns": columns,
        "sample_rows": sample_rows,
        "suggested_mapping": suggested_mapping,
        "created_at": now_iso(),
    }
    write_json(HISTORY_DIR / f"upload-{upload_id}.json", record)
    append_record(UPLOAD_INDEX, record)
    return record


def get_upload(upload_id: str) -> dict[str, Any]:
    record = read_json(HISTORY_DIR / f"upload-{upload_id}.json", None)
    if not record:
        raise HTTPException(status_code=404, detail="上传记录不存在")
    return record
