"""FastAPI 主入口 — 前后端统一端口"""

import sys
from contextlib import asynccontextmanager

sys.stdout.reconfigure(encoding="utf-8")

import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

from database import init_db
from api.routes import router as download_router
from api.auth import router as auth_router
from api.history import router as history_router
from api.ai import router as ai_router

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
_FRONTEND_PUBLIC = os.path.join(BASE_DIR, "frontend", "public")
_FRONTEND_DIST = os.path.join(BASE_DIR, "frontend", "dist")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("✅ 数据库表已初始化")
    yield


app = FastAPI(title="万能视频下载器", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API 路由 ────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(download_router)
app.include_router(history_router)
app.include_router(ai_router)


# ── SEO 静态页面 ────────────────────────────────────────────
@app.get("/features", response_class=HTMLResponse)
@app.get("/features.html", response_class=HTMLResponse)
async def features_page():
    path = os.path.join(_FRONTEND_PUBLIC, "features.html")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Not Found</h1>", status_code=404)


@app.get("/faq", response_class=HTMLResponse)
@app.get("/faq.html", response_class=HTMLResponse)
async def faq_page():
    path = os.path.join(_FRONTEND_PUBLIC, "faq.html")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Not Found</h1>", status_code=404)


@app.get("/robots.txt")
async def robots_txt():
    path = os.path.join(_FRONTEND_PUBLIC, "robots.txt")
    if os.path.exists(path):
        return FileResponse(path, media_type="text/plain")
    return HTMLResponse(content="User-agent: *\nAllow: /", media_type="text/plain")


@app.get("/sitemap.xml")
async def sitemap_xml():
    path = os.path.join(_FRONTEND_PUBLIC, "sitemap.xml")
    if os.path.exists(path):
        return FileResponse(path, media_type="application/xml")
    return HTMLResponse(content="<urlset/>", media_type="application/xml")


# ── 前端静态文件 ────────────────────────────────────────────
if os.path.isdir(_FRONTEND_DIST):
    # 直接挂载整个 dist 目录（favicon、assets、public 文件全部由 StaticFiles 处理）
    app.mount("/assets", StaticFiles(directory=os.path.join(_FRONTEND_DIST, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        """SPA 兜底路由"""
        # 尝试在 dist 中查找精确文件（favicon.ico 等）
        file_path = os.path.join(_FRONTEND_DIST, full_path)
        if full_path and os.path.isfile(file_path):
            resp = FileResponse(file_path)
            # index.html 不缓存（确保更新后立即生效）
            if full_path == "index.html":
                resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            return resp
        # 兜底返回 index.html（Vue Router 处理前端路由）
        index_path = os.path.join(_FRONTEND_DIST, "index.html")
        if os.path.exists(index_path):
            resp = FileResponse(index_path)
            resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            return resp
        return HTMLResponse(content="<h1>请先构建前端: cd frontend && npm run build</h1>", status_code=503)

    print(f"✅ 前端静态文件已挂载: {_FRONTEND_DIST}")
else:
    @app.get("/")
    async def root():
        return {"message": "万能视频下载器 API", "version": "1.0.0", "note": "前端未构建，请执行: cd frontend && npm run build"}
    print(f"⚠️  前端未构建 ({_FRONTEND_DIST} 不存在)，仅提供 API")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
