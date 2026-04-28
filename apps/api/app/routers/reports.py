import json
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import FileResponse, StreamingResponse

from app.models.schemas import DirectDownloadRequest, GenerateConfig, GenerateReportRequest, ReportResponse
from app.services.file_service import save_runtime_upload
from app.services.report_service import build_report_file_bytes, build_report_file_bytes_from_path, generate_report, get_report

router = APIRouter(prefix="/api/reports", tags=["reports"])


def _build_download_headers(filename: str) -> dict[str, str]:
    safe_name = "".join(ch if ord(ch) < 128 else "_" for ch in filename) or "finance-report.xlsx"
    encoded_name = quote(filename)
    return {"Content-Disposition": f"attachment; filename={safe_name}; filename*=UTF-8''{encoded_name}"}


@router.post("/generate", response_model=ReportResponse)
def create_report(payload: GenerateReportRequest):
    record = generate_report(
        payload.upload_id,
        payload.mapping,
        payload.config,
        source_url=payload.source_url,
        source_filename=payload.source_filename,
    )
    return _response(record)


@router.get("/{report_id}", response_model=ReportResponse)
def report_detail(report_id: str):
    return _response(get_report(report_id))


@router.get("/{report_id}/download")
def download_report(report_id: str):
    record = get_report(report_id)
    path = Path(record["xlsx_path"])
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="财务数据一键拆表结果.xlsx",
    )


@router.post("/download-direct")
def download_report_direct(payload: DirectDownloadRequest):
    content, filename = build_report_file_bytes(
        payload.upload_id,
        payload.mapping,
        payload.config,
        source_url=payload.source_url,
        source_filename=payload.source_filename,
    )
    headers = _build_download_headers(filename)
    return StreamingResponse(
        iter([content]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


@router.post("/download-from-file")
async def download_report_from_file(
    file: UploadFile = File(...),
    mapping_json: str = Form(...),
    config_json: str = Form(...),
):
    mapping = json.loads(mapping_json)
    config = GenerateConfig.model_validate(json.loads(config_json))
    source_path = await save_runtime_upload(file)
    content, filename = build_report_file_bytes_from_path(source_path, file.filename or "finance-data.xlsx", mapping, config)
    headers = _build_download_headers(filename)
    return StreamingResponse(
        iter([content]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


def _response(record: dict):
    return {
        "report_id": record["id"],
        "status": record["status"],
        "metrics": record["metrics"],
        "anomaly_summary": record["anomaly_summary"],
        "preview": record["preview"],
        "download_url": record["download_url"],
        "boss_summary": record["boss_summary"],
        "ai_enabled": record.get("ai_enabled", False),
        "ai_model": record.get("ai_model"),
        "download_request": record.get("download_request"),
    }
