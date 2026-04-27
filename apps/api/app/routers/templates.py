from fastapi import APIRouter

from app.models.schemas import TemplateCreate, TemplateRecord
from app.services.template_service import create_template, list_templates

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("", response_model=list[TemplateRecord])
def get_templates():
    return list_templates()


@router.post("", response_model=TemplateRecord)
def save_template(payload: TemplateCreate):
    return create_template(payload.model_dump())
