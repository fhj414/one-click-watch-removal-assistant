from fastapi import APIRouter, UploadFile

from app.models.schemas import MappingResponse, RemoteUploadCreate, UploadInitRequest, UploadInitResponse, UploadResponse
from app.services.file_service import get_upload, register_remote_upload, save_upload
from app.services.object_storage import create_presigned_upload, r2_enabled
from app.services.template_service import list_templates

router = APIRouter(prefix="/api/uploads", tags=["uploads"])


@router.post("/init", response_model=UploadInitResponse)
def init_upload(payload: UploadInitRequest):
    if not r2_enabled():
        return {"storage_mode": "local"}
    try:
        return create_presigned_upload(payload.filename, payload.content_type)
    except Exception as exc:
        return {"storage_mode": "local", "storage_error": f"R2 配置异常: {exc}"}


@router.post("/complete", response_model=UploadResponse)
def complete_upload(payload: RemoteUploadCreate):
    record = register_remote_upload(
        payload.object_key,
        payload.filename,
        payload.content_type,
        columns=payload.columns,
        sample_rows=payload.sample_rows,
        rows_count=payload.rows_count,
    )
    return {
        "upload_id": record["id"],
        "filename": record["original_name"],
        "columns": record["columns"],
        "sample_rows": record["sample_rows"],
        "suggested_mapping": record["suggested_mapping"],
        "storage_mode": record.get("storage_mode", "r2"),
    }


@router.post("", response_model=UploadResponse)
async def upload_file(file: UploadFile):
    record = await save_upload(file)
    return {
        "upload_id": record["id"],
        "filename": record["original_name"],
        "columns": record["columns"],
        "sample_rows": record["sample_rows"],
        "suggested_mapping": record["suggested_mapping"],
        "storage_mode": "local",
    }


@router.get("/{upload_id}/mapping", response_model=MappingResponse)
def get_mapping(upload_id: str):
    record = get_upload(upload_id)
    return {
        "upload_id": record["id"],
        "filename": record["original_name"],
        "columns": record["columns"],
        "sample_rows": record["sample_rows"],
        "suggested_mapping": record["suggested_mapping"],
        "templates": list_templates(),
    }
