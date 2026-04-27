# 财务数据一键拆表助手 - 产品与技术架构

## 1. 完整产品架构

财务数据一键拆表助手面向财务分析、出纳、会计和经营分析人员，核心路径是“上传原始数据 -> 自动识别字段 -> 人工确认映射 -> 配置报表 -> 预览结果 -> 下载多 sheet Excel”。产品由以下模块组成：

1. 上传中心：接收 `.xlsx`、`.xls`、`.csv`，保存上传记录，抽取样本数据。
2. 字段识别中心：基于字段别名、值分布和 AI 识别占位模块推断标准字段。
3. 模板中心：保存字段映射规则，下次上传同类文件时复用。
4. 数据处理中心：统一列名、清洗空值、标准化日期/金额、识别收入支出方向，保留原始行号用于追溯。
5. 异常检查中心：检查金额、日期、重复单号、主体缺失、方向异常、异常金额和无法识别值。
6. 报表生成中心：生成清洗明细、收入、支出、月度、部门、客户、供应商、异常和管理摘要。
7. 结果交付中心：提供前 20 行预览、关键指标、异常统计、完整 xlsx 下载，预留 zip 导出。
8. 历史中心：记录上传、生成任务和下载结果。

## 2. 技术架构

前端使用 Next.js App Router、React、TypeScript、Tailwind CSS、shadcn/ui 风格组件、Zustand、react-dropzone 和 TanStack Table。后端使用 FastAPI、pandas、openpyxl、pydantic 和 python-multipart。MVP 使用本地 JSON 文件作为轻量存储，便于直接运行；上线时可替换为 PostgreSQL 或 SQLite。

部署形态建议为前后端分离：Next.js 部署为 Web 服务，FastAPI 部署为 API 服务，并通过 `NEXT_PUBLIC_API_BASE_URL` 指向后端。文件和导出物默认保存在服务端磁盘，生产环境建议迁移到对象存储。

## 3. 项目目录结构

```text
apps/
  api/
    app/
      core/            # 配置、存储、常量
      models/          # Pydantic 模型
      routers/         # FastAPI 路由
      services/        # 上传、识别、清洗、异常、报表、导出、模板
    data/              # MVP 本地数据目录
    requirements.txt
  web/
    app/               # Next.js 页面
    components/ui/     # shadcn 风格基础组件
    lib/               # API、工具函数
    store/             # Zustand 状态
docs/
  ARCHITECTURE.md
  API.md
sample_data/
  finance_sample.csv
README.md
```

## 4. 数据流设计

```text
Upload(xlsx/xls/csv)
  -> file_service 保存文件并读取样本
  -> field_detector 别名识别 + 值分布识别 + ai_field_detector 占位
  -> 用户在 Mapping 页面确认字段映射
  -> normalizer 根据映射输出标准 DataFrame
  -> anomaly_checker 生成异常原因
  -> report_builder 生成多张业务表和指标
  -> excel_exporter 写入格式、公式、筛选、冻结窗格、条件格式
  -> Result Preview 返回预览、指标、异常统计、下载链接
```

标准字段包括：`date`、`amount`、`direction`、`department`、`project`、`customer`、`supplier`、`order_no`、`payment_method`、`invoice_status`、`remark`。

## 5. 数据库表设计

MVP 用 JSON 文件模拟以下表。生产环境建议按此结构建表。

### upload_files

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | uuid | 上传文件 ID |
| original_name | varchar | 原始文件名 |
| stored_path | varchar | 服务端保存路径 |
| file_type | varchar | xlsx/xls/csv |
| rows_count | int | 行数 |
| columns | jsonb | 原始列名 |
| sample_rows | jsonb | 样本行 |
| created_at | timestamp | 上传时间 |

### field_templates

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | uuid | 模板 ID |
| name | varchar | 模板名称 |
| mapping | jsonb | 原始列到标准字段映射 |
| source_columns | jsonb | 模板来源列 |
| created_at | timestamp | 创建时间 |
| updated_at | timestamp | 更新时间 |

### report_jobs

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | uuid | 任务 ID |
| upload_id | uuid | 上传文件 ID |
| template_id | uuid | 使用模板 |
| config | jsonb | 生成配置 |
| status | varchar | queued/running/succeeded/failed |
| metrics | jsonb | 关键指标 |
| anomaly_summary | jsonb | 异常统计 |
| created_at | timestamp | 创建时间 |
| finished_at | timestamp | 完成时间 |

### report_outputs

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | uuid | 输出 ID |
| job_id | uuid | 任务 ID |
| xlsx_path | varchar | xlsx 文件路径 |
| zip_path | varchar | zip 文件路径，预留 |
| sheets | jsonb | sheet 元信息 |
| created_at | timestamp | 创建时间 |

### processing_events

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | uuid | 事件 ID |
| job_id | uuid | 任务 ID |
| level | varchar | info/warn/error |
| message | text | 处理日志 |
| payload | jsonb | 事件详情 |
| created_at | timestamp | 创建时间 |

## 6. API 设计

详见 `docs/API.md`。核心接口包括上传、字段映射、模板保存、报表生成、结果查询、下载、示例文件和历史记录。

## 7. MVP 上线边界

第一版实现真实可运行的数据处理、9 张表、多 sheet xlsx、字段映射模板、结果预览、异常统计和老板摘要文案。AI 字段识别以可替换接口形式预留，后续可接 OpenRouter、OpenAI 或内部模型。
