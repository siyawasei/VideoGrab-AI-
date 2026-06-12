"""FastAPI 主入口"""

import sys
from contextlib import asynccontextmanager

# Windows 控制台 UTF-8 支持
sys.stdout.reconfigure(encoding="utf-8")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from api.routes import router as download_router
from api.auth import router as auth_router
from api.history import router as history_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动时初始化数据库"""
    init_db()
    print("✅ 数据库表已初始化")
    yield


app = FastAPI(title="万能视频下载器", version="1.0.0", lifespan=lifespan)

# CORS 配置（允许前端开发服务器访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router)
app.include_router(download_router)
app.include_router(history_router)


@app.get("/")
async def root():
    return {"message": "万能视频下载器 API", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
