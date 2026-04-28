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

DYNAMIC_COLUMN_ALIASES = {
    "业务单元": ["业务单元", "事业部", "业务群", "BG", "BU", "产业", "组织单元"],
    "产品线": ["产品线", "产品", "品类", "产品类别", "产品族", "面板尺寸", "尺寸"],
    "产品型号": ["型号", "机型", "SKU", "物料", "物料编码", "料号", "产品型号"],
    "区域": ["区域", "地区", "国家", "市场", "销售区域", "海外区域"],
    "预算版本": ["预算版本", "版本", "Forecast", "FCST", "滚动预测", "预算口径"],
    "预算金额": ["预算金额", "预算", "目标金额", "目标", "Forecast金额", "预算数"],
    "费用归口": ["费用归口", "费用类型", "费用分类", "费用科目", "科目", "成本要素"],
    "客户账期": ["客户账期", "账期", "信用期", "付款周期", "回款周期", "DSO"],
    "回款状态": ["回款状态", "收款状态", "到款状态", "逾期状态", "回款进度"],
    "回款日期": ["回款日期", "收款日期", "到款日期", "到账日期"],
    "到期日期": ["到期日期", "应收到账日", "应付到期日", "付款到期日"],
    "供应商类型": ["供应商类型", "供应商分类", "供应商类别", "采购类型"],
    "订单状态": ["订单状态", "履约状态", "交付状态", "发货状态"],
}

NUMERIC_DYNAMIC_COLUMNS = {"预算金额"}
DATE_DYNAMIC_COLUMNS = {"回款日期", "到期日期"}


def normalize_dataframe(df: pd.DataFrame, mapping: dict[str, str]) -> pd.DataFrame:
    result = pd.DataFrame()
    result["原始行号"] = df.index + 2

    for source_column, field in mapping.items():
        if field in STANDARD_COLUMNS and source_column in df.columns:
            result[STANDARD_COLUMNS[field]] = df[source_column]

    for column in STANDARD_COLUMNS.values():
        if column not in result.columns:
            result[column] = ""

    used_source_columns = {source_column for source_column, field in mapping.items() if field in STANDARD_COLUMNS}
    for target_column, aliases in DYNAMIC_COLUMN_ALIASES.items():
        source_column = _best_dynamic_source(df.columns, aliases, used_source_columns)
        result[target_column] = df[source_column] if source_column else ""

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
    for column in DYNAMIC_COLUMN_ALIASES:
        if column in DATE_DYNAMIC_COLUMNS:
            result[column] = pd.to_datetime(result[column], errors="coerce")
        elif column in NUMERIC_DYNAMIC_COLUMNS:
            result[column] = pd.to_numeric(
                result[column].astype(str).str.replace(",", "", regex=False).str.replace("￥", "", regex=False).str.replace("¥", "", regex=False),
                errors="coerce",
            )
        else:
            result[column] = result[column].fillna("").astype(str).str.strip()

    result["月份"] = result["日期"].dt.to_period("M").astype(str).replace("NaT", "")
    result["净额"] = result.apply(
        lambda row: row["金额"] if row["收支方向"] == "收入" else (-row["金额"] if row["收支方向"] == "支出" else 0),
        axis=1,
    )
    return result


def _best_dynamic_source(columns: pd.Index, aliases: list[str], used_source_columns: set[str]) -> str | None:
    best_column = None
    best_score = 0
    for column in columns:
        if column in used_source_columns:
            continue
        norm = _normalize_text(column)
        for alias in aliases:
            alias_norm = _normalize_text(alias)
            score = 0
            if alias_norm == norm:
                score = 1000 + len(alias_norm)
            elif len(alias_norm) >= 2 and alias_norm in norm:
                score = 100 + len(alias_norm)
            elif len(norm) >= 2 and norm in alias_norm:
                score = 50 + len(alias_norm)
            if score > best_score:
                best_column = str(column)
                best_score = score
    return best_column


def _normalize_text(value: object) -> str:
    return "".join(ch for ch in str(value).lower() if ch.isalnum())


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
