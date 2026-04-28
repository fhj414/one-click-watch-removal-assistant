from __future__ import annotations

from typing import Any

import pandas as pd


SHEET_NAME_MAP = {
    "cleaned": "原始清洗表",
    "income": "收入明细表",
    "expense": "支出明细表",
    "monthly": "月度汇总表",
    "department": "部门汇总表",
    "customer": "客户汇总表",
    "supplier": "供应商汇总表",
    "anomalies": "异常数据表",
    "summary": "管理摘要表",
    "bp_insights": "财务BP洞察表",
    "customer_concentration": "客户集中度表",
    "expense_structure": "费用结构表",
    "department_performance": "部门经营分析表",
    "project_profitability": "项目盈利测算表",
    "customer_risk": "客户回款风险表",
    "working_capital": "营运资金关注表",
    "product_line": "产品线经营表",
    "budget_variance": "预算执行偏差表",
    "expense_owner": "费用归口分析表",
    "supplier_type": "供应商类型分析表",
    "region": "区域经营表",
    "collection_status": "回款状态跟踪表",
    "bp_field_guide": "BP字段应用建议表",
}


def build_report_tables(cleaned: pd.DataFrame, anomalies: pd.DataFrame, bp_sheet: pd.DataFrame | None = None) -> dict[str, pd.DataFrame]:
    income = cleaned[cleaned["收支方向"] == "收入"].copy()
    expense = cleaned[cleaned["收支方向"] == "支出"].copy()

    monthly = _pivot(cleaned, ["月份"])
    department = _pivot(cleaned, ["部门"])
    customer = _entity_summary(income, "客户", "收入金额")
    supplier = _entity_summary(expense, "供应商", "支出金额")
    customer_concentration = _concentration(customer, "客户", "收入金额")
    expense_structure = _expense_structure(expense)
    department_performance = _department_performance(cleaned)
    project_profitability = _project_profitability(cleaned)
    customer_risk = _customer_risk(cleaned, anomalies)
    working_capital = _working_capital_watch(cleaned, anomalies, customer, supplier)
    product_line = _dimension_performance(cleaned, "产品线", "产品线经营表")
    budget_variance = _budget_variance(cleaned)
    expense_owner = _expense_owner_analysis(expense)
    supplier_type = _supplier_type_analysis(expense)
    region = _dimension_performance(cleaned, "区域", "区域经营表")
    collection_status = _collection_status_watch(cleaned)
    bp_field_guide = _bp_field_guide(cleaned)
    summary = _management_summary(cleaned, income, expense, customer, supplier, monthly, anomalies)

    tables = {
        "原始清洗表": cleaned,
        "收入明细表": income,
        "支出明细表": expense,
        "月度汇总表": monthly,
        "部门汇总表": department,
        "客户汇总表": customer,
        "供应商汇总表": supplier,
        "客户集中度表": customer_concentration,
        "费用结构表": expense_structure,
        "部门经营分析表": department_performance,
        "项目盈利测算表": project_profitability,
        "客户回款风险表": customer_risk,
        "营运资金关注表": working_capital,
        "产品线经营表": product_line,
        "预算执行偏差表": budget_variance,
        "费用归口分析表": expense_owner,
        "供应商类型分析表": supplier_type,
        "区域经营表": region,
        "回款状态跟踪表": collection_status,
        "BP字段应用建议表": bp_field_guide,
        "异常数据表": anomalies,
        "管理摘要表": summary,
    }
    if bp_sheet is not None and not bp_sheet.empty:
        tables["财务BP洞察表"] = bp_sheet
    return tables


def _pivot(df: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=by + ["收入", "支出", "净额", "记录数"])
    grouped = (
        df.assign(
            收入=df.apply(lambda row: row["金额"] if row["收支方向"] == "收入" and pd.notna(row["金额"]) else 0, axis=1),
            支出=df.apply(lambda row: row["金额"] if row["收支方向"] == "支出" and pd.notna(row["金额"]) else 0, axis=1),
        )
        .groupby(by, dropna=False)
        .agg(收入=("收入", "sum"), 支出=("支出", "sum"), 净额=("净额", "sum"), 记录数=("原始行号", "count"))
        .reset_index()
    )
    return grouped.sort_values(by=by)


def _entity_summary(df: pd.DataFrame, entity_col: str, amount_name: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=[entity_col, amount_name, "记录数", "占比"])
    total = df["金额"].fillna(0).sum()
    result = (
        df.groupby(entity_col, dropna=False)
        .agg(**{amount_name: ("金额", "sum"), "记录数": ("原始行号", "count")})
        .reset_index()
        .sort_values(amount_name, ascending=False)
    )
    result["占比"] = result[amount_name] / total if total else 0
    return result


def _concentration(df: pd.DataFrame, entity_col: str, amount_name: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=[entity_col, amount_name, "占比", "累计占比", "分层"])
    result = df[[entity_col, amount_name, "占比"]].copy()
    result["累计占比"] = result["占比"].cumsum()
    result["分层"] = [
        "核心贡献" if index == 0 or cumulative <= 0.6 else ("重点关注" if cumulative <= 0.85 else "尾部")
        for index, cumulative in enumerate(result["累计占比"])
    ]
    return result


def _expense_structure(expense: pd.DataFrame) -> pd.DataFrame:
    if expense.empty:
        return pd.DataFrame(columns=["项目", "支出金额", "记录数", "占比"])
    total = expense["金额"].fillna(0).sum()
    result = (
        expense.groupby("项目", dropna=False)
        .agg(支出金额=("金额", "sum"), 记录数=("原始行号", "count"))
        .reset_index()
        .sort_values("支出金额", ascending=False)
    )
    result["占比"] = result["支出金额"] / total if total else 0
    return result


def _department_performance(cleaned: pd.DataFrame) -> pd.DataFrame:
    if cleaned.empty:
        return pd.DataFrame(columns=["部门", "收入", "支出", "净额", "收入占比", "支出占比", "费用率", "记录数"])
    result = (
        cleaned.assign(
            收入=cleaned.apply(lambda row: row["金额"] if row["收支方向"] == "收入" and pd.notna(row["金额"]) else 0, axis=1),
            支出=cleaned.apply(lambda row: abs(row["金额"]) if row["收支方向"] == "支出" and pd.notna(row["金额"]) else 0, axis=1),
        )
        .groupby("部门", dropna=False)
        .agg(收入=("收入", "sum"), 支出=("支出", "sum"), 净额=("净额", "sum"), 记录数=("原始行号", "count"))
        .reset_index()
    )
    total_income = result["收入"].sum()
    total_expense = result["支出"].sum()
    result["收入占比"] = result["收入"] / total_income if total_income else 0
    result["支出占比"] = result["支出"] / total_expense if total_expense else 0
    result["费用率"] = result.apply(lambda row: row["支出"] / row["收入"] if row["收入"] else 0, axis=1)
    return result.sort_values("净额", ascending=False)


def _project_profitability(cleaned: pd.DataFrame) -> pd.DataFrame:
    if cleaned.empty:
        return pd.DataFrame(columns=["项目", "收入", "支出", "净额", "毛利率代理", "记录数", "经营判断"])
    result = (
        cleaned.assign(
            收入=cleaned.apply(lambda row: row["金额"] if row["收支方向"] == "收入" and pd.notna(row["金额"]) else 0, axis=1),
            支出=cleaned.apply(lambda row: abs(row["金额"]) if row["收支方向"] == "支出" and pd.notna(row["金额"]) else 0, axis=1),
        )
        .groupby("项目", dropna=False)
        .agg(收入=("收入", "sum"), 支出=("支出", "sum"), 净额=("净额", "sum"), 记录数=("原始行号", "count"))
        .reset_index()
    )
    result["毛利率代理"] = result.apply(lambda row: row["净额"] / row["收入"] if row["收入"] else 0, axis=1)
    result["经营判断"] = result.apply(_project_commentary, axis=1)
    return result.sort_values("净额", ascending=False)


def _project_commentary(row: pd.Series) -> str:
    if row["收入"] == 0 and row["支出"] > 0:
        return "成本先行，需跟踪收入确认"
    if row["收入"] > 0 and row["支出"] == 0:
        return "高净额项目，需确认成本是否完整归集"
    if row["毛利率代理"] < 0:
        return "净流出项目，关注费用归集与产出"
    if row["毛利率代理"] < 0.2:
        return "薄利项目，建议复盘资源投入"
    return "表现正常，可持续跟踪"


def _customer_risk(cleaned: pd.DataFrame, anomalies: pd.DataFrame) -> pd.DataFrame:
    income = cleaned[cleaned["收支方向"] == "收入"].copy()
    if income.empty:
        return pd.DataFrame(columns=["客户", "收入金额", "订单数", "最近月份", "异常笔数", "集中度", "风险等级", "建议动作"])
    anomaly_orders = set(anomalies["订单号"].astype(str)) if not anomalies.empty else set()
    result = (
        income.groupby("客户", dropna=False)
        .agg(收入金额=("金额", "sum"), 订单数=("订单号", "count"), 最近月份=("月份", "max"))
        .reset_index()
        .sort_values("收入金额", ascending=False)
    )
    total_income = result["收入金额"].sum()
    result["集中度"] = result["收入金额"] / total_income if total_income else 0
    result["异常笔数"] = result["客户"].apply(
        lambda customer: int(
            income[(income["客户"] == customer) & (income["订单号"].astype(str).isin(anomaly_orders))]["订单号"].count()
        )
    )
    result["风险等级"] = result.apply(_customer_risk_level, axis=1)
    result["建议动作"] = result["风险等级"].map(
        {
            "高": "建立专项回款与合同核对清单，月度复盘",
            "中": "跟踪订单履约与开票进度",
            "低": "纳入常规客户经营跟踪",
        }
    )
    return result


def _customer_risk_level(row: pd.Series) -> str:
    if row["集中度"] >= 0.5 or row["异常笔数"] >= 1:
        return "高"
    if row["集中度"] >= 0.2:
        return "中"
    return "低"


def _working_capital_watch(
    cleaned: pd.DataFrame, anomalies: pd.DataFrame, customer: pd.DataFrame, supplier: pd.DataFrame
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    total_records = len(cleaned)
    anomaly_rate = len(anomalies) / total_records if total_records else 0
    top_customer_ratio = float(customer["占比"].iloc[0]) if not customer.empty else 0
    top_supplier_ratio = float(supplier["占比"].iloc[0]) if not supplier.empty else 0
    missing_date_count = int((cleaned["日期"].isna()).sum())
    duplicate_order_count = int(cleaned["订单号"].astype(str).duplicated(keep=False).sum())

    rows.append(
        {
            "关注项": "数据质量",
            "指标": "异常数据占比",
            "数值": anomaly_rate,
            "状态": "高关注" if anomaly_rate >= 0.1 else "可控",
            "说明": "异常占比高会直接影响经营分析、滚动预测和内外部报送口径",
        }
    )
    rows.append(
        {
            "关注项": "客户集中度",
            "指标": "头部客户收入占比",
            "数值": top_customer_ratio,
            "状态": "高关注" if top_customer_ratio >= 0.5 else "可控",
            "说明": "客户集中度高时需要同步关注回款节奏与合同执行",
        }
    )
    rows.append(
        {
            "关注项": "供应商集中度",
            "指标": "头部供应商支出占比",
            "数值": top_supplier_ratio,
            "状态": "重点跟踪" if top_supplier_ratio >= 0.35 else "可控",
            "说明": "供应商集中可能影响采购议价、费用归口和预算刚性",
        }
    )
    rows.append(
        {
            "关注项": "单据口径",
            "指标": "缺失日期笔数",
            "数值": missing_date_count,
            "状态": "高关注" if missing_date_count > 0 else "可控",
            "说明": "缺失日期会影响月结、预算执行和滚动预测归属",
        }
    )
    rows.append(
        {
            "关注项": "订单治理",
            "指标": "重复订单号笔数",
            "数值": duplicate_order_count,
            "状态": "高关注" if duplicate_order_count > 0 else "可控",
            "说明": "重复单据需先清理，再用于产品盈利测算和经营报表",
        }
    )
    return pd.DataFrame(rows)


def _dimension_performance(cleaned: pd.DataFrame, dimension: str, sheet_name: str) -> pd.DataFrame:
    columns = [dimension, "收入", "支出", "净额", "收入占比", "支出占比", "费用率", "记录数", "BP关注"]
    if cleaned.empty or not _has_value(cleaned, dimension):
        return pd.DataFrame(columns=columns)
    result = (
        cleaned.assign(
            收入=cleaned.apply(lambda row: row["金额"] if row["收支方向"] == "收入" and pd.notna(row["金额"]) else 0, axis=1),
            支出=cleaned.apply(lambda row: abs(row["金额"]) if row["收支方向"] == "支出" and pd.notna(row["金额"]) else 0, axis=1),
        )
        .groupby(dimension, dropna=False)
        .agg(收入=("收入", "sum"), 支出=("支出", "sum"), 净额=("净额", "sum"), 记录数=("原始行号", "count"))
        .reset_index()
    )
    total_income = result["收入"].sum()
    total_expense = result["支出"].sum()
    result["收入占比"] = result["收入"] / total_income if total_income else 0
    result["支出占比"] = result["支出"] / total_expense if total_expense else 0
    result["费用率"] = result.apply(lambda row: row["支出"] / row["收入"] if row["收入"] else 0, axis=1)
    result["BP关注"] = result.apply(lambda row: _dimension_commentary(row, dimension), axis=1)
    return result[columns].sort_values("净额", ascending=False)


def _budget_variance(cleaned: pd.DataFrame) -> pd.DataFrame:
    columns = ["预算版本", "部门", "项目", "预算金额", "实际净额", "偏差金额", "达成率", "记录数", "BP关注"]
    if cleaned.empty or not _has_value(cleaned, "预算金额"):
        return pd.DataFrame(columns=columns)
    group_cols = [column for column in ["预算版本", "部门", "项目"] if _has_value(cleaned, column)] or ["预算版本"]
    result = (
        cleaned.groupby(group_cols, dropna=False)
        .agg(预算金额=("预算金额", "sum"), 实际净额=("净额", "sum"), 记录数=("原始行号", "count"))
        .reset_index()
    )
    result["偏差金额"] = result["实际净额"] - result["预算金额"]
    result["达成率"] = result.apply(lambda row: row["实际净额"] / row["预算金额"] if row["预算金额"] else 0, axis=1)
    result["BP关注"] = result.apply(_budget_commentary, axis=1)
    for column in columns:
        if column not in result.columns:
            result[column] = ""
    return result[columns].sort_values("偏差金额")


def _expense_owner_analysis(expense: pd.DataFrame) -> pd.DataFrame:
    columns = ["费用归口", "部门", "项目", "支出金额", "记录数", "占比", "BP关注"]
    if expense.empty or not _has_value(expense, "费用归口"):
        return pd.DataFrame(columns=columns)
    group_cols = [column for column in ["费用归口", "部门", "项目"] if _has_value(expense, column)] or ["费用归口"]
    result = expense.groupby(group_cols, dropna=False).agg(支出金额=("金额", "sum"), 记录数=("原始行号", "count")).reset_index()
    total = result["支出金额"].fillna(0).sum()
    result["占比"] = result["支出金额"] / total if total else 0
    result["BP关注"] = result["占比"].apply(lambda value: "高占比费用，建议核查预算归口和节超原因" if value >= 0.2 else "常规跟踪")
    for column in columns:
        if column not in result.columns:
            result[column] = ""
    return result[columns].sort_values("支出金额", ascending=False)


def _supplier_type_analysis(expense: pd.DataFrame) -> pd.DataFrame:
    columns = ["供应商类型", "支出金额", "供应商数", "记录数", "占比", "BP关注"]
    if expense.empty or not _has_value(expense, "供应商类型"):
        return pd.DataFrame(columns=columns)
    result = (
        expense.groupby("供应商类型", dropna=False)
        .agg(支出金额=("金额", "sum"), 供应商数=("供应商", "nunique"), 记录数=("原始行号", "count"))
        .reset_index()
    )
    total = result["支出金额"].fillna(0).sum()
    result["占比"] = result["支出金额"] / total if total else 0
    result["BP关注"] = result["占比"].apply(lambda value: "供应商类型支出集中，建议结合采购策略复盘" if value >= 0.35 else "常规跟踪")
    return result[columns].sort_values("支出金额", ascending=False)


def _collection_status_watch(cleaned: pd.DataFrame) -> pd.DataFrame:
    columns = ["回款状态", "客户", "收入金额", "订单数", "最近回款日期", "最近到期日期", "BP关注"]
    income = cleaned[cleaned["收支方向"] == "收入"].copy()
    if income.empty or not (_has_value(income, "回款状态") or _has_value(income, "回款日期") or _has_value(income, "到期日期")):
        return pd.DataFrame(columns=columns)
    group_cols = [column for column in ["回款状态", "客户"] if _has_value(income, column)] or ["客户"]
    result = (
        income.groupby(group_cols, dropna=False)
        .agg(收入金额=("金额", "sum"), 订单数=("订单号", "count"), 最近回款日期=("回款日期", "max"), 最近到期日期=("到期日期", "max"))
        .reset_index()
    )
    result["BP关注"] = result.apply(_collection_commentary, axis=1)
    for column in columns:
        if column not in result.columns:
            result[column] = ""
    return result[columns].sort_values("收入金额", ascending=False)


def _bp_field_guide(cleaned: pd.DataFrame) -> pd.DataFrame:
    field_actions = {
        "业务单元": "用于区分 BU/BG 经营贡献，适合经营会按组织口径复盘。",
        "产品线": "用于产品线收入、费用、净额和资源投入产出分析。",
        "产品型号": "用于 SKU/机型盈利测算和异常波动追踪。",
        "区域": "用于国内/海外、区域市场收入质量和费用效率分析。",
        "预算版本": "用于预算、Forecast、实际数之间的口径对齐。",
        "预算金额": "用于预算执行偏差、达成率和节超说明。",
        "费用归口": "用于费用科目归属、预算责任人和节超治理。",
        "客户账期": "用于应收风险、回款周期和现金流预测。",
        "回款状态": "用于回款风险分层和经营现金流跟踪。",
        "供应商类型": "用于采购结构、供应商集中度和成本策略复盘。",
    }
    rows = []
    for field, action in field_actions.items():
        rows.append(
            {
                "字段": field,
                "是否识别": "是" if _has_value(cleaned, field) else "否",
                "BP用途": action,
                "建议动作": "纳入动态报表" if _has_value(cleaned, field) else "建议在源表补充该字段",
            }
        )
    return pd.DataFrame(rows)


def _has_value(df: pd.DataFrame, column: str) -> bool:
    if column not in df.columns or df.empty:
        return False
    if pd.api.types.is_datetime64_any_dtype(df[column]) or pd.api.types.is_numeric_dtype(df[column]):
        return bool(df[column].notna().any())
    values = df[column].fillna("").astype(str).str.strip()
    return bool(values[values != ""].any())


def _dimension_commentary(row: pd.Series, dimension: str) -> str:
    if row["收入"] == 0 and row["支出"] > 0:
        return f"{dimension}仅有支出，需核查收入确认或费用归集"
    if row["费用率"] >= 0.5 and row["收入"] > 0:
        return f"{dimension}费用率偏高，建议复盘资源投入效率"
    if row["收入占比"] >= 0.4:
        return f"{dimension}收入贡献集中，需关注持续性和回款质量"
    return "常规跟踪"


def _budget_commentary(row: pd.Series) -> str:
    if row["预算金额"] == 0:
        return "缺少预算金额，无法判断达成率"
    if row["达成率"] < 0.8:
        return "低于预算，需解释收入或费用执行偏差"
    if row["达成率"] > 1.2:
        return "高于预算，需确认一次性因素或预算口径"
    return "执行进度相对正常"


def _collection_commentary(row: pd.Series) -> str:
    status = str(row.get("回款状态", ""))
    if any(keyword in status for keyword in ["逾期", "未回", "未收", "风险"]):
        return "回款风险较高，建议建立专项跟踪清单"
    if row.get("最近到期日期") and not row.get("最近回款日期"):
        return "存在到期信息，建议核对实际回款状态"
    return "常规跟踪"


def _management_summary(
    cleaned: pd.DataFrame,
    income: pd.DataFrame,
    expense: pd.DataFrame,
    customer: pd.DataFrame,
    supplier: pd.DataFrame,
    monthly: pd.DataFrame,
    anomalies: pd.DataFrame,
) -> pd.DataFrame:
    total_income = float(income["金额"].fillna(0).sum())
    total_expense = float(expense["金额"].fillna(0).sum())
    net = total_income - total_expense
    rows: list[dict[str, Any]] = [
        {"模块": "关键指标", "项目": "总收入", "数值": total_income, "说明": "收入明细表金额合计"},
        {"模块": "关键指标", "项目": "总支出", "数值": total_expense, "说明": "支出明细表金额合计"},
        {"模块": "关键指标", "项目": "净额", "数值": net, "说明": "总收入 - 总支出"},
        {"模块": "关键指标", "项目": "异常记录数", "数值": int(len(anomalies)), "说明": "异常数据表行数"},
    ]

    for _, row in customer.head(5).iterrows():
        rows.append({"模块": "Top5 客户", "项目": row.get("客户", ""), "数值": row.get("收入金额", 0), "说明": "按收入排序"})
    for _, row in supplier.head(5).iterrows():
        rows.append({"模块": "Top5 支出项", "项目": row.get("供应商", ""), "数值": row.get("支出金额", 0), "说明": "按支出排序"})
    for _, row in monthly.iterrows():
        rows.append({"模块": "月度趋势", "项目": row.get("月份", ""), "数值": row.get("净额", 0), "说明": "月度净额"})

    return pd.DataFrame(rows)


def build_metrics(tables: dict[str, pd.DataFrame]) -> dict[str, Any]:
    summary = tables["管理摘要表"]
    metrics = {str(row["项目"]): row["数值"] for _, row in summary[summary["模块"] == "关键指标"].iterrows()}
    return {
        "total_income": float(metrics.get("总收入", 0)),
        "total_expense": float(metrics.get("总支出", 0)),
        "net_amount": float(metrics.get("净额", 0)),
        "anomaly_count": int(metrics.get("异常记录数", 0)),
    }


def boss_summary_text(metrics: dict[str, Any], anomaly_count: int) -> str:
    net = metrics.get("net_amount", 0)
    tone = "经营净流入为正，整体现金表现较稳健" if net >= 0 else "经营净流出，需要重点关注支出节奏和回款安排"
    return (
        f"本期总收入 {metrics.get('total_income', 0):,.2f} 元，"
        f"总支出 {metrics.get('total_expense', 0):,.2f} 元，"
        f"净额 {net:,.2f} 元。{tone}。"
        f"系统识别到 {anomaly_count} 条异常记录，建议优先核对金额、日期、重复单号和往来主体。"
    )
