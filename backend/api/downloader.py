"""yt-dlp 封装：视频解析和下载核心逻辑

根据 yt-dlp 2026.06.09 源码，各平台支持情况：
- B站: yt-dlp extractor 已过时(WBI反爬)，使用自定义 API 处理器
- 优酷/芒果TV/AcFun: yt-dlp 直接支持
- 抖音: yt-dlp 支持，部分视频需要 cookies
- 西瓜视频: 需要 cookies
- 爱奇艺: extractor 已过时(API变更)
- 微博: extractor 已过时(解析报错)
- 腾讯视频: DRM 版权保护，无法下载
- 快手/小红书: yt-dlp 无 extractor 或 extractor 失效
"""

import os
import re
import uuid
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import yt_dlp

from config import DOWNLOAD_DIR

# 下载任务存储（内存）
download_tasks: dict = {}

# 线程池
executor = ThreadPoolExecutor(max_workers=4)

# 平台配置：根据 yt-dlp 源码和实测结果
PLATFORM_CONFIG = {
    "bilibili.com":     {"name": "B站",      "status": "ok",       "handler": "custom",  "note": "自定义API处理器"},
    "b23.tv":           {"name": "B站短链",   "status": "ok",       "handler": "custom",  "note": "自定义API处理器"},
    "youku.com":        {"name": "优酷",      "status": "ok",       "handler": "ytdlp",   "note": "yt-dlp直接支持"},
    "acfun.cn":         {"name": "AcFun",     "status": "ok",       "handler": "ytdlp",   "note": "yt-dlp直接支持"},
    "douyin.com":       {"name": "抖音",      "status": "ok",       "handler": "ytdlp",   "note": "大部分视频可用"},
    "mgtv.com":         {"name": "芒果TV",    "status": "ok",       "handler": "ytdlp",   "note": "yt-dlp直接支持"},
    "ixigua.com":       {"name": "西瓜视频",  "status": "cookies",  "handler": "ytdlp",   "note": "需要上传cookies"},
    "iqiyi.com":        {"name": "爱奇艺",    "status": "broken",   "handler": "ytdlp",   "note": "yt-dlp extractor已过时"},
    "weibo.com":        {"name": "微博",      "status": "broken",   "handler": "ytdlp",   "note": "yt-dlp extractor已过时"},
    "m.weibo.cn":       {"name": "微博",      "status": "broken",   "handler": "ytdlp",   "note": "yt-dlp extractor已过时"},
    "v.qq.com":         {"name": "腾讯视频",  "status": "throttled", "handler": "ytdlp",   "note": "CDN限速，下载极慢"},
    "kuaishou.com":     {"name": "快手",      "status": "noext",    "handler": "none",    "note": "yt-dlp无此extractor"},
    "xiaohongshu.com":  {"name": "小红书",    "status": "broken",   "handler": "ytdlp",   "note": "extractor失效"},
}

# 需要 cookies 的平台
COOKIE_DOMAINS = ["ixigua.com", "douyin.com", "tiktok.com", "xiaohongshu.com"]


def normalize_url(url: str) -> str:
    """规范化视频链接：短链接重定向、提取真实视频地址"""
    url = url.strip()

    # 抖音短链接（v.douyin.com）→ 跟随重定向获取真实地址
    if "v.douyin.com" in url:
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            })
            resp = urllib.request.urlopen(req, timeout=10)
            url = resp.geturl()
        except Exception as e:
            # 有些重定向会在错误中返回 Location
            if hasattr(e, "headers") and e.headers.get("Location"):
                url = e.headers["Location"]

    # 抖音精选页（jingxuan?modal_id=xxx）→ 提取 modal_id 构造视频链接
    if "douyin.com/jingxuan" in url:
        match = re.search(r"modal_id=(\d+)", url)
        if match:
            url = f"https://www.douyin.com/video/{match.group(1)}"

    # YouTube 缩短链接（youtu.be/xxx）→ 展开
    if "youtu.be/" in url:
        match = re.search(r"youtu\.be/([a-zA-Z0-9_-]+)", url)
        if match:
            url = f"https://www.youtube.com/watch?v={match.group(1)}"

    # B站短链接（b23.tv）→ 跟随重定向
    if "b23.tv" in url:
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            })
            resp = urllib.request.urlopen(req, timeout=10)
            url = resp.geturl()
        except Exception:
            pass

    return url


def detect_platform(url: str) -> dict | None:
    """检测 URL 对应的平台配置"""
    for domain, config in PLATFORM_CONFIG.items():
        if domain in url:
            return config
    return None


def _get_ydl_opts(extra_opts: dict = None) -> dict:
    """获取 yt-dlp 基础配置"""
    opts = {
        "quiet": True,
        "no_warnings": True,
        "no_color": True,
        "socket_timeout": 15,
        "ffmpeg_location": _find_ffmpeg(),
    }
    if extra_opts:
        opts.update(extra_opts)
    return opts


def _find_ffmpeg() -> str:
    """查找 ffmpeg 路径"""
    import shutil
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        return os.path.dirname(ffmpeg)
    for path in [
        r"C:\Program Files\ffmpeg\bin",
        r"C:\ffmpeg\bin",
    ]:
        if os.path.exists(os.path.join(path, "ffmpeg.exe")):
            return path
    return ""


def _try_extract_with_cookies(url: str, download: bool = False, extra_opts: dict = None):
    """尝试解析/下载，按优先级尝试不同 cookie 来源"""
    base_opts = _get_ydl_opts(extra_opts)
    cookie_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cookies", "cookies.txt")

    # 第一次尝试：不带 cookies
    try:
        with yt_dlp.YoutubeDL(base_opts) as ydl:
            return ydl.extract_info(url, download=download)
    except Exception as first_err:
        err_msg = str(first_err)

    # 第二次尝试：使用上传的 cookie 文件
    if os.path.exists(cookie_file):
        try:
            cookie_opts = {**base_opts, "cookiefile": cookie_file}
            with yt_dlp.YoutubeDL(cookie_opts) as ydl:
                return ydl.extract_info(url, download=download)
        except Exception:
            pass

    # 第三次尝试：读取浏览器 cookies（仅对需要 cookies 的平台）
    if any(d in url for d in COOKIE_DOMAINS) or "412" in err_msg or "403" in err_msg or "cookies" in err_msg.lower():
        for browser in ["chrome", "edge", "firefox"]:
            try:
                cookie_opts = {**base_opts, "cookiesfrombrowser": (browser,)}
                with yt_dlp.YoutubeDL(cookie_opts) as ydl:
                    return ydl.extract_info(url, download=download)
            except Exception:
                continue

    raise Exception(err_msg)


def _format_error(url: str, err: Exception) -> str:
    """根据平台和错误类型生成友好的错误提示"""
    err_msg = str(err)
    platform = detect_platform(url)

    if platform:
        name = platform["name"]
        status = platform["status"]
        note = platform["note"]

        if status == "cookies":
            return f"[{name}] 需要 cookies 才能解析。请在浏览器登录{name}后，用扩展导出 cookies.txt 并上传。"
        elif status == "broken":
            return f"[{name}] yt-dlp 的{name}解析器已过时（{note}）。请等待 yt-dlp 更新。"
        elif status == "drm":
            return f"[{name}] 视频受 DRM 版权保护，无法下载。"
        elif status == "throttled":
            return f"[{name}] {note}。视频可解析但下载速度极慢，不建议使用。"
        elif status == "noext":
            return f"[{name}] yt-dlp 暂不支持{name}（{note}）。"

    if "cookies" in err_msg.lower():
        return "此平台需要 cookies。请在浏览器登录后，用 'Get cookies.txt LOCALLY' 扩展导出并上传。"
    if "Unsupported URL" in err_msg:
        return "不支持的链接格式。请检查链接是否正确。"
    if "timeout" in err_msg.lower():
        return "网络连接超时，请检查网络或稍后重试。"

    return f"解析失败: {err_msg[:150]}"


def extract_info(url: str) -> dict:
    """解析视频 URL，返回标题、封面、可用格式列表"""
    # YouTube 优先返回 H.264 格式（兼容性最好）
    extra_opts = {}
    if "youtube.com" in url or "youtu.be" in url:
        extra_opts["format_sort"] = ["vcodec:h264", "acodec:aac"]

    try:
        info = _try_extract_with_cookies(url, download=False, extra_opts=extra_opts)
    except Exception as e:
        raise Exception(_format_error(url, e))

    # 提取可用格式
    formats = []
    seen = set()
    for f in info.get("formats", []):
        if f.get("vcodec") == "none" and f.get("acodec") == "none":
            continue

        height = f.get("height")
        quality = f"{height}p" if height else (f.get("format_note") or "audio")
        ext = f.get("ext", "mp4")

        vcodec = f.get("vcodec")
        acodec = f.get("acodec")
        has_video = vcodec not in (None, "none") if vcodec is not None else bool(height)
        has_audio = acodec not in (None, "none") if acodec is not None else True

        # 去重：按分辨率+扩展名去重（忽略 CDN 后缀和编码差异）
        key = f"{quality}_{ext}_{has_video}_{has_audio}"
        if key in seen:
            continue
        seen.add(key)

        formats.append({
            "format_id": f["format_id"],
            "quality": quality,
            "ext": ext,
            "filesize": f.get("filesize") or f.get("filesize_approx"),
            "has_video": has_video,
            "has_audio": has_audio,
            "fps": f.get("fps"),
            "vcodec": f.get("vcodec"),
            "acodec": f.get("acodec"),
        })

    def sort_key(item):
        q = item["quality"]
        if q and "p" in q:
            try:
                return int(q.replace("p", ""))
            except ValueError:
                pass
        return 0
    formats.sort(key=sort_key, reverse=True)

    # 检查是否有可下载格式
    if not formats:
        platform = detect_platform(url)
        name = platform["name"] if platform else "此平台"
        raise Exception(f"[{name}] 解析成功但无可下载格式。可能原因：视频受 DRM 版权保护、需要登录、或 yt-dlp 解析器已过时。")

    extractor = info.get("extractor_key") or info.get("extractor") or "Unknown"

    return {
        "title": info.get("title", "未知标题"),
        "thumbnail": info.get("thumbnail"),
        "duration": info.get("duration"),
        "uploader": info.get("uploader", "未知"),
        "uploader_avatar": info.get("channel_avatar") or info.get("uploader_avatar"),
        "view_count": info.get("view_count") or info.get("play_count"),
        "like_count": info.get("like_count"),
        "description": info.get("description", ""),
        "platform": extractor,
        "formats": formats,
    }


def _progress_hook(task_id: str):
    """返回一个 yt-dlp progress_hooks 回调函数"""
    def hook(d):
        if task_id not in download_tasks:
            return
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            speed = d.get("speed") or 0
            eta = d.get("eta") or 0

            # 计算进度：优先用字节，其次用 HLS 分片，最后用百分比字符串
            if total and downloaded:
                progress = downloaded / total * 100
            elif d.get("fragment_index") and d.get("fragment_count"):
                progress = d["fragment_index"] / d["fragment_count"] * 100
            elif d.get("_percent_str"):
                try:
                    progress = float(d["_percent_str"].replace("%", "").strip())
                except ValueError:
                    progress = 0
            else:
                progress = 0

            download_tasks[task_id].update({
                "status": "downloading",
                "progress": round(progress, 1),
                "speed": _format_speed(speed),
                "eta": _format_eta(eta),
                "downloaded": downloaded,
                "total": total,
            })
        elif d["status"] == "finished":
            download_tasks[task_id].update({
                "status": "finished",
                "progress": 100,
                "speed": "",
                "eta": "00:00",
            })
    return hook


def _download_task(task_id: str, url: str, format_id: str, quality: str):
    """实际下载任务（在线程池中运行）"""
    try:
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)

        ydl_opts = {
            "outtmpl": os.path.join(DOWNLOAD_DIR, f"{task_id}_%(title).50s.%(ext)s"),
            "progress_hooks": [_progress_hook(task_id)],
            "merge_output_format": "mp4",
            "remux_video": "mp4",  # HLS/TS 等格式自动转封装为 MP4
        }

        is_youtube = "youtube.com" in url or "youtu.be" in url
        is_douyin = "douyin.com" in url or "tiktok.com" in url

        if is_youtube:
            # YouTube: 强制 H.264 + AAC，自动合并视频+音频
            ydl_opts["format"] = "bestvideo[vcodec^=avc1]+bestaudio[acodec^=mp4a]/bestvideo+bestaudio/best"
            ydl_opts["format_sort"] = ["vcodec:h264", "acodec:aac"]
        elif is_douyin:
            # 抖音: 用 best 让 yt-dlp 自动选（手动指定 format_id 容易因 CDN 问题失败）
            ydl_opts["format"] = "best"
        else:
            # 通用平台: 用前端传的 format_id，自动合并音视频
            format_str = format_id
            if "bestvideo" in format_id or format_id.startswith(("137", "248", "271", "313")):
                format_str = f"{format_id}+bestaudio/best"
            ydl_opts["format"] = format_str

        info = _try_extract_with_cookies(url, download=True, extra_opts=ydl_opts)

        title = info.get("title", "video")
        filename = None
        for f in os.listdir(DOWNLOAD_DIR):
            if f.startswith(task_id):
                filename = os.path.join(DOWNLOAD_DIR, f)
                break

        if not filename or not os.path.exists(filename):
            files = sorted(
                [os.path.join(DOWNLOAD_DIR, f) for f in os.listdir(DOWNLOAD_DIR)],
                key=os.path.getmtime,
                reverse=True,
            )
            filename = files[0] if files else ""

        file_size = os.path.getsize(filename) if filename and os.path.exists(filename) else 0

        download_tasks[task_id].update({
            "status": "completed",
            "progress": 100,
            "filename": os.path.basename(filename) if filename else "",
            "filepath": filename or "",
            "file_size": file_size,
            "title": info.get("title", ""),
        })

    except Exception as e:
        download_tasks[task_id].update({
            "status": "failed",
            "error": _format_error(url, e),
        })


def start_download(url: str, format_id: str, quality: str) -> str:
    """创建下载任务，返回 task_id"""
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

    executor.submit(_download_task, task_id, url, format_id, quality)
    return task_id


def get_task(task_id: str) -> dict | None:
    """获取任务状态"""
    return download_tasks.get(task_id)


def _format_speed(speed: float) -> str:
    if not speed:
        return ""
    if speed > 1024 * 1024:
        return f"{speed / 1024 / 1024:.1f} MB/s"
    return f"{speed / 1024:.1f} KB/s"


def _format_eta(eta: int) -> str:
    if not eta:
        return ""
    minutes, seconds = divmod(int(eta), 60)
    return f"{minutes:02d}:{seconds:02d}"
