from __future__ import annotations

import pandas as pd


def check_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    checked = df.copy()
    duplicate_orders = checked["订单号"].astype(str).str.strip()
    duplicated_mask = duplicate_orders.ne("") & duplicate_orders.duplicated(keep=False)
    reasons: list[str] = []

    amount_q99 = checked["金额"].dropna().abs().quantile(0.99) if checked["金额"].notna().any() else 0
    amount_threshold = max(float(amount_q99 or 0) * 2, 1_000_000)

    for index, row in checked.iterrows():
        row_reasons: list[str] = []
        if pd.isna(row["金额"]):
            row_reasons.append("金额为空或无法解析")
        if pd.isna(row["日期"]):
            row_reasons.append("日期为空或格式异常")
        if duplicated_mask.loc[index]:
            row_reasons.append("重复订单号/流水号")
        if row["收支方向"] == "收入" and not str(row["客户"]).strip():
            row_reasons.append("收入记录客户为空")
        if row["收支方向"] == "支出" and not str(row["供应商"]).strip():
            row_reasons.append("支出记录供应商为空")
        if row["收支方向"] == "未知":
            row_reasons.append("收入支出方向异常")
        if pd.notna(row["金额"]) and (row["金额"] < 0 or abs(row["金额"]) > amount_threshold):
            row_reasons.append("明显异常金额")
        if str(row.get("发票状态", "")).strip() and str(row["发票状态"]).strip() not in {"已开票", "未开票", "已收票", "未收票", "无需发票"}:
            row_reasons.append("无法识别的字段值: 发票状态")
        reasons.append("；".join(row_reasons))

    checked["异常原因"] = reasons
    return checked[checked["异常原因"].astype(bool)].copy()


def anomaly_summary(anomalies: pd.DataFrame) -> dict[str, int]:
    counter: dict[str, int] = {}
    if anomalies.empty:
        return {"异常总数": 0}
    for reason_text in anomalies["异常原因"].astype(str):
        for reason in reason_text.split("；"):
            if reason:
                counter[reason] = counter.get(reason, 0) + 1
    counter["异常总数"] = int(len(anomalies))
    return counter
