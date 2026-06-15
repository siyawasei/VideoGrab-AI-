"""Bilibili 专用处理器 — 绕过 yt-dlp 的 412 反爬问题"""

import hashlib
import time
import urllib.request
import json
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com",
}

# 缓存解析结果（URL 有时效性，避免重复解析）
_info_cache: dict = {}
CACHE_TTL = 600  # 10 分钟


def _api_get(url: str, cookies: dict = None) -> dict:
    """发送 GET 请求到 Bilibili API"""
    headers = dict(HEADERS)
    if cookies:
        headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in cookies.items())
    req = urllib.request.Request(url, headers=headers)
    resp = urllib.request.urlopen(req, timeout=15)
    return json.loads(resp.read())


def _get_buvid() -> tuple:
    """获取 Bilibili 的 buvid 反爬指纹"""
    data = _api_get("https://api.bilibili.com/x/frontend/finger/spi")
    return data["data"]["b_3"], data["data"]["b_4"]


def _get_bili_ticket() -> str:
    """获取 bili_ticket（POST 请求）"""
    ts = int(time.time())
    sign_str = f"24d12fa04b644d05a340a5de5c61640a{ts}"
    sign = hashlib.md5(sign_str.encode()).hexdigest()
    url = f"https://api.bilibili.com/bapis/bilibili.api.ticket.v1.Ticket/GenWebTicket?key_id=ec02&hexsign={sign}&csrf=&choupei={ts}"
    req = urllib.request.Request(url, data=b"", headers=HEADERS)
    resp = urllib.request.urlopen(req, timeout=10)
    data = json.loads(resp.read())
    return data.get("data", {}).get("ticket", "")


def _extract_bvid(url: str) -> str:
    """从 URL 中提取 BV 号"""
    match = re.search(r"(BV[a-zA-Z0-9]+)", url)
    return match.group(1) if match else ""


def is_bilibili_url(url: str) -> bool:
    """判断是否为 Bilibili 链接"""
    return "bilibili.com" in url or "b23.tv" in url


def _load_sessdata() -> str:
    """从配置文件加载 Bilibili SESSDATA"""
    import os
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cookies", "bilibili_sessdata.txt")
    if os.path.exists(path):
        with open(path) as f:
            data = f.read().strip()
            if data:
                return data
    return ""


def bilibili_extract_info(url: str) -> dict:
    """直接通过 Bilibili API 解析视频信息（绕过 yt-dlp 的 412 问题）"""
    # 检查缓存
    bvid = _extract_bvid(url)
    if bvid and bvid in _info_cache:
        cached = _info_cache[bvid]
        if time.time() - cached["_cached_at"] < CACHE_TTL:
            return cached

    if not bvid:
        raise ValueError(f"无法从 URL 中提取 BV 号: {url}")

    # 获取 cookies
    buvid3, buvid4 = _get_buvid()
    try:
        ticket = _get_bili_ticket()
    except Exception:
        ticket = ""

    cookies = {
        "buvid3": buvid3,
        "buvid4": buvid4,
        "b_nut": str(int(time.time())),
    }
    if ticket:
        cookies["bili_ticket"] = ticket

    # 加载 SESSDATA（解锁高清画质）
    sessdata = _load_sessdata()
    if sessdata:
        cookies["SESSDATA"] = sessdata

    # 获取视频基本信息
    view_data = _api_get(
        f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}",
        cookies,
    )
    if view_data.get("code") != 0:
        raise Exception(f"B站 API 错误: {view_data.get('message', '未知错误')}")

    video = view_data["data"]
    cid = video["cid"]

    # 加载 SESSDATA（如果有）
    sessdata = cookies.get("SESSDATA", "")

    # 获取视频流地址（请求最高画质）
    play_data = _api_get(
        f"https://api.bilibili.com/x/player/wbi/playurl?bvid={bvid}&cid={cid}&qn=127&fnval=4048&fourk=1",
        cookies,
    )

    # B站画质 ID 映射
    quality_map = {
        127: "8K", 126: "Dolby", 125: "HDR", 120: "4K",
        116: "1080p60", 112: "1080p+", 80: "1080p", 74: "720p60",
        64: "720p", 48: "720p", 32: "480p", 16: "360p",
    }

    formats = []
    if play_data.get("code") == 0:
        dash = play_data.get("data", {}).get("dash", {})
        if dash:
            # DASH 视频流：按画质去重（每个画质只保留一个编码格式，优先 avc1）
            seen_quality = set()
            for v in dash.get("video", []):
                qid = v.get("id", 0)
                if qid in seen_quality:
                    continue
                # 优先 avc1 编码（兼容性最好）
                codecs = v.get("codecs", "")
                if not seen_quality or "avc1" in codecs:
                    seen_quality.add(qid)
                else:
                    # 如果还没选过这个画质，也接受其他编码
                    if qid not in seen_quality:
                        seen_quality.add(qid)

                h = v.get("height", 0)
                quality_label = quality_map.get(qid, f"{h}p" if h else str(qid))
                urls = [v.get("baseUrl") or v.get("base_url")]
                urls.extend(v.get("backup_url") or [])
                formats.append({
                    "format_id": str(qid),
                    "quality": quality_label,
                    "ext": "mp4",
                    "filesize": None,
                    "has_video": True,
                    "has_audio": False,
                    "fps": v.get("frameRate"),
                    "vcodec": codecs,
                    "acodec": "none",
                    "bandwidth": v.get("bandwidth"),
                    "video_url": urls[0],
                    "video_urls": urls,
                })

            # 音频流：选最佳音质
            best_audio = None
            for a in dash.get("audio", []):
                bw = a.get("bandwidth", 0)
                if not best_audio or bw > best_audio.get("bandwidth", 0):
                    best_audio = a
            if best_audio:
                urls = [best_audio.get("baseUrl") or best_audio.get("base_url")]
                urls.extend(best_audio.get("backup_url") or [])
                formats.append({
                    "format_id": str(best_audio.get("id", "")),
                    "quality": "audio",
                    "ext": "mp4",
                    "filesize": None,
                    "has_video": False,
                    "has_audio": True,
                    "fps": None,
                    "vcodec": "none",
                    "acodec": best_audio.get("codecs", ""),
                    "bandwidth": best_audio.get("bandwidth"),
                    "audio_url": urls[0],
                    "audio_urls": urls,
                })
        else:
            # 非 DASH 格式（较低画质）
            for d in play_data.get("data", {}).get("durl", []):
                formats.append({
                    "format_id": str(d.get("order", 1)),
                    "quality": "default",
                    "ext": "mp4",
                    "filesize": d.get("size"),
                    "has_video": True,
                    "has_audio": True,
                    "fps": None,
                    "vcodec": "",
                    "acodec": "",
                    "url": d.get("url"),
                })

    # 去重
    seen = set()
    unique_formats = []
    for f in formats:
        key = f"{f['quality']}_{f['has_video']}_{f['has_audio']}"
        if key not in seen:
            seen.add(key)
            unique_formats.append(f)

    # 按分辨率排序
    def sort_key(item):
        q = item["quality"]
        if q and "p" in q:
            try:
                return int(q.replace("p", ""))
            except ValueError:
                pass
        return 0
    unique_formats.sort(key=sort_key, reverse=True)

    result = {
        "title": video.get("title", "未知标题"),
        "thumbnail": video.get("pic", ""),
        "duration": video.get("duration", 0),
        "uploader": video.get("owner", {}).get("name", "未知"),
        "uploader_avatar": video.get("owner", {}).get("face", ""),
        "view_count": video.get("stat", {}).get("view", 0),
        "like_count": video.get("stat", {}).get("like", 0),
        "coin_count": video.get("stat", {}).get("coin", 0),
        "favorite_count": video.get("stat", {}).get("favorite", 0),
        "share_count": video.get("stat", {}).get("share", 0),
        "danmaku_count": video.get("stat", {}).get("danmaku", 0),
        "reply_count": video.get("stat", {}).get("reply", 0),
        "description": video.get("desc", ""),
        "platform": "BiliBili",
        "bvid": bvid,
        "cid": cid,
        "cookies": cookies,
        "formats": unique_formats,
    }

    # 写入缓存
    result["_cached_at"] = time.time()
    _info_cache[bvid] = result
    return result


def get_cached_info(bvid: str) -> dict | None:
    """获取缓存的视频信息（下载时使用，避免重复解析）"""
    if bvid in _info_cache:
        cached = _info_cache[bvid]
        if time.time() - cached.get("_cached_at", 0) < CACHE_TTL:
            return cached
    return None


def bilibili_download_stream(url: str, dest: str, cookies: dict, backup_urls: list = None) -> None:
    """下载 Bilibili 视频/音频流到本地文件，自动尝试备用 CDN"""
    headers = {
        "User-Agent": HEADERS["User-Agent"],
        "Referer": "https://www.bilibili.com",
        "Cookie": "; ".join(f"{k}={v}" for k, v in cookies.items()),
    }

    urls_to_try = [url] + (backup_urls or [])
    last_err = None

    for try_url in urls_to_try:
        try:
            req = urllib.request.Request(try_url, headers=headers)
            with urllib.request.urlopen(req, timeout=300) as resp, open(dest, "wb") as f:
                while True:
                    chunk = resp.read(1024 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)
            return  # 成功
        except Exception as e:
            last_err = e
            continue

    raise Exception(f"所有 CDN 节点下载失败: {last_err}")


def bilibili_merge_streams(video_path: str, audio_path: str, output_path: str) -> None:
    """用 ffmpeg 合并 Bilibili 的视频流和音频流"""
    import subprocess, shutil, os

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        # Windows 常见安装路径
        for path in [
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
            r"C:\ffmpeg\bin\ffmpeg.exe",
        ]:
            if os.path.exists(path):
                ffmpeg = path
                break
    if not ffmpeg:
        raise FileNotFoundError("ffmpeg 未找到，请确保已安装并添加到 PATH")

    cmd = [
        ffmpeg, "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "copy",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"ffmpeg 合并失败: {result.stderr[:200]}")


def bilibili_get_subtitle(bvid: str, cid: int, cookies: dict = None) -> dict | None:
    """获取 Bilibili 视频的字幕内容（用于 AI 总结）

    优先使用 /x/v2/dm/view API（不需要 SESSDATA），失败则回退到 /x/player/v2。

    Returns:
        {
            "segments": [{"from": 0.0, "to": 5.0, "content": "..."}],
            "text": "纯文本字幕",
            "language": "ai-zh",
        }
        无字幕时返回 None
    """
    if not cookies:
        cookies = {}
        buvid3, buvid4 = _get_buvid()
        cookies["buvid3"] = buvid3
        cookies["buvid4"] = buvid4
        sessdata = _load_sessdata()
        if sessdata:
            cookies["SESSDATA"] = sessdata

    # 方法 1: /x/v2/dm/view API（不需要 SESSDATA，优先使用）
    subtitle_list = []
    try:
        dm_data = _api_get(
            f"https://api.bilibili.com/x/v2/dm/view?type=1&oid={cid}&pid={cid}",
            cookies,
        )
        if dm_data.get("code") == 0:
            subtitle_list = dm_data.get("data", {}).get("subtitle", {}).get("subtitles", [])
    except Exception:
        pass

    # 方法 2: /x/player/v2 API（需要 SESSDATA，作为备用）
    if not subtitle_list:
        try:
            player_data = _api_get(
                f"https://api.bilibili.com/x/player/v2?bvid={bvid}&cid={cid}",
                cookies,
            )
            if player_data.get("code") == 0:
                subtitle_list = player_data.get("data", {}).get("subtitle", {}).get("subtitles", [])
        except Exception:
            pass

    if not subtitle_list:
        return None

    # 优先选择: ai-zh > zh-CN > zh > 第一个
    target = None
    for sub in subtitle_list:
        if sub.get("lan") == "ai-zh":
            target = sub
            break
    if not target:
        for sub in subtitle_list:
            if sub.get("lan") == "zh-CN":
                target = sub
                break
    if not target:
        for sub in subtitle_list:
            if sub.get("lan", "").startswith("zh"):
                target = sub
                break
    if not target:
        target = subtitle_list[0]

    subtitle_url = target.get("subtitle_url", "")
    if not subtitle_url:
        return None

    # 补全协议
    if subtitle_url.startswith("//"):
        subtitle_url = "https:" + subtitle_url
    elif subtitle_url.startswith("http://"):
        subtitle_url = subtitle_url.replace("http://", "https://")

    # 下载字幕 JSON
    try:
        headers = dict(HEADERS)
        req = urllib.request.Request(subtitle_url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=15)
        subtitle_data = json.loads(resp.read())
    except Exception:
        return None

    body = subtitle_data.get("body", [])
    if not body:
        return None

    segments = []
    text_parts = []
    for item in body:
        seg = {
            "from": item.get("from", 0.0),
            "to": item.get("to", 0.0),
            "content": item.get("content", ""),
        }
        segments.append(seg)
        text_parts.append(seg["content"])

    return {
        "segments": segments,
        "text": " ".join(text_parts),
        "language": target.get("lan", "unknown"),
    }
