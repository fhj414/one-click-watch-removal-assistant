from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import ALLOWED_ORIGINS, ensure_data_dirs
from app.routers import misc, reports, templates, uploads

ensure_data_dirs()

app = FastAPI(title="财务数据一键拆表助手 API", version="0.1.0")

default_origins = [
    "http://127.0.0.1:3000",
    "http://localhost:3000",
    "http://127.0.0.1:3001",
    "http://localhost:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=default_origins + ALLOWED_ORIGINS,
    allow_origin_regex=r"http://(127\.0\.0\.1|localhost):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(uploads.router)
app.include_router(templates.router)
app.include_router(reports.router)
app.include_router(misc.router)
