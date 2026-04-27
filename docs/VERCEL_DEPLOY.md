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
- 入口文件：`app.py`
- Vercel 会将 FastAPI 识别为单个 Python Function；官方支持的入口名包含 `app.py`、`index.py`、`server.py` 等。[FastAPI on Vercel](https://vercel.com/docs/frameworks/backend/fastapi)

主要环境变量：

- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL`
- `ALLOWED_ORIGINS=https://<your-web-project>.vercel.app`
- 可选：`DATA_ROOT=/tmp/finance-splitter`

## 3. 当前实现的 Vercel 适配

本次改造已包含：

- FastAPI 标准入口 `apps/api/app.py`
- 在 Vercel 环境下自动使用 `/tmp/finance-splitter` 作为临时数据目录
- 前端下载改为 `POST /api/reports/download-direct` 直出 xlsx，减少对持久磁盘的依赖
- 可通过 `ALLOWED_ORIGINS` 配置线上 CORS 域名

## 4. 仍需注意的限制

### 请求体大小

Vercel Functions 的请求体和响应体最大为 `4.5 MB`。超过上限会返回 `413`。[Functions Limits](https://vercel.com/docs/functions/limitations)

这意味着：

- 小型 Excel/CSV 可以直接上传到后端
- 大文件建议走对象存储直传

### Python 函数体积

FastAPI 应用会被打成单个 Python Function，需满足 `500MB` bundle 限制。[FastAPI on Vercel](https://vercel.com/docs/frameworks/backend/fastapi)

### 无状态存储

Vercel 不是持久磁盘环境。本项目目前通过 `/tmp` 支持临时文件处理，足以完成单次上传、预览和下载流程，但如果你需要：

- 跨会话历史记录
- 模板长期保存
- 大文件长期留存

建议继续接入：

- Vercel Blob / S3 / OSS：原始文件与导出文件
- Postgres / Neon / Supabase：历史记录与模板

## 5. 推荐上线顺序

1. 先部署 `apps/api`
2. 拿到 API 域名后，配置 `apps/web` 的 `NEXT_PUBLIC_API_BASE_URL`
3. 部署 `apps/web`
4. 回到 `apps/api` 配置 `ALLOWED_ORIGINS`
5. 用一份小型样例表先验收完整上传与导出链路
