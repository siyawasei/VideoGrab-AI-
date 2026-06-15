"""字幕获取统一接口 — 抽象不同平台的字幕获取逻辑"""

import json
import urllib.request

from api.bilibili import is_bilibili_url, bilibili_get_subtitle, _extract_bvid, _api_get, _load_sessdata, _get_buvid, _get_bili_ticket


def get_video_transcript(url: str) -> dict:
    """统一字幕获取入口，根据 URL 自动选择平台

    Returns:
        {
            "title": str,
            "transcript": str,              # 纯文本字幕（用于 LLM）
            "transcript_segments": list,     # 带时间戳的片段
            "source": str,                  # "subtitle" | "description"
            "language": str,
        }
    """
    if is_bilibili_url(url):
        return _get_bilibili_transcript(url)
    else:
        return _get_ytdlp_transcript(url)


def _get_bilibili_transcript(url: str) -> dict:
    """获取 Bilibili 视频字幕（复用 bilibili.py 基础设施）"""
    from api.bilibili import bilibili_extract_info, _load_sessdata

    # 先获取视频信息（包含 aid, cid, title, description）
    info = bilibili_extract_info(url)
    bvid = info.get("bvid", _extract_bvid(url))
    cid = info.get("cid")
    title = info.get("title", "")
    description = info.get("description", "")
    cookies = info.get("cookies", {})

    # 检查 SESSDATA 是否已配置
    has_sessdata = bool(_load_sessdata())

    # 尝试获取字幕
    subtitle = None
    if bvid and cid:
        subtitle = bilibili_get_subtitle(bvid, cid, cookies)

    if subtitle and subtitle.get("text"):
        return {
            "title": title,
            "transcript": subtitle["text"],
            "transcript_segments": subtitle.get("segments", []),
            "source": "subtitle",
            "language": subtitle.get("language", "unknown"),
        }

    # 无字幕时，使用标题+描述作为上下文
    sessdata_hint = ""
    if not has_sessdata:
        sessdata_hint = "\n\n提示：配置 B站 SESSDATA 后可获取完整字幕（点击右上角设置 → B站 SESSDATA）"
    return {
        "title": title,
        "transcript": f"视频标题：{title}\n视频描述：{description}{sessdata_hint}",
        "transcript_segments": [],
        "source": "description",
        "language": "zh",
        "has_sessdata": has_sessdata,
    }


def _get_ytdlp_transcript(url: str) -> dict:
    """通过 yt-dlp 获取字幕（不下载视频）"""
    import yt_dlp

    title = ""
    description = ""
    segments = []
    language = "unknown"

    # 第一步：获取元数据 + 字幕信息
    opts = {
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": ["zh-CN", "zh-Hans", "zh", "en", "en-US"],
    }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get("title", "")
            description = info.get("description", "")

            # 优先手动字幕，其次自动生成
            subtitles = info.get("subtitles", {})
            auto_captions = info.get("automatic_captions", {})

            # 按优先级查找字幕
            lang_priority = ["zh-CN", "zh-Hans", "zh", "en", "en-US"]
            subtitle_entries = None

            for lang in lang_priority:
                if lang in subtitles:
                    subtitle_entries = subtitles[lang]
                    language = lang
                    break
                if lang in auto_captions:
                    subtitle_entries = auto_captions[lang]
                    language = lang
                    break

            # 如果以上都没有，取第一个可用的
            if not subtitle_entries:
                for lang, entries in {**subtitles, **auto_captions}.items():
                    if entries:
                        subtitle_entries = entries
                        language = lang
                        break

            if subtitle_entries:
                # 优先 json3 格式（有时间戳），其次 vtt/srt
                json3_url = None
                vtt_url = None
                for entry in subtitle_entries:
                    ext = entry.get("ext", "")
                    if ext == "json3":
                        json3_url = entry.get("url")
                    elif ext == "vtt":
                        vtt_url = entry.get("url")

                if json3_url:
                    segments = _fetch_json3_subtitle(json3_url)
                elif vtt_url:
                    segments = _fetch_vtt_subtitle(vtt_url)
    except Exception:
        pass

    if segments:
        text = " ".join(seg["content"] for seg in segments if seg.get("content"))
        return {
            "title": title,
            "transcript": text,
            "transcript_segments": segments,
            "source": "subtitle",
            "language": language,
        }

    # 无字幕，使用标题+描述
    return {
        "title": title,
        "transcript": f"视频标题：{title}\n视频描述：{description}",
        "transcript_segments": [],
        "source": "description",
        "language": "zh",
    }


def _fetch_json3_subtitle(url: str) -> list:
    """下载并解析 YouTube json3 格式字幕"""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        })
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())

        segments = []
        for event in data.get("events", []):
            if "segs" not in event:
                continue
            text = "".join(seg.get("utf8", "") for seg in event["segs"]).strip()
            if not text or text == "\n":
                continue
            start_ms = event.get("tStartMs", 0)
            dur_ms = event.get("dDurationMs", 0)
            segments.append({
                "from": start_ms / 1000.0,
                "to": (start_ms + dur_ms) / 1000.0,
                "content": text,
            })
        return segments
    except Exception:
        return []


def _fetch_vtt_subtitle(url: str) -> list:
    """下载并解析 VTT 格式字幕"""
    import re
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        })
        resp = urllib.request.urlopen(req, timeout=15)
        content = resp.read().decode("utf-8", errors="ignore")

        segments = []
        # 解析 VTT 格式: HH:MM:SS.mmm --> HH:MM:SS.mmm
        pattern = re.compile(
            r"(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})\s*\n(.+?)(?:\n\n|\Z)",
            re.DOTALL,
        )
        for match in pattern.finditer(content):
            start = _vtt_time_to_seconds(match.group(1))
            end = _vtt_time_to_seconds(match.group(2))
            text = match.group(3).strip().replace("\n", " ")
            if text:
                segments.append({
                    "from": start,
                    "to": end,
                    "content": text,
                })
        return segments
    except Exception:
        return []


def _vtt_time_to_seconds(time_str: str) -> float:
    """将 VTT 时间格式 HH:MM:SS.mmm 转换为秒数"""
    parts = time_str.split(":")
    hours = int(parts[0])
    minutes = int(parts[1])
    sec_parts = parts[2].split(".")
    seconds = int(sec_parts[0])
    millis = int(sec_parts[1]) if len(sec_parts) > 1 else 0
    return hours * 3600 + minutes * 60 + seconds + millis / 1000.0
