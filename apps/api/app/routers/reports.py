from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, StreamingResponse

from app.models.schemas import DirectDownloadRequest, GenerateReportRequest, ReportResponse
from app.services.report_service import build_report_file_bytes, generate_report, get_report

router = APIRouter(prefix="/api/reports", tags=["reports"])


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
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
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
