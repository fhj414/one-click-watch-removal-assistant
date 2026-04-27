from __future__ import annotations

from typing import Any

import pandas as pd


STANDARD_COLUMNS = {
    "date": "日期",
    "amount": "金额",
    "direction": "收支方向",
    "department": "部门",
    "project": "项目",
    "customer": "客户",
    "supplier": "供应商",
    "order_no": "订单号",
    "payment_method": "付款方式",
    "invoice_status": "发票状态",
    "remark": "备注",
}


def normalize_dataframe(df: pd.DataFrame, mapping: dict[str, str]) -> pd.DataFrame:
    result = pd.DataFrame()
    result["原始行号"] = df.index + 2

    for source_column, field in mapping.items():
        if field in STANDARD_COLUMNS and source_column in df.columns:
            result[STANDARD_COLUMNS[field]] = df[source_column]

    for column in STANDARD_COLUMNS.values():
        if column not in result.columns:
            result[column] = ""

    result["原始记录"] = df.astype(str).agg(" | ".join, axis=1)
    result["日期"] = pd.to_datetime(result["日期"], errors="coerce")
    result["金额"] = (
        result["金额"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("￥", "", regex=False)
        .str.replace("¥", "", regex=False)
        .str.strip()
    )
    result["金额"] = pd.to_numeric(result["金额"], errors="coerce")

    result["收支方向"] = result.apply(_normalize_direction, axis=1)
    for column in ["部门", "项目", "客户", "供应商", "订单号", "付款方式", "发票状态", "备注"]:
        result[column] = result[column].fillna("").astype(str).str.strip()

    result["月份"] = result["日期"].dt.to_period("M").astype(str).replace("NaT", "")
    result["净额"] = result.apply(
        lambda row: row["金额"] if row["收支方向"] == "收入" else (-row["金额"] if row["收支方向"] == "支出" else 0),
        axis=1,
    )
    return result


def _normalize_direction(row: pd.Series) -> str:
    value = str(row.get("收支方向", "")).strip()
    amount = row.get("金额")
    if value in {"收入", "收", "进账", "贷", "credit", "Credit", "+"}:
        return "收入"
    if value in {"支出", "支", "出账", "借", "debit", "Debit", "-"}:
        return "支出"
    if isinstance(amount, (int, float)) and pd.notna(amount):
        if amount < 0:
            return "支出"
    return "未知"


def dataframe_preview(df: pd.DataFrame, limit: int = 20) -> list[dict[str, Any]]:
    preview = df.head(limit).copy()
    for column in preview.columns:
        if pd.api.types.is_datetime64_any_dtype(preview[column]):
            preview[column] = preview[column].dt.strftime("%Y-%m-%d").fillna("")
    preview = preview.where(pd.notna(preview), "")
    return preview.to_dict(orient="records")
