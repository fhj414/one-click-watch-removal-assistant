from __future__ import annotations

import re
from typing import Any

from app.models.schemas import StandardField
from app.services.openrouter_service import enhance_mapping_with_llm


FIELD_ALIASES: dict[StandardField, list[str]] = {
    "date": ["日期", "时间", "交易日期", "发生日期", "付款日期", "收款日期", "date", "time"],
    "amount": ["金额", "实收", "应付金额", "含税金额", "价税合计", "交易金额", "收入金额", "支出金额", "amount", "money"],
    "direction": ["收支", "方向", "收入支出", "借贷", "类型", "交易类型", "direction", "type"],
    "department": ["部门", "组织", "成本中心", "业务部门", "dept", "department"],
    "project": ["项目", "项目名称", "费用项", "支出项", "业务线", "project"],
    "customer": ["客户", "客户名称", "购买方", "付款方", "往来客户", "customer"],
    "supplier": ["供应商", "供应商名称", "销售方", "收款方", "往来供应商", "supplier", "vendor"],
    "order_no": ["订单", "订单号", "流水", "流水号", "单号", "凭证号", "交易号", "order", "serial"],
    "payment_method": ["付款方式", "支付方式", "收款方式", "渠道", "payment"],
    "invoice_status": ["发票", "开票", "票据", "发票状态", "invoice"],
    "remark": ["备注", "摘要", "说明", "用途", "comment", "remark", "memo"],
    "ignore": [],
}


def _normalize(text: str) -> str:
    return re.sub(r"[\s_\-()/（）]+", "", str(text).lower())


def ai_field_detector_placeholder(column: str, values: list[Any]) -> StandardField | None:
    """Replace this function with OpenRouter/OpenAI integration later."""
    sample = " ".join(str(value) for value in values[:8] if value is not None)
    if re.search(r"\d{4}[-/年]\d{1,2}", sample):
        return "date"
    if re.search(r"收入|支出|借|贷", sample):
        return "direction"
    return None


def detect_mapping(columns: list[str], sample_rows: list[dict[str, Any]]) -> dict[str, StandardField]:
    mapping: dict[str, StandardField] = {}
    for column in columns:
        norm = _normalize(column)
        detected: StandardField = "ignore"
        best_score = 0
        for field, aliases in FIELD_ALIASES.items():
            for alias in aliases:
                alias_norm = _normalize(alias)
                score = 0
                if alias_norm == norm:
                    score = 1000 + len(alias_norm)
                elif len(alias_norm) >= 2 and alias_norm in norm:
                    score = 100 + len(alias_norm)
                elif len(norm) >= 2 and norm in alias_norm:
                    score = 50 + len(alias_norm)
                if score > best_score:
                    best_score = score
                    detected = field
        if best_score == 0:
            values = [row.get(column) for row in sample_rows]
            detected = ai_field_detector_placeholder(column, values) or "ignore"
        mapping[column] = detected
    enhanced_mapping, _, _ = enhance_mapping_with_llm(columns, sample_rows, mapping)
    return enhanced_mapping  # type: ignore[return-value]
