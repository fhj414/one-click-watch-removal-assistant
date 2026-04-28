# Vercel 部署说明

本仓库建议作为两个独立的 Vercel Project 部署：

1. `apps/web`：Next.js 前端
2. `apps/api`：FastAPI 后端

这符合 Vercel 官方对 monorepo 的建议：为同一仓库中的多个目录分别设置 Root Directory。[Vercel Monorepos](https://vercel.com/docs/monorepos)

## 1. 前端项目

- Root Directory：`apps/web`
- Framework：Next.js
- 主要环境变量：
  - `NEXT_PUBLIC_API_BASE_URL=https://<your-api-project>.vercel.app`

## 2. 后端项目

- Root Directory：`apps/api`
- 入口文件：`api/index.py`
- Vercel 会从项目内的 `api/` 目录识别 Python Serverless Function；当前仓库已经改成 `api/index.py` 作为 FastAPI 入口。[FastAPI on Vercel](https://vercel.com/docs/frameworks/backend/fastapi)
- 后端项目不再依赖自定义 `vercel.json` 的 `functions` pattern，避免因目录匹配导致部署失败；如需调整执行时长，优先在 Vercel 项目设置里配置。

主要环境变量：

- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL`
- `ENABLE_REMOTE_AI_ON_GENERATE=false`
- `ALLOWED_ORIGINS=https://<your-web-project>.vercel.app`
- `R2_ACCOUNT_ID`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET_NAME`
- 可选：`DATA_ROOT=/tmp/finance-splitter`
- 可选：`R2_ENDPOINT_URL`
- 可选：`R2_PUBLIC_BASE_URL`
- 可选：`R2_PRESIGNED_EXPIRES=3600`
- 可选：`R2_UPLOAD_PREFIX=uploads`
- 可选：`R2_EXPORT_PREFIX=exports`

## 3. 当前实现的 Vercel 适配

本次改造已包含：

- FastAPI 标准入口 `apps/api/api/index.py`
- 在 Vercel 环境下自动使用 `/tmp/finance-splitter` 作为临时数据目录
- 启用 R2 后，前端先获取预签名上传地址，再直传源文件到对象存储
- 线上预览生成不再同步导出完整 Excel，避免 `/api/reports/generate` 被 Excel 导出和 R2 写入拖慢
- 可通过 `ALLOWED_ORIGINS` 配置线上 CORS 域名

如果启用 Cloudflare R2，请在桶上补一条 CORS，至少允许：

- Origin：你的前端域名
- Methods：`PUT`, `GET`, `HEAD`
- Headers：`Content-Type`

## 4. 仍需注意的限制

### 请求体大小

Vercel Functions 的请求体和响应体最大为 `4.5 MB`。超过上限会返回 `413`。[Functions Limits](https://vercel.com/docs/functions/limitations)

这意味着：

- 小型 Excel/CSV 可以直接上传到后端
- 线上环境强烈建议启用 R2 直传，避免把大文件全部经过 Python Function

### Python 函数体积

FastAPI 应用会被打成单个 Python Function，需满足 `500MB` bundle 限制。[FastAPI on Vercel](https://vercel.com/docs/frameworks/backend/fastapi)

### 无状态存储

Vercel 不是持久磁盘环境。本项目目前通过 `/tmp` 支持临时文件处理，足以完成单次上传、预览和下载流程，但如果你需要：

- 跨会话历史记录
- 模板长期保存
- 大文件长期留存

建议继续接入：

- Cloudflare R2 / S3 / OSS：原始文件与导出文件
- Postgres / Neon / Supabase：历史记录与模板

## 5. 推荐上线顺序

1. 先部署 `apps/api`
2. 拿到 API 域名后，配置 `apps/web` 的 `NEXT_PUBLIC_API_BASE_URL`
3. 部署 `apps/web`
4. 回到 `apps/api` 配置 `ALLOWED_ORIGINS`
5. 用一份小型样例表先验收完整上传与导出链路
