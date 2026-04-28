# API 设计文档

默认后端地址：`http://127.0.0.1:8000`

## POST /api/uploads/init

初始化上传策略。

请求：

```json
{
  "filename": "raw.xlsx",
  "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
}
```

响应（启用 R2 时）：

```json
{
  "storage_mode": "r2",
  "upload_url": "https://...",
  "object_key": "uploads/raw-uuid.xlsx",
  "expires_in": 3600
}
```

响应（未启用 R2 时）：

```json
{
  "storage_mode": "local"
}
```

## POST /api/uploads/complete

当文件已经直传到 R2 后，通知后端拉取样本并完成字段识别。

请求：

```json
{
  "object_key": "uploads/raw-uuid.xlsx",
  "filename": "raw.xlsx",
  "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
}
```

## POST /api/uploads

上传 Excel 或 CSV 文件。

请求：`multipart/form-data`

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| file | file | 是 | `.xlsx`、`.xls`、`.csv` |

响应：

```json
{
  "upload_id": "uuid",
  "filename": "raw.csv",
  "columns": ["日期", "金额"],
  "sample_rows": [{ "日期": "2026-01-01", "金额": "1000" }],
  "suggested_mapping": { "日期": "date", "金额": "amount" },
  "storage_mode": "local"
}
```

## GET /api/uploads/{upload_id}/mapping

获取某个上传文件的字段识别结果和样本。

## GET /api/templates

获取已保存的字段模板。

## POST /api/templates

保存字段映射模板。

请求：

```json
{
  "name": "支付宝流水模板",
  "mapping": { "交易时间": "date", "实收金额": "amount" },
  "source_columns": ["交易时间", "实收金额"]
}
```

## POST /api/reports/generate

根据上传文件、字段映射和生成配置创建报表。

请求：

```json
{
  "upload_id": "uuid",
  "mapping": { "日期": "date", "金额": "amount" },
  "config": {
    "sheets": ["cleaned", "income", "expense", "monthly", "department", "customer", "supplier", "anomalies", "summary"],
    "enable_anomaly_check": true,
    "enable_formulas": true,
    "enable_summary": true,
    "export_version": "finance"
  }
}
```

响应：

```json
{
  "report_id": "uuid",
  "status": "succeeded",
  "metrics": {
    "total_income": 10000,
    "total_expense": 3000,
    "net_amount": 7000
  },
  "preview": {
    "原始清洗表": [{ "日期": "2026-01-01" }]
  },
  "download_url": "/api/reports/uuid/download",
  "report_plan": {
    "data_type_label": "经营流水综合分析",
    "recommended_sheets": ["原始清洗表", "客户汇总表", "费用结构表"],
    "bp_focus": ["客户集中度", "费用结构"],
    "missing_fields": ["预算金额", "回款状态/回款日期"]
  }
}
```

启用 R2 后，`download_url` 会返回一个对象存储签名下载地址，前端可直接跳转下载，避免再次重算。

## GET /api/reports/{report_id}

获取结果预览、指标、异常统计和下载地址。

## GET /api/reports/{report_id}/download

下载包含多个 sheet 的完整 xlsx。

## GET /api/sample-file

下载示例 CSV 文件。

## GET /api/history

获取最近上传和生成记录。
