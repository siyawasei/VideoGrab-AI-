"""下载相关 API 路由"""

import asyncio
import json
import os
import shutil

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from models import DownloadHistory, User
from api.auth import get_current_user_optional
from api.downloader import extract_info, start_download, get_task, normalize_url
from api.bilibili import is_bilibili_url, bilibili_extract_info, bilibili_download_stream, bilibili_merge_streams, get_cached_info, _extract_bvid
from config import MEMBERSHIP_LIMITS, COOKIES_DIR

router = APIRouter(prefix="/api", tags=["download"])


class InfoRequest(BaseModel):
    url: str


class DownloadRequest(BaseModel):
    url: str
    format_id: str
    quality: str


@router.post("/info")
async def get_video_info(req: InfoRequest):
    """解析视频 URL，返回视频信息和可用格式"""
    try:
        url = normalize_url(req.url)
        loop = asyncio.get_event_loop()
        # B站使用专用 API 绕过 412
        if is_bilibili_url(url):
            info = await loop.run_in_executor(None, bilibili_extract_info, url)
        else:
            info = await loop.run_in_executor(None, extract_info, url)
        return {"code": 0, "data": info}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"解析失败: {str(e)}")


@router.post("/download")
async def download_video(
    req: DownloadRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """开始下载视频"""
    # 检查用户下载次数限制
    if current_user:
        limit = MEMBERSHIP_LIMITS.get(current_user.membership, MEMBERSHIP_LIMITS["free"])
        if current_user.daily_downloads_used >= limit["daily_downloads"]:
            raise HTTPException(status_code=403, detail="今日下载次数已用完，请升级会员")
        current_user.daily_downloads_used += 1
        db.commit()

    # B站使用专用下载逻辑
    url = normalize_url(req.url)
    if is_bilibili_url(url):
        task_id = _start_bilibili_download(url, req.format_id, req.quality)
    else:
        task_id = start_download(url, req.format_id, req.quality)

    # 记录到数据库
    if current_user:
        history = DownloadHistory(
            user_id=current_user.id,
            url=req.url,
            quality=req.quality,
            status="downloading",
        )
        db.add(history)
        db.commit()

    return {"code": 0, "data": {"task_id": task_id}}


def _start_bilibili_download(url: str, format_id: str, quality: str) -> str:
    """创建 B站下载任务（DASH 流合并）"""
    import uuid
    from concurrent.futures import ThreadPoolExecutor
    from api.downloader import download_tasks, executor, _progress_hook

    task_id = str(uuid.uuid4())[:8]
    download_tasks[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "progress": 0,
        "speed": "",
        "eta": "",
        "url": url,
        "format_id": format_id,
        "quality": quality,
        "filename": "",
        "filepath": "",
        "file_size": 0,
        "title": "",
        "error": "",
    }

    def _bilibili_task():
        import os, time
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from config import DOWNLOAD_DIR
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)

        try:
            download_tasks[task_id]["status"] = "downloading"
            download_tasks[task_id]["progress"] = 10

            # 每次下载都获取新鲜的流 URL（避免过期）
            info = bilibili_extract_info(url)
            title = info.get("title", "bilibili_video")
            cookies = info.get("cookies", {})
            download_tasks[task_id]["title"] = title
            download_tasks[task_id]["progress"] = 20

            # 找到选中的格式，获取流地址
            selected_format = None
            audio_format = None
            for f in info.get("formats", []):
                if f.get("format_id") == format_id:
                    selected_format = f
                if f.get("has_audio") and f.get("audio_url"):
                    audio_format = f

            # 获取视频流 URL
            video_url = None
            if selected_format and selected_format.get("video_url"):
                video_url = selected_format["video_url"]
            else:
                for f in info.get("formats", []):
                    if f.get("has_video") and f.get("video_url"):
                        video_url = f["video_url"]
                        break

            if not video_url:
                for f in info.get("formats", []):
                    if f.get("has_video") and f.get("has_audio") and f.get("url"):
                        video_url = f["url"]
                        break

            if not video_url:
                download_tasks[task_id].update({"status": "failed", "error": "未找到可用的视频流"})
                return

            download_tasks[task_id]["progress"] = 30

            safe_title = "".join(c for c in title[:40] if c.isalnum() or c in " _-.") or "bilibili"
            output_path = os.path.join(DOWNLOAD_DIR, f"{task_id}_{safe_title}.mp4")

            if audio_format and audio_format.get("audio_url"):
                # DASH 格式：并发下载视频和音频，再合并
                video_tmp = os.path.join(DOWNLOAD_DIR, f"{task_id}_video.m4s")
                audio_tmp = os.path.join(DOWNLOAD_DIR, f"{task_id}_audio.m4s")

                download_tasks[task_id]["progress"] = 35

                # 获取备用 URL
                video_backups = selected_format.get("video_urls", [])[1:] if selected_format else []
                audio_backups = audio_format.get("audio_urls", [])[1:] if audio_format else []

                # 并发下载（自动尝试备用 CDN）
                dl_pool = ThreadPoolExecutor(max_workers=2)
                video_future = dl_pool.submit(bilibili_download_stream, video_url, video_tmp, cookies, video_backups)
                audio_future = dl_pool.submit(bilibili_download_stream, audio_format["audio_url"], audio_tmp, cookies, audio_backups)

                video_future.result()
                download_tasks[task_id]["progress"] = 60

                audio_future.result()
                download_tasks[task_id]["progress"] = 80

                download_tasks[task_id]["progress"] = 85
                bilibili_merge_streams(video_tmp, audio_tmp, output_path)

                for tmp in [video_tmp, audio_tmp]:
                    if os.path.exists(tmp):
                        os.remove(tmp)
            else:
                # 单文件下载
                download_tasks[task_id]["progress"] = 50
                video_backups = selected_format.get("video_urls", [])[1:] if selected_format else []
                bilibili_download_stream(video_url, output_path, cookies, video_backups)

            file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
            download_tasks[task_id].update({
                "status": "completed",
                "progress": 100,
                "filename": os.path.basename(output_path),
                "filepath": output_path,
                "file_size": file_size,
                "title": title,
            })

        except Exception as e:
            download_tasks[task_id].update({"status": "failed", "error": str(e)})

    executor.submit(_bilibili_task)
    return task_id


@router.get("/progress/{task_id}")
async def progress_stream(task_id: str):
    """SSE 实时推送下载进度"""

    async def event_generator():
        while True:
            task = get_task(task_id)
            if not task:
                yield f"data: {json.dumps({'status': 'error', 'error': '任务不存在'})}\n\n"
                break

            yield f"data: {json.dumps(task, ensure_ascii=False)}\n\n"

            if task["status"] in ("completed", "failed"):
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/file/{task_id}")
async def download_file(task_id: str):
    """下载已完成的视频文件"""
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="下载尚未完成")
    if not os.path.exists(task["filepath"]):
        raise HTTPException(status_code=404, detail="文件不存在")

    return FileResponse(
        path=task["filepath"],
        filename=task["filename"],
        media_type="application/octet-stream",
    )


@router.post("/cookies/upload")
async def upload_cookies(file: UploadFile = File(...)):
    """上传 cookies.txt 文件（Netscape 格式）"""
    os.makedirs(COOKIES_DIR, exist_ok=True)
    dest = os.path.join(COOKIES_DIR, "cookies.txt")
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"code": 0, "message": "Cookies 上传成功", "path": dest}


@router.get("/cookies/status")
async def cookies_status():
    """检查 cookies 文件是否存在"""
    path = os.path.join(COOKIES_DIR, "cookies.txt")
    exists = os.path.exists(path)
    return {"code": 0, "data": {"exists": exists, "path": path if exists else None}}


@router.post("/bilibili/sessdata")
async def set_bilibili_sessdata(body: dict):
    """设置 Bilibili SESSDATA（解锁高清画质）"""
    sessdata = body.get("sessdata", "").strip()
    os.makedirs(COOKIES_DIR, exist_ok=True)
    path = os.path.join(COOKIES_DIR, "bilibili_sessdata.txt")
    with open(path, "w") as f:
        f.write(sessdata)
    return {"code": 0, "message": "SESSDATA 已保存，B站高清画质已解锁"}


@router.get("/bilibili/sessdata")
async def get_bilibili_sessdata():
    """获取 Bilibili SESSDATA 状态"""
    path = os.path.join(COOKIES_DIR, "bilibili_sessdata.txt")
    exists = os.path.exists(path)
    has_data = False
    if exists:
        with open(path) as f:
            has_data = bool(f.read().strip())
    return {"code": 0, "data": {"exists": has_data}}


@router.get("/platforms")
async def get_platforms():
    """获取支持的平台列表和状态"""
    from api.downloader import PLATFORM_CONFIG
    platforms = []
    seen = set()
    for domain, config in PLATFORM_CONFIG.items():
        name = config["name"]
        if name in seen:
            continue
        seen.add(name)
        platforms.append({
            "name": name,
            "domain": domain,
            "status": config["status"],
            "note": config["note"],
        })
    return {"code": 0, "data": platforms}
