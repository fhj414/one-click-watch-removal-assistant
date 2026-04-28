from __future__ import annotations

import uuid
from io import BytesIO
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from app.core.config import ENABLE_REMOTE_AI_ON_GENERATE, EXPORT_DIR, HISTORY_DIR, IS_VERCEL, PREVIEW_LIMIT
from app.core.storage import append_record, now_iso, read_json, write_json
from app.services.anomaly_checker import anomaly_summary, check_anomalies
from app.services.excel_exporter import export_workbook
from app.services.file_service import get_upload, read_dataframe, resolve_source
from app.services.normalizer import dataframe_preview, normalize_dataframe
from app.services.openrouter_service import build_ai_bp_insights
from app.services.object_storage import build_export_key, guess_content_type, presigned_download_url, r2_enabled, upload_file
from app.services.report_planner import apply_report_plan, build_report_plan
from app.services.report_builder import boss_summary_text, build_metrics, build_report_tables


REPORT_INDEX = HISTORY_DIR / "reports.json"


def generate_report(upload_id: str | None, mapping: dict[str, str], config: Any, source_url: str | None = None, source_filename: str | None = None) -> dict[str, Any]:
    report_id = str(uuid.uuid4())
    if source_url:
        source_path, resolved_filename = resolve_source(None, source_url, source_filename)
    else:
        source_path, resolved_filename = resolve_source(upload_id, source_url, source_filename)
    download_source_url = source_url or _source_url_from_upload(upload_id)
    raw_df = read_dataframe(source_path)
    cleaned = normalize_dataframe(raw_df, mapping)
    anomalies = check_anomalies(cleaned) if config.enable_anomaly_check else cleaned.iloc[0:0].copy()
    report_plan = build_report_plan(cleaned, anomalies)
    base_tables = build_report_tables(cleaned, anomalies)
    ai_payload, ai_enabled, ai_model = build_ai_bp_insights(
        cleaned,
        anomalies,
        build_metrics(base_tables),
        base_tables["月度汇总表"],
        base_tables["客户汇总表"],
        base_tables["供应商汇总表"],
        config.export_version,
        config.ai_model,
        allow_remote_ai=bool(config.enable_ai_enhance and ENABLE_REMOTE_AI_ON_GENERATE),
    )
    bp_sheet = None
    if config.enable_ai_enhance and ai_payload.get("sheet_rows"):
        import pandas as pd

        bp_sheet = pd.DataFrame(ai_payload["sheet_rows"])

    tables = build_report_tables(cleaned, anomalies, bp_sheet=bp_sheet)

    selected_sheets = set(config.sheets or [])
    selected_names: set[str] | None = None
    if selected_sheets:
        from app.services.report_builder import SHEET_NAME_MAP

        selected_names = {SHEET_NAME_MAP[key] for key in selected_sheets if key in SHEET_NAME_MAP}
    tables = apply_report_plan(tables, report_plan, selected_names)

    metrics = build_metrics(tables if "管理摘要表" in tables else build_report_tables(cleaned, anomalies, bp_sheet=bp_sheet))
    anomalies_stat = anomaly_summary(anomalies)
    preview = {name: dataframe_preview(table, PREVIEW_LIMIT) for name, table in tables.items()}
    summary_text = ai_payload.get("executive_summary") if config.enable_ai_enhance else None
    if not summary_text:
        summary_text = boss_summary_text(metrics, int(anomalies_stat.get("异常总数", 0)))

    record = {
        "id": report_id,
        "upload_id": upload_id,
        "status": "succeeded",
        "config": config.model_dump(),
        "metrics": metrics,
        "anomaly_summary": anomalies_stat,
        "preview": preview,
        "xlsx_path": "",
        "download_url": f"/api/reports/{report_id}/download",
        "download_request": {
            "upload_id": None if download_source_url else upload_id,
            "source_url": download_source_url,
            "source_filename": resolved_filename,
            "mapping": mapping,
            "config": config.model_dump(),
        },
        "report_plan": report_plan,
        "boss_summary": summary_text,
        "ai_enabled": bool(config.enable_ai_enhance and ai_enabled),
        "ai_model": ai_model if config.enable_ai_enhance else None,
        "key_findings": ai_payload.get("key_findings", []),
        "risk_alerts": ai_payload.get("risk_alerts", []),
        "recommended_actions": ai_payload.get("recommended_actions", []),
        "created_at": now_iso(),
        "finished_at": now_iso(),
        "source_filename": resolved_filename,
    }
    if not IS_VERCEL:
        export_filename = f"{Path(resolved_filename).stem or 'finance-report'}-拆表结果.xlsx"
        output_path = EXPORT_DIR / f"{report_id}.xlsx"
        export_workbook(tables, output_path, enable_formulas=config.enable_formulas)
        record["xlsx_path"] = str(output_path)
        if r2_enabled():
            export_key = build_export_key(export_filename)
            upload_file(output_path, export_key, guess_content_type(export_filename))
            record["download_url"] = presigned_download_url(export_key, export_filename)
            record["export_storage_key"] = export_key
        write_json(HISTORY_DIR / f"report-{report_id}.json", record)
        append_record(REPORT_INDEX, record)
    return record


def get_report(report_id: str) -> dict[str, Any]:
    record = read_json(HISTORY_DIR / f"report-{report_id}.json", None)
    if not record:
        raise HTTPException(status_code=404, detail="报表不存在")
    return record


def build_report_file_bytes(
    upload_id: str | None,
    mapping: dict[str, str],
    config: Any,
    source_url: str | None = None,
    source_filename: str | None = None,
) -> tuple[bytes, str]:
    if source_url:
        source_path, resolved_filename = resolve_source(None, source_url, source_filename)
    else:
        source_path, resolved_filename = resolve_source(upload_id, source_url, source_filename)
    return build_report_file_bytes_from_path(source_path, resolved_filename, mapping, config)


def build_report_file_bytes_from_path(source_path: Path, source_filename: str, mapping: dict[str, str], config: Any) -> tuple[bytes, str]:
    raw_df = read_dataframe(source_path)
    cleaned = normalize_dataframe(raw_df, mapping)
    anomalies = check_anomalies(cleaned) if config.enable_anomaly_check else cleaned.iloc[0:0].copy()
    report_plan = build_report_plan(cleaned, anomalies)
    base_tables = build_report_tables(cleaned, anomalies)
    ai_payload, _, _ = build_ai_bp_insights(
        cleaned,
        anomalies,
        build_metrics(base_tables),
        base_tables["月度汇总表"],
        base_tables["客户汇总表"],
        base_tables["供应商汇总表"],
        config.export_version,
        config.ai_model,
        allow_remote_ai=False,
    )
    bp_sheet = None
    if config.enable_ai_enhance and ai_payload.get("sheet_rows"):
        import pandas as pd

        bp_sheet = pd.DataFrame(ai_payload["sheet_rows"])
    tables = build_report_tables(cleaned, anomalies, bp_sheet=bp_sheet)
    selected_sheets = set(config.sheets or [])
    selected_names: set[str] | None = None
    if selected_sheets:
        from app.services.report_builder import SHEET_NAME_MAP

        selected_names = {SHEET_NAME_MAP[key] for key in selected_sheets if key in SHEET_NAME_MAP}
    tables = apply_report_plan(tables, report_plan, selected_names)

    output_path = EXPORT_DIR / f"download-{uuid.uuid4()}.xlsx"
    export_workbook(tables, output_path, enable_formulas=config.enable_formulas)
    content = output_path.read_bytes()
    filename = f"{Path(source_filename).stem or 'finance-report'}-拆表结果.xlsx"
    return content, filename


def _source_url_from_upload(upload_id: str | None) -> str | None:
    if not upload_id:
        return None
    try:
        record = get_upload(upload_id)
    except Exception:
        return None
    value = record.get("source_url")
    return str(value) if value else None
