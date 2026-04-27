from __future__ import annotations

import shutil
import urllib.request
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


def fetch_remote_file(source_url: str, filename: str | None = None) -> Path:
    suffix = Path(filename or source_url).suffix.lower() or ".xlsx"
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="远程文件格式不受支持")
    temp_path = UPLOAD_DIR / f"remote-{uuid.uuid4()}{suffix}"
    try:
        with urllib.request.urlopen(source_url, timeout=30) as response, temp_path.open("wb") as file:
            shutil.copyfileobj(response, file)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"远程文件读取失败: {exc}") from exc
    return temp_path


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


async def save_runtime_upload(file: UploadFile) -> Path:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="仅支持 xlsx、xls、csv 文件")
    stored_path = UPLOAD_DIR / f"runtime-{uuid.uuid4()}{suffix}"
    with stored_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return stored_path


def get_upload(upload_id: str) -> dict[str, Any]:
    record = read_json(HISTORY_DIR / f"upload-{upload_id}.json", None)
    if not record:
        raise HTTPException(status_code=404, detail="上传记录不存在")
    return record


def resolve_source(upload_id: str | None = None, source_url: str | None = None, source_filename: str | None = None) -> tuple[Path, str]:
    if upload_id:
        record = get_upload(upload_id)
        return Path(record["stored_path"]), record["original_name"]
    if source_url:
        return fetch_remote_file(source_url, source_filename), source_filename or Path(source_url).name
    raise HTTPException(status_code=400, detail="缺少 upload_id 或 source_url")
