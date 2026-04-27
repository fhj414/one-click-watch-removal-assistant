from fastapi import APIRouter, UploadFile

from app.models.schemas import MappingResponse, UploadResponse
from app.services.file_service import get_upload, save_upload
from app.services.template_service import list_templates

router = APIRouter(prefix="/api/uploads", tags=["uploads"])


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
