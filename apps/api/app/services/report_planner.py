from __future__ import annotations

from typing import Any

import pandas as pd


CORE_SHEETS = ["原始清洗表", "异常数据表", "管理摘要表"]
DYNAMIC_BP_SHEETS = {
    "产品线经营表",
    "预算执行偏差表",
    "费用归口分析表",
    "供应商类型分析表",
    "区域经营表",
    "回款状态跟踪表",
    "BP字段应用建议表",
}


def build_report_plan(cleaned: pd.DataFrame, anomalies: pd.DataFrame) -> dict[str, Any]:
    total_rows = int(len(cleaned))
    income_count = int((cleaned["收支方向"] == "收入").sum()) if not cleaned.empty else 0
    expense_count = int((cleaned["收支方向"] == "支出").sum()) if not cleaned.empty else 0
    has_income = income_count > 0
    has_expense = expense_count > 0
    has_customer = _has_real_values(cleaned, "客户")
    has_supplier = _has_real_values(cleaned, "供应商")
    has_department = _has_real_values(cleaned, "部门")
    has_project = _has_real_values(cleaned, "项目")
    has_month = _has_real_values(cleaned, "月份")
    has_product_line = _has_real_values(cleaned, "产品线")
    has_budget = _has_real_values(cleaned, "预算金额")
    has_expense_owner = _has_real_values(cleaned, "费用归口")
    has_supplier_type = _has_real_values(cleaned, "供应商类型")
    has_region = _has_real_values(cleaned, "区域")
    has_collection_status = any(_has_real_values(cleaned, column) for column in ["回款状态", "回款日期", "到期日期", "客户账期"])
    anomaly_count = int(len(anomalies))

    recommended: list[str] = ["原始清洗表"]
    focus: list[str] = []
    reasons: list[str] = []
    missing_fields: list[str] = []

    data_type = _classify_data_type(has_income, has_expense, has_customer, has_supplier, has_project)

    if has_income:
        recommended.extend(["收入明细表", "客户汇总表", "客户集中度表", "客户回款风险表"])
        focus.extend(["客户收入贡献", "客户集中度", "回款风险"])
        reasons.append("检测到收入记录，优先输出客户贡献、集中度和回款风险相关表。")
    else:
        missing_fields.append("收入方向或收入金额")

    if has_expense:
        recommended.extend(["支出明细表", "供应商汇总表", "费用结构表"])
        focus.extend(["费用结构", "供应商集中度", "预算归口"])
        reasons.append("检测到支出记录，优先输出费用结构和供应商集中度相关表。")
    else:
        missing_fields.append("支出方向或支出金额")

    if has_month:
        recommended.append("月度汇总表")
        focus.append("月度趋势")
    else:
        missing_fields.append("日期/月份")

    if has_department:
        recommended.extend(["部门汇总表", "部门经营分析表"])
        focus.extend(["部门贡献", "费用率"])
    else:
        missing_fields.append("部门")

    if has_project:
        recommended.append("项目盈利测算表")
        focus.append("项目投入产出")
    else:
        missing_fields.append("项目/产品线")

    if has_product_line:
        recommended.append("产品线经营表")
        focus.extend(["产品线贡献", "产品组合"])
        reasons.append("检测到产品线/型号字段，增加产品维度经营贡献分析。")

    if has_budget:
        recommended.append("预算执行偏差表")
        focus.extend(["预算执行", "Forecast偏差"])
        reasons.append("检测到预算字段，增加预算执行偏差和达成率分析。")
    else:
        missing_fields.append("预算金额")

    if has_expense_owner:
        recommended.append("费用归口分析表")
        focus.extend(["费用归口", "节超治理"])

    if has_supplier_type:
        recommended.append("供应商类型分析表")
        focus.append("采购结构")

    if has_region:
        recommended.append("区域经营表")
        focus.append("区域经营贡献")

    if has_collection_status:
        recommended.append("回款状态跟踪表")
        focus.extend(["回款状态", "现金流风险"])
    else:
        missing_fields.append("回款状态/回款日期")

    if has_income or has_expense:
        recommended.append("营运资金关注表")
        focus.append("营运资金")

    if anomaly_count:
        focus.append("数据治理")
        reasons.append(f"检测到 {anomaly_count} 条异常，保留异常数据表用于月结前清理。")

    recommended.extend(["异常数据表", "管理摘要表", "财务BP洞察表", "BP字段应用建议表"])
    return {
        "data_type": data_type,
        "data_type_label": _data_type_label(data_type),
        "recommended_sheets": _unique(recommended),
        "bp_focus": _unique(focus),
        "missing_fields": _unique(missing_fields),
        "reasons": reasons or ["数据字段较通用，按经营流水基础分析模板输出。"],
        "row_count": total_rows,
        "income_count": income_count,
        "expense_count": expense_count,
        "anomaly_count": anomaly_count,
    }


def apply_report_plan(tables: dict[str, pd.DataFrame], plan: dict[str, Any], selected_sheet_names: set[str] | None = None) -> dict[str, pd.DataFrame]:
    planned_names = set(plan.get("recommended_sheets") or [])
    if selected_sheet_names:
        planned_names = (planned_names & selected_sheet_names) | (planned_names & DYNAMIC_BP_SHEETS)
    keep_names = planned_names | {name for name in CORE_SHEETS if name in tables}
    return {name: table for name, table in tables.items() if name in keep_names}


def _has_real_values(df: pd.DataFrame, column: str) -> bool:
    if column not in df.columns or df.empty:
        return False
    values = df[column].astype(str).str.strip()
    return bool(values[(values != "") & (values.str.lower() != "nan")].any())


def _classify_data_type(has_income: bool, has_expense: bool, has_customer: bool, has_supplier: bool, has_project: bool) -> str:
    if has_income and has_expense and has_project:
        return "project_business"
    if has_income and has_customer and not has_expense:
        return "sales_collection"
    if has_expense and has_supplier and not has_income:
        return "expense_procurement"
    if has_income and has_expense:
        return "mixed_cashflow"
    return "general_ledger"


def _data_type_label(data_type: str) -> str:
    labels = {
        "project_business": "项目/产品经营分析",
        "sales_collection": "收入与回款分析",
        "expense_procurement": "费用与采购分析",
        "mixed_cashflow": "经营流水综合分析",
        "general_ledger": "通用财务台账分析",
    }
    return labels.get(data_type, "通用财务台账分析")


def _unique(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result
