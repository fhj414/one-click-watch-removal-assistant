# 财务数据一键拆表助手

一个面向财务人员的智能 Excel 处理平台。上传原始 Excel/CSV 后，系统自动识别字段、清洗数据、分类汇总、检查异常，并导出包含多张 sheet 的可用 Excel 工作簿。

## 功能

- 上传 `.xlsx`、`.xls`、`.csv`
- 字段别名自动识别和手动映射
- 模板保存与复用
- 生成原始清洗表、收入明细、支出明细、月度汇总、部门汇总、客户汇总、供应商汇总、异常数据、管理摘要
- Excel 自动格式：加粗表头、冻结首行、筛选、金额格式、日期格式、合计、公式、条件格式
- 结果预览、关键指标、异常统计、老板摘要文案
- 处理历史记录
- Cloudflare R2 直传与结果回写，适合 Vercel 线上部署
- 动态财务 BP 报表规划：根据上传字段自动增加产品线、预算偏差、费用归口、回款状态等 TCL BP 常用分析表

## 启动方式

### 后端

```bash
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 前端

```bash
cd apps/web
npm install
npm run dev
```

打开 `http://127.0.0.1:3000`。

## OpenRouter 增强

如需启用 AI 增强识别和财务 BP 洞察：

1. 在 `apps/api/.env` 中配置 `OPENROUTER_API_KEY`
2. 可选配置 `OPENROUTER_MODEL`
3. 重启后端

当前代码已支持通过 OpenRouter 进行：

- 字段映射二次判读
- 老板摘要 / 财务 BP 洞察生成
- 风险提示和建议动作输出
- 额外生成 `财务BP洞察表`

推荐默认模型：

- `qwen/qwen3-30b-a3b`：中文、表格理解、结构化输出和速度的平衡最好，适合作为默认线上模型
- `deepseek/deepseek-chat-v3-0324`：推理更强，适合偏复杂的口径归因
- `google/gemini-2.5-flash`：速度快，但输出成本明显更高

线上速度建议：

- `ENABLE_REMOTE_AI_ON_GENERATE=false`：生成预览时不等待远程模型，优先返回规则版 BP 摘要和数据预览
- 下载完整 Excel 时仍会按当前数据重新生成工作簿，避免预览阶段同步导出造成长时间等待

## Cloudflare R2 对象存储

如需让上传和下载更适合线上环境，建议配置 R2。启用后：

- 浏览器先向后端申请预签名上传地址
- 原始文件直接上传到 R2
- 后端从 R2 回源识别字段和生成报表
- 生成后的完整 Excel 也会写回 R2，并优先走对象存储直链下载

需要在 `apps/api/.env` 中配置：

- `R2_ACCOUNT_ID`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET_NAME`
- 可选：`R2_ENDPOINT_URL`
- 可选：`R2_PUBLIC_BASE_URL`
- 可选：`R2_PRESIGNED_EXPIRES`
- 可选：`R2_UPLOAD_PREFIX`
- 可选：`R2_EXPORT_PREFIX`

## 页面截图说明位

- 首页：上传区、示例下载、功能亮点、最近模板。
- 字段识别页：左侧原始列名，右侧系统识别和下拉校正。
- 生成配置页：报表多选、异常检查、自动公式、摘要分析、导出版本。
- 结果预览页：指标卡、异常统计、sheet 预览、下载按钮。
- 历史记录页：最近上传、生成任务、下载入口。

## 文档

- 产品与技术架构：`docs/ARCHITECTURE.md`
- API 设计：`docs/API.md`
- Vercel 部署：`docs/VERCEL_DEPLOY.md`
- 示例数据：`sample_data/finance_sample.csv`
