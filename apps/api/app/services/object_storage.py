from __future__ import annotations

import mimetypes
import uuid
from pathlib import Path
from urllib.parse import quote

import boto3
from botocore.client import BaseClient
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import (
    R2_ACCESS_KEY_ID,
    R2_BUCKET_NAME,
    R2_ENDPOINT_URL,
    R2_EXPORT_PREFIX,
    R2_PRESIGNED_EXPIRES,
    R2_PUBLIC_BASE_URL,
    R2_SECRET_ACCESS_KEY,
    R2_UPLOAD_PREFIX,
    UPLOAD_DIR,
)


def r2_enabled() -> bool:
    return bool(R2_ENDPOINT_URL and R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY and R2_BUCKET_NAME)


def build_object_key(prefix: str, filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    stem = Path(filename).stem or "finance-file"
    safe_stem = "".join(ch if ch.isascii() and (ch.isalnum() or ch in {"-", "_"}) else "-" for ch in stem)
    safe_stem = safe_stem.strip("-")[:80] or "finance-file"
    return f"{prefix}/{safe_stem}-{uuid.uuid4()}{suffix}"


def build_upload_key(filename: str) -> str:
    return build_object_key(R2_UPLOAD_PREFIX, filename)


def build_export_key(filename: str) -> str:
    return build_object_key(R2_EXPORT_PREFIX, filename)


def guess_content_type(filename: str) -> str:
    guessed, _ = mimetypes.guess_type(filename)
    return guessed or "application/octet-stream"


def create_presigned_upload(filename: str, content_type: str | None = None) -> dict[str, str | int]:
    key = build_upload_key(filename)
    client = _client()
    upload_url = client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": R2_BUCKET_NAME,
            "Key": key,
        },
        ExpiresIn=R2_PRESIGNED_EXPIRES,
        HttpMethod="PUT",
    )
    return {
        "storage_mode": "r2",
        "object_key": key,
        "upload_url": upload_url,
        "expires_in": R2_PRESIGNED_EXPIRES,
    }


def upload_file(local_path: Path, object_key: str, content_type: str | None = None) -> None:
    client = _client()
    try:
        client.put_object(
            Bucket=R2_BUCKET_NAME,
            Key=object_key,
            Body=local_path.read_bytes(),
            ContentType=content_type or guess_content_type(local_path.name),
        )
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError(f"R2 写入失败: {_error_message(exc)}") from exc


def download_to_temp(object_key: str, filename: str | None = None) -> Path:
    suffix = Path(filename or object_key).suffix.lower() or ".xlsx"
    local_path = UPLOAD_DIR / f"r2-{uuid.uuid4()}{suffix}"
    client = _client()
    try:
        response = client.get_object(Bucket=R2_BUCKET_NAME, Key=object_key)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_bytes(response["Body"].read())
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError(f"R2 读取失败: {_error_message(exc)}") from exc
    return local_path


def presigned_download_url(object_key: str, filename: str, expires_in: int | None = None) -> str:
    safe_name = "".join(ch if ord(ch) < 128 else "_" for ch in filename) or "finance-report.xlsx"
    content_disposition = f"attachment; filename={safe_name}; filename*=UTF-8''{quote(filename)}"
    if R2_PUBLIC_BASE_URL:
        return f"{R2_PUBLIC_BASE_URL.rstrip('/')}/{object_key}"
    client = _client()
    return client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": R2_BUCKET_NAME,
            "Key": object_key,
            "ResponseContentDisposition": content_disposition,
            "ResponseContentType": guess_content_type(filename),
        },
        ExpiresIn=expires_in or R2_PRESIGNED_EXPIRES,
    )


def _client() -> BaseClient:
    if not r2_enabled():
        raise RuntimeError("R2 storage is not configured")
    return boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT_URL,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name="auto",
        config=Config(
            signature_version="s3v4",
            connect_timeout=5,
            read_timeout=20,
            retries={"max_attempts": 2, "mode": "standard"},
            s3={"addressing_style": "virtual"},
        ),
    )


def _error_message(exc: Exception) -> str:
    if isinstance(exc, ClientError):
        error = exc.response.get("Error", {})
        code = error.get("Code", "ClientError")
        message = error.get("Message", str(exc))
        return f"{code}: {message}"
    return str(exc)
