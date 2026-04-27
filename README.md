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

## 页面截图说明位

- 首页：上传区、示例下载、功能亮点、最近模板。
- 字段识别页：左侧原始列名，右侧系统识别和下拉校正。
- 生成配置页：报表多选、异常检查、自动公式、摘要分析、导出版本。
- 结果预览页：指标卡、异常统计、sheet 预览、下载按钮。
- 历史记录页：最近上传、生成任务、下载入口。

## 文档

- 产品与技术架构：`docs/ARCHITECTURE.md`
- API 设计：`docs/API.md`
- 示例数据：`sample_data/finance_sample.csv`
