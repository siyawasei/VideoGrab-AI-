# AI 视频内容总结功能 — 完整实施方案

## 一、竞品调研核心结论

### 调研对象
| 产品 | 定位 | 核心技术 | 开源 |
|------|------|---------|------|
| **BibGPT** (bibigpt.co) | 视频 AI 总结 | 字幕提取 + LLM | ✅ 6K⭐ |
| **NoteGPT** (notegpt.io) | 学习笔记 + 视频总结 | 转录 + LLM | ❌ |
| **VideoSeek** (videoseek.ai) | 视频快速总结 | 转录 + LLM | ❌ |
| **飞书妙记** (feishu.cn) | 会议录制 + AI 纪要 | ASR + LLM | ❌ |

### 关键发现
1. **技术门槛低**: 所有竞品核心都是「获取字幕/转录 → LLM 总结」，无自训练模型
2. **BibGPT 开源可参考**: 核心逻辑 = 字幕提取 + 6200字节截断 + 一个 LLM prompt
3. **我们有天然优势**: `bilibili.py` 已有 B站 API 处理器，`yt-dlp` 支持 1000+ 平台字幕
4. **差异化空间**: 总结 + 下载一站式体验，竞品都没有

### 技术决策
- **LLM**: DeepSeek API（`deepseek-v4-pro`，**1M 上下文**，OpenAI 兼容 SDK）
- **无字幕处理**: 平台字幕优先，无字幕用标题+描述兜底，**Whisper 后续再接入**
- **功能范围**: AI 摘要 + 章节时间线 + 关键要点 + **思维导图** + **AI 问答**
- **使用限制**: **全免费，无限制，无需登录**

---

## 二、整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端 (Vue 3 + Vite)                       │
│                                                                 │
│  ┌──────────────┐    ┌──────────────────────────────────────┐   │
│  │  HomeView    │───>│  DownloadModal.vue                    │   │
│  │  (现有)      │    │  ┌──────────────────────────────────┐ │   │
│  └──────────────┘    │  │  VideoSummary.vue (新增)         │ │   │
│                      │  │                                  │ │   │
│                      │  │  ┌────────┬──────────┬────────┐ │ │   │
│                      │  │  │📝 总结  │🧠 思维导图│💬 AI问答│ │ │   │
│                      │  │  │Tab 1   │Tab 2     │Tab 3   │ │ │   │
│                      │  │  └────────┴──────────┴────────┘ │ │   │
│                      │  └──────────────────────────────────┘ │   │
│                      └──────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  useAiSummary.js (新增 Composable)                       │   │
│  │  ├─ startSummary(url) → SSE 流式消费                      │   │
│  │  ├─ askQuestion(url, question) → SSE 流式消费              │   │
│  │  └─ summaryText / chatMessages (响应式状态)                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  api/index.js (扩展，不修改现有代码)                        │   │
│  │  ├─ 现有: getInfo, download, login, ...                   │   │
│  │  └─ 新增: summarizeVideo, aiChat (原生 fetch SSE)          │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────────┘
                               │ HTTP / SSE
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      后端 (FastAPI + Python)                      │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │  app.py      │  │  config.py   │  │  database.py         │   │
│  │  (扩展注册)   │  │  (扩展配置)   │  │  (现有，不动)         │   │
│  └──────┬───────┘  └──────────────┘  └──────────────────────┘   │
│         │                                                       │
│         ├── 现有路由 ──────────────────────────────────┐        │
│         │   ├─ auth_router   (api/auth.py)             │        │
│         │   ├─ download_router (api/routes.py)         │        │
│         │   └─ history_router (api/history.py)         │        │
│         │                                              │        │
│         └── 新增路由 ──────────────────────────────────┤        │
│             └─ ai_router (api/ai.py) ← 新建            │        │
│                 ├─ POST /api/summarize (SSE 流式)       │        │
│                 └─ POST /api/ai-chat   (SSE 流式)       │        │
│                                                          │        │
│  ┌─────────────────────────────────────────────────────┐ │        │
│  │  api/subtitle.py (新建 — 字幕获取统一接口)             │ │        │
│  │                                                     │ │        │
│  │  get_video_transcript(url) → dict                   │ │        │
│  │     ├─ B站: /x/player/v2 → subtitle JSON            │ │        │
│  │     │   (复用 bilibili.py 的 _api_get 等基础设施)     │ │        │
│  │     ├─ YouTube/其他: yt-dlp --write-auto-sub         │ │        │
│  │     └─ 兜底: title + description + tags              │ │        │
│  └─────────────────────────────────────────────────────┘ │        │
│                                                          │        │
│  ┌─────────────────────────────────────────────────────┐ │        │
│  │  LLM 调用层 (ai.py 内部)                            │ │        │
│  │                                                     │ │        │
│  │  DeepSeek API (OpenAI 兼容 SDK)                     │ │        │
│  │  ├─ model: deepseek-v4-pro                          │ │        │
│  │  ├─ base_url: https://api.deepseek.com              │ │        │
│  │  ├─ stream: true → SSE 流式输出                      │ │        │
│  │  └─ 1M 上下文 → 无需截断字幕                         │ │        │
│  └─────────────────────────────────────────────────────┘ │        │
│                                                            │        │
│  ┌──────────────────────────────────────────────────────┐ │        │
│  │  现有模块 (不修改)                                     │ │        │
│  │  ├─ api/bilibili.py  (B站专用处理器)                   │ │        │
│  │  ├─ api/downloader.py (yt-dlp 封装)                   │ │        │
│  │  ├─ api/auth.py      (JWT 认证)                       │ │        │
│  │  ├─ api/history.py   (下载历史)                        │ │        │
│  │  ├─ models.py        (数据模型)                        │ │        │
│  │  └─ database.py      (数据库连接)                      │ │        │
│  └──────────────────────────────────────────────────────┘ │        │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                        外部服务                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ DeepSeek API    │  │ Bilibili API    │  │ yt-dlp          │ │
│  │ (LLM 总结/问答)  │  │ (字幕获取)      │  │ (字幕获取)       │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 数据流图

```
用户粘贴 URL
     │
     ▼
 POST /api/info ──→ 视频元数据 (title, thumbnail, formats...)
     │
     ▼
 DownloadModal 显示视频信息
     │
     ├─ 用户点击「AI 总结」Tab
     │       │
     │       ▼
     │  POST /api/summarize ──→ subtitle.py 获取字幕
     │       │                        │
     │       │                   ┌────┴────┐
     │       │                   │ B站API   │ yt-dlp
     │       │                   └────┬────┘
     │       │                        │
     │       │                   字幕文本 + 时间戳
     │       │                        │
     │       ▼                        ▼
     │  ai.py 构建 prompt ──→ DeepSeek API (stream=True)
     │       │
     │       ▼
     │  SSE 流式返回 ──→ VideoSummary Tab 1 (Markdown 渲染)
     │                    VideoSummary Tab 2 (Mermaid 思维导图)
     │
     └─ 用户在「AI 问答」Tab 输入问题
             │
             ▼
        POST /api/ai-chat ──→ subtitle.py 获取字幕 (可缓存)
             │
             ▼
        ai.py 构建问答 prompt ──→ DeepSeek API (stream=True)
             │
             ▼
        SSE 流式返回 ──→ VideoSummary Tab 3 (对话渲染)
```

---

## 三、新增/修改文件清单

### 新增文件 (开闭原则 — 只新增，不修改现有文件核心逻辑)

| 文件 | 类型 | 说明 |
|------|------|------|
| `backend/api/subtitle.py` | 新建 | 字幕获取统一接口 |
| `backend/api/ai.py` | 新建 | AI 总结 + AI 问答 API 路由 |
| `frontend/src/components/VideoSummary.vue` | 新建 | AI 总结展示组件 (3个Tab) |
| `frontend/src/composables/useAiSummary.js` | 新建 | AI 总结 composable |

### 仅扩展注册，不修改现有逻辑

| 文件 | 改动 | 说明 |
|------|------|------|
| `backend/app.py` | +2行 | 新增 `ai_router` 注册 (不影响现有路由) |
| `backend/config.py` | +5行 | 新增 DeepSeek 配置常量 (不影响现有配置) |
| `backend/api/bilibili.py` | +30行 | 新增 `bilibili_get_subtitle()` 函数 (不影响现有函数) |
| `frontend/src/api/index.js` | +5行 | 新增 API 方法 (不影响现有方法) |
| `frontend/src/components/DownloadModal.vue` | +15行 | 新增「AI 总结」按钮和 Tab (不影响现有 UI) |

---

## 四、技术栈与依赖

### 后端新增依赖
```bash
pip install openai    # DeepSeek 兼容 OpenAI SDK
```

### 前端新增依赖
```bash
cd frontend
npm install mermaid   # 思维导图渲染 (mindmap 类型)
npm install marked    # Markdown 渲染
```

### API 文档参考 (Context7 获取的最新文档)
- **DeepSeek API**: `model="deepseek-v4-pro"`, `base_url="https://api.deepseek.com"`, OpenAI 兼容
- **Mermaid**: `mermaid.initialize({ startOnLoad: false })` + `mermaid.render('id', definition)` 动态渲染
- **Marked**: `import { marked } from 'marked'` + `marked.parse(markdown)` 渲染

---

## 五、开发步骤

### Step 1: config.py — 新增 DeepSeek 配置
### Step 2: subtitle.py — 字幕获取统一接口
### Step 3: bilibili.py — 新增字幕获取函数
### Step 4: ai.py — AI 总结 + AI 问答 API
### Step 5: app.py — 注册 ai_router
### Step 6: 前端 api/index.js — 新增 API 方法
### Step 7: 前端 useAiSummary.js — SSE 消费 composable
### Step 8: 前端 VideoSummary.vue — 3 Tab 组件
### Step 9: 前端 DownloadModal.vue — 集成入口
### Step 10: 依赖安装 + 端到端测试

---

## 六、验证方案

1. **B站视频 (有字幕)**: 粘贴 B站 URL → 解析 → AI 总结 → 流式输出结构化总结
2. **思维导图**: 切换到「思维导图」Tab → Mermaid 渲染知识图谱
3. **AI 问答**: 输入关于视频内容的问题 → 流式返回答案
4. **YouTube 视频**: 粘贴 YouTube URL → 同上流程
5. **无字幕视频**: 粘贴无字幕短视频 → 基于标题+描述生成简单总结
6. **流式效果**: 文本逐字/逐句出现，非一次性加载
7. **现有功能不受影响**: 下载、登录、历史记录等现有功能正常工作

---

*方案确认后开始按步骤实施。*
