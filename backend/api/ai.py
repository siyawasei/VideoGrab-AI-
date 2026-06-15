"""AI 视频总结 & 问答 API — 基于 DeepSeek 大模型"""

import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import OpenAI

from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
from api.subtitle import get_video_transcript

router = APIRouter(prefix="/api", tags=["ai"])

# DeepSeek 客户端（延迟初始化）
_client: OpenAI | None = None


def _get_client() -> OpenAI:
    """获取 DeepSeek API 客户端"""
    global _client
    if _client is None:
        if not DEEPSEEK_API_KEY:
            raise HTTPException(status_code=500, detail="DeepSeek API Key 未配置，请在环境变量 DEEPSEEK_API_KEY 中设置")
        _client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
        )
    return _client


# ── 请求模型 ──────────────────────────────────────────────────

class SummarizeRequest(BaseModel):
    url: str


class AiChatRequest(BaseModel):
    url: str
    question: str
    history: list = []  # [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]


# ── Prompt 模板 ────────────────────────────────────────────────

SUMMARY_SYSTEM_PROMPT = """你是一位专业的视频内容分析师。请根据视频信息和字幕内容，生成结构化的内容总结。

输出格式要求：
## 📝 内容摘要
（用 2-3 句话概括视频核心内容）

## 📑 章节时间线
（根据内容自动划分章节，标注时间点，每个章节用 1-2 句话描述）
- [MM:SS] 章节标题：简要描述

## 💡 关键要点
- 要点 1（简明扼要）
- 要点 2
- 要点 3
（提取 3-7 个核心要点）

## 🏷️ 标签
标签1, 标案2, 标签3

## 🧠 思维导图
（请用 Mermaid mindmap 语法生成思维导图，中心主题为视频标题）
```mermaid
mindmap
  root((视频标题))
    分支1
      子节点1
      子节点2
    分支2
      子节点3
```

注意：
- 使用中文输出
- 字幕中的错别字请自动纠正
- 章节时间线必须基于字幕中的实际时间戳（如有）
- 要点应简洁有力，适合快速浏览
- 思维导图的 mermaid 代码块必须完整且可渲染"""

CHAT_SYSTEM_PROMPT_TEMPLATE = """你是一位专业的视频内容分析师。用户正在观看一个视频，以下是视频的完整信息。
请基于视频内容回答用户的问题。如果问题超出视频内容范围，请如实告知并尽量提供有用的建议。

视频信息：
标题：{title}
作者：{uploader}

视频字幕/转录文本：
{transcript}

回答要求：
- 使用中文回答
- 引用视频中的具体内容来支持你的回答
- 回答要结构化，适当使用 Markdown 格式"""


# ── 字幕缓存 ──────────────────────────────────────────────────

_transcript_cache: dict = {}
TRANSCRIPT_CACHE_TTL = 600  # 10 分钟


def _get_cached_transcript(url: str) -> dict:
    """获取缓存的字幕（避免重复请求）"""
    import time
    cached = _transcript_cache.get(url)
    if cached and time.time() - cached["_cached_at"] < TRANSCRIPT_CACHE_TTL:
        return cached
    transcript_data = get_video_transcript(url)
    transcript_data["_cached_at"] = time.time()
    _transcript_cache[url] = transcript_data
    return transcript_data


# ── API 路由 ──────────────────────────────────────────────────

@router.post("/transcript")
async def get_transcript(req: SummarizeRequest):
    """获取视频字幕/转录文本（不调用 LLM，直接返回字幕数据）"""
    try:
        transcript_data = _get_cached_transcript(req.url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"获取视频信息失败: {str(e)}")

    return {
        "code": 0,
        "data": {
            "title": transcript_data.get("title", ""),
            "transcript": transcript_data.get("transcript", ""),
            "segments": transcript_data.get("transcript_segments", []),
            "source": transcript_data.get("source", "unknown"),
            "language": transcript_data.get("language", "unknown"),
            "has_sessdata": transcript_data.get("has_sessdata", True),
        },
    }


@router.post("/summarize")
async def summarize_video(req: SummarizeRequest):
    """AI 总结视频内容（流式 SSE 输出）

    获取视频字幕 → 构建 prompt → 调用 DeepSeek → 流式返回总结
    """
    try:
        transcript_data = _get_cached_transcript(req.url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"获取视频信息失败: {str(e)}")

    title = transcript_data.get("title", "未知视频")
    transcript = transcript_data.get("transcript", "")
    source = transcript_data.get("source", "unknown")

    if not transcript:
        raise HTTPException(status_code=400, detail="无法获取视频内容，请检查 URL 是否正确")

    # 构建用户消息
    user_content = f"""请总结以下视频内容：

视频标题：{title}
字幕来源：{"平台字幕" if source == "subtitle" else "视频描述（无字幕）"}

字幕/转录文本：
{transcript}"""

    async def stream_generator():
        """SSE 流式生成器"""
        try:
            client = _get_client()
            stream = client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                stream=True,
                max_tokens=4096,
                temperature=0.3,
            )

            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"

            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/ai-chat")
async def ai_chat(req: AiChatRequest):
    """基于视频内容的 AI 问答（流式 SSE 输出）

    用户输入问题 → 构建带上下文的 prompt → 调用 DeepSeek → 流式返回回答
    """
    try:
        transcript_data = _get_cached_transcript(req.url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"获取视频信息失败: {str(e)}")

    title = transcript_data.get("title", "未知视频")
    transcript = transcript_data.get("transcript", "")
    uploader = transcript_data.get("title", "").split(" - ")[0] if " - " in transcript_data.get("title", "") else ""

    # 构建系统 prompt
    system_prompt = CHAT_SYSTEM_PROMPT_TEMPLATE.format(
        title=title,
        uploader=uploader,
        transcript=transcript[:50000],  # 限制长度，避免超出上下文
    )

    # 构建消息历史
    messages = [{"role": "system", "content": system_prompt}]
    # 加入对话历史（最多保留最近 10 轮）
    for msg in req.history[-20:]:
        if msg.get("role") in ("user", "assistant") and msg.get("content"):
            messages.append({"role": msg["role"], "content": msg["content"]})
    # 加入当前问题
    messages.append({"role": "user", "content": req.question})

    async def stream_generator():
        """SSE 流式生成器"""
        try:
            client = _get_client()
            stream = client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=messages,
                stream=True,
                max_tokens=2048,
                temperature=0.5,
            )

            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"

            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
