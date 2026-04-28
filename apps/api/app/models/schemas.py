from typing import Any, Literal

from pydantic import BaseModel, Field


StandardField = Literal[
    "date",
    "amount",
    "direction",
    "department",
    "project",
    "customer",
    "supplier",
    "order_no",
    "payment_method",
    "invoice_status",
    "remark",
    "ignore",
]


class UploadResponse(BaseModel):
    upload_id: str
    filename: str
    columns: list[str]
    sample_rows: list[dict[str, Any]]
    suggested_mapping: dict[str, StandardField]
    storage_mode: str = "local"
    storage_key: str | None = None
    source_url: str | None = None


class UploadInitRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content_type: str | None = None


class UploadInitResponse(BaseModel):
    storage_mode: str
    upload_url: str | None = None
    object_key: str | None = None
    expires_in: int | None = None
    storage_error: str | None = None


class RemoteUploadCreate(BaseModel):
    object_key: str
    filename: str = Field(min_length=1, max_length=255)
    content_type: str | None = None
    columns: list[str] | None = None
    sample_rows: list[dict[str, Any]] | None = None
    rows_count: int | None = None


class TemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    mapping: dict[str, StandardField]
    source_columns: list[str] = []


class TemplateRecord(TemplateCreate):
    id: str
    created_at: str
    updated_at: str


class GenerateConfig(BaseModel):
    sheets: list[str] = Field(default_factory=list)
    enable_anomaly_check: bool = True
    enable_formulas: bool = True
    enable_summary: bool = True
    enable_ai_enhance: bool = True
    ai_model: str | None = None
    export_version: Literal["finance", "boss", "operations"] = "finance"


class GenerateReportRequest(BaseModel):
    upload_id: str | None = None
    storage_key: str | None = None
    source_url: str | None = None
    source_filename: str | None = None
    mapping: dict[str, StandardField]
    config: GenerateConfig
    template_name: str | None = None


class ReportResponse(BaseModel):
    report_id: str
    status: str
    metrics: dict[str, Any]
    anomaly_summary: dict[str, Any]
    preview: dict[str, list[dict[str, Any]]]
    download_url: str
    boss_summary: str
    ai_enabled: bool = False
    ai_model: str | None = None
    download_request: dict[str, Any] | None = None
    report_plan: dict[str, Any] | None = None


class MappingResponse(BaseModel):
    upload_id: str
    filename: str
    columns: list[str]
    sample_rows: list[dict[str, Any]]
    suggested_mapping: dict[str, StandardField]
    templates: list[TemplateRecord]


class DirectDownloadRequest(BaseModel):
    upload_id: str | None = None
    storage_key: str | None = None
    source_url: str | None = None
    source_filename: str | None = None
    mapping: dict[str, StandardField]
    config: GenerateConfig
