from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

import pandas as pd

from app.core.config import (
    OPENROUTER_API_KEY,
    OPENROUTER_APP_NAME,
    OPENROUTER_BASE_URL,
    OPENROUTER_MODEL,
    OPENROUTER_SITE_URL,
)


def openrouter_enabled() -> bool:
    return bool(OPENROUTER_API_KEY)


def resolve_model(requested_model: str | None = None) -> str:
    return requested_model or OPENROUTER_MODEL


def enhance_mapping_with_llm(
    columns: list[str],
    sample_rows: list[dict[str, Any]],
    current_mapping: dict[str, str],
    requested_model: str | None = None,
) -> tuple[dict[str, str], bool, str | None]:
    if not openrouter_enabled():
        return current_mapping, False, None

    schema = {
        "name": "finance_field_mapping",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "mapping": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "string",
                        "enum": [
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
                        ],
                    },
                }
            },
            "required": ["mapping"],
            "additionalProperties": False,
        },
    }
    prompt = (
        "你是高级财务BP的数据建模助手。请根据列名和样本值，将原始字段映射到标准字段。"
        "优先遵循已有规则映射，只有在你非常确定时才修正。输出必须是 JSON。"
        f"\n列名: {json.dumps(columns, ensure_ascii=False)}"
        f"\n当前规则映射: {json.dumps(current_mapping, ensure_ascii=False)}"
        f"\n样本行: {json.dumps(sample_rows[:8], ensure_ascii=False)}"
    )
    response = _chat_json(prompt, schema, requested_model)
    if not response:
        return current_mapping, False, resolve_model(requested_model)
    mapping = response.get("mapping", {})
    final_mapping = {column: mapping.get(column, current_mapping.get(column, "ignore")) for column in columns}
    return final_mapping, True, resolve_model(requested_model)


def build_ai_bp_insights(
    cleaned: pd.DataFrame,
    anomalies: pd.DataFrame,
    metrics: dict[str, Any],
    monthly: pd.DataFrame,
    customer: pd.DataFrame,
    supplier: pd.DataFrame,
    export_version: str,
    requested_model: str | None = None,
) -> tuple[dict[str, Any], bool, str | None]:
    fallback = heuristic_bp_insights(cleaned, anomalies, metrics, monthly, customer, supplier, export_version)
    if not openrouter_enabled():
        return fallback, False, None

    prompt_payload = {
        "metrics": metrics,
        "anomaly_summary": {
            "count": int(len(anomalies)),
            "top_reasons": anomalies["异常原因"].astype(str).value_counts().head(10).to_dict() if not anomalies.empty else {},
        },
        "monthly_net": monthly.to_dict(orient="records"),
        "top_customers": customer.head(5).to_dict(orient="records"),
        "top_suppliers": supplier.head(5).to_dict(orient="records"),
        "sample_rows": cleaned.head(12).astype(str).to_dict(orient="records"),
        "export_version": export_version,
    }
    schema = {
        "name": "finance_bp_insights",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "executive_summary": {"type": "string"},
                "key_findings": {"type": "array", "items": {"type": "string"}},
                "risk_alerts": {"type": "array", "items": {"type": "string"}},
                "recommended_actions": {"type": "array", "items": {"type": "string"}},
                "sheet_rows": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "模块": {"type": "string"},
                            "主题": {"type": "string"},
                            "结论": {"type": "string"},
                            "建议动作": {"type": "string"},
                            "优先级": {"type": "string"},
                        },
                        "required": ["模块", "主题", "结论", "建议动作", "优先级"],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["executive_summary", "key_findings", "risk_alerts", "recommended_actions", "sheet_rows"],
            "additionalProperties": False,
        },
    }
    prompt = (
        "你是制造业/消费电子背景下的高级财务BP。请基于财务流水、月度趋势、客户和供应商集中度、异常情况，输出老板可看、BP可执行的经营分析。"
        "请尽量贴近大型制造企业财务BP常见关注：预算执行、费用归口、产品/项目盈利测算、客户集中度、经营现金流质量、营运资金、内外部报送一致性。"
        "风格要求：务实、可落地、避免空话。结论要围绕回款、费用结构、集中度、异常数据治理和经营动作。"
        "口径要求：这里只有流水与净额，不要把净额误写成净利润；没有利润表时统一使用“净额”“净流入/净流出”“收支结余”等表述。"
        f"\n输入数据: {json.dumps(prompt_payload, ensure_ascii=False)}"
    )
    response = _chat_json(prompt, schema, requested_model)
    if not response:
        return fallback, False, resolve_model(requested_model)
    return response, True, resolve_model(requested_model)


def heuristic_bp_insights(
    cleaned: pd.DataFrame,
    anomalies: pd.DataFrame,
    metrics: dict[str, Any],
    monthly: pd.DataFrame,
    customer: pd.DataFrame,
    supplier: pd.DataFrame,
    export_version: str,
) -> dict[str, Any]:
    total_income = float(metrics.get("total_income", 0))
    total_expense = float(metrics.get("total_expense", 0))
    net_amount = float(metrics.get("net_amount", 0))
    top_customer_ratio = float(customer.head(1)["占比"].iloc[0]) if not customer.empty and "占比" in customer.columns else 0
    top_supplier_ratio = float(supplier.head(1)["占比"].iloc[0]) if not supplier.empty and "占比" in supplier.columns else 0
    anomaly_ratio = len(anomalies) / len(cleaned) if len(cleaned) else 0
    monthly_sorted = monthly[monthly["月份"].astype(str) != ""].copy() if not monthly.empty else monthly
    trend_desc = "月度趋势较平稳"
    if len(monthly_sorted) >= 2:
        first_net = float(monthly_sorted["净额"].iloc[0])
        last_net = float(monthly_sorted["净额"].iloc[-1])
        if last_net > first_net:
            trend_desc = "月度净额呈改善趋势"
        elif last_net < first_net:
            trend_desc = "月度净额呈走弱趋势"

    key_findings = [
        f"本期净额为 {net_amount:,.2f} 元，收入 {total_income:,.2f} 元、支出 {total_expense:,.2f} 元。",
        trend_desc,
        f"头部客户收入占比约 {top_customer_ratio:.1%}，需关注收入集中度。" if top_customer_ratio else "客户分布较分散。",
    ]
    risk_alerts = [
        f"异常数据占比约 {anomaly_ratio:.1%}，建议先完成基础口径治理。" if anomaly_ratio else "基础数据质量整体可控。",
        f"头部供应商支出占比约 {top_supplier_ratio:.1%}，建议核查采购议价与预算归口。" if top_supplier_ratio else "供应商支出分布较分散。",
    ]
    recommended_actions = [
        "对重复订单号、缺失日期、异常金额建立月结前必清单。",
        "将客户/部门/月度趋势纳入固定经营复盘模板。",
        "对 Top 客户建立回款节奏跟踪，对 Top 支出项建立预算-执行偏差复核。",
    ]
    sheet_rows = [
        {"模块": "经营概览", "主题": "收入与净额", "结论": key_findings[0], "建议动作": "复盘收入确认与费用归类口径", "优先级": "高"},
        {"模块": "趋势判断", "主题": "月度趋势", "结论": trend_desc, "建议动作": "补充月度波动原因备注", "优先级": "中"},
        {"模块": "集中度", "主题": "客户集中度", "结论": key_findings[2], "建议动作": "跟踪头部客户续约与回款", "优先级": "高"},
        {"模块": "风险提示", "主题": "异常数据", "结论": risk_alerts[0], "建议动作": "建立异常闭环责任人", "优先级": "高"},
        {"模块": "费用管控", "主题": "供应商结构", "结论": risk_alerts[1], "建议动作": "复核供应商成本合理性", "优先级": "中"},
    ]
    if export_version == "boss":
        recommended_actions.insert(0, "把核心经营结论控制在 3 条，突出现金流、收入质量和费用效率。")
    return {
        "executive_summary": "；".join(key_findings[:2]) + "。" + risk_alerts[0],
        "key_findings": key_findings,
        "risk_alerts": risk_alerts,
        "recommended_actions": recommended_actions,
        "sheet_rows": sheet_rows,
    }


def _chat_json(prompt: str, schema: dict[str, Any], requested_model: str | None = None) -> dict[str, Any] | None:
    body = {
        "model": resolve_model(requested_model),
        "messages": [
            {"role": "system", "content": "You are a precise finance data copilot. Always return valid JSON that matches the schema."},
            {"role": "user", "content": prompt},
        ],
        "response_format": {"type": "json_schema", "json_schema": schema},
    }
    data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        OPENROUTER_BASE_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": OPENROUTER_SITE_URL,
            "X-Title": OPENROUTER_APP_NAME,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
        return None

    try:
        content = payload["choices"][0]["message"]["content"]
        if isinstance(content, list):
            content = "".join(item.get("text", "") for item in content if isinstance(item, dict))
        return json.loads(content)
    except (KeyError, TypeError, json.JSONDecodeError):
        return None
