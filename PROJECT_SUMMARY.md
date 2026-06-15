# VideoGrab - 万能视频下载器

一个基于 yt-dlp + FastAPI + Vue 3 的在线视频下载工具，支持国内主流平台，清爽极简白底 UI。集成 AI 视频总结、字幕提取、思维导图等功能。

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | Vue 3 + Vite + Tailwind CSS 4 + Pinia + Vue Router |
| 后端 | Python FastAPI + yt-dlp 2026.06.09 |
| 数据库 | MySQL 8 (localhost:3306) |
| AI 大模型 | DeepSeek API (deepseek-chat) |
| 实时进度 | Server-Sent Events (SSE) |
| 视频处理 | ffmpeg（音视频合并、TS→MP4 转封装） |

## 功能架构图

### 整体系统架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            用户浏览器/手机                                │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    Vue 3 + Tailwind CSS 前端                       │  │
│  │                                                                    │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐  │  │
│  │  │ 导航栏    │ │ 首屏输入  │ │ 解析弹窗  │ │ 进度面板  │ │ 定价区  │  │  │
│  │  │ 登录/注册 │ │ URL粘贴  │ │ 画质选择  │ │ SSE实时  │ │ 会员套餐│  │  │
│  │  │ Cookies  │ │ 解析按钮  │ │ 视频信息  │ │ 文件保存  │ │        │  │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └────────┘  │  │
│  └──────────────────────────┬────────────────────────────────────────┘  │
│                             │ Axios HTTP / SSE                          │
│  ┌──────────────────────────▼────────────────────────────────────────┐  │
│  │                    FastAPI 后端 (端口 8000)                        │  │
│  │                                                                    │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐  │  │
│  │  │ /api/info    │ │ /api/download│ │/api/progress│ │ /api/auth   │  │  │
│  │  │ 解析视频信息 │ │ 触发下载     │ │ SSE进度推送  │ │ 登录/注册   │  │  │
│  │  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └─────────────┘  │  │
│  │         │               │               │                          │  │
│  │  ┌──────▼───────────────▼───────────────▼──────────────────────┐   │  │
│  │  │                   路由分发层 (routes.py)                      │   │  │
│  │  │    URL规范化 → 平台检测 → 路由到对应处理器                    │   │  │
│  │  └──────┬───────────────┬──────────────────────────────────────┘   │  │
│  │         │               │                                          │  │
│  │  ┌──────▼──────┐ ┌──────▼──────────────────────────────────────┐   │  │
│  │  │ B站专用处理器 │ │          yt-dlp 通用处理器                   │   │  │
│  │  │ bilibili.py │ │          downloader.py                       │   │  │
│  │  │             │ │                                              │   │  │
│  │  │ ·buvid指纹  │ │ ·URL规范化(短链/精选页/YouTube)              │   │  │
│  │  │ ·WBI签名    │ │ ·平台智能检测(cookies/broken/drm)            │   │  │
│  │  │ ·DASH流下载  │ │ ·格式去重+排序                              │   │  │
│  │  │ ·CDN备用    │ │ ·H.264+AAC优先(YouTube)                    │   │  │
│  │  │ ·ffmpeg合并  │ │ ·HLS→MP4转封装(芒果TV)                     │   │  │
│  │  │ ·SESSDATA   │ │ ·progress_hooks进度回调                     │   │  │
│  │  └──────┬──────┘ └──────┬──────────────────────────────────────┘   │  │
│  │         │               │                                          │  │
│  │  ┌──────▼───────────────▼──────────────────────────────────────┐   │  │
│  │  │              数据存储层                                       │   │  │
│  │  │  ┌─────────┐  ┌─────────────┐  ┌──────────────────────┐    │   │  │
│  │  │  │ MySQL   │  │ 文件系统     │  │ 内存                  │    │   │  │
│  │  │  │ users   │  │ downloads/  │  │ download_tasks{}      │    │   │  │
│  │  │  │ history │  │ cookies/    │  │ _info_cache{}         │    │   │  │
│  │  │  │ orders  │  │             │  │ platform_config{}     │    │   │  │
│  │  │  └─────────┘  └─────────────┘  └──────────────────────┘    │   │  │
│  │  └─────────────────────────────────────────────────────────────┘   │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                              │                                           │
└──────────────────────────────┼───────────────────────────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
   ┌────▼────┐           ┌────▼────┐           ┌────▼────┐
   │  B站API  │           │  yt-dlp │           │  ffmpeg │
   │ 独立调用 │           │ 1800+平台│           │ 音视频  │
   │ 绕过反爬 │           │ 解析/下载│           │ 合并/转 │
   └─────────┘           └─────────┘           └─────────┘
```

### 视频下载流程

```
用户粘贴URL
    │
    ▼
┌─────────────────────┐
│   URL 规范化          │  抖音短链→重定向
│   normalize_url()    │  精选页→提取ID
│                      │  YouTube→展开
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐     ┌──────────────┐
│   平台检测            │────→│ B站URL?      │
│   is_bilibili_url()  │     │ 是 → B站处理器│
└──────────┬──────────┘     └──────────────┘
           │ 否
           ▼
┌─────────────────────┐
│   yt-dlp 解析         │
│   extract_info()     │
│                      │
│   第1次: 无cookie     │
│   第2次: 上传的cookie  │
│   第3次: 浏览器cookie  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   格式处理            │  去重(按分辨率)
│                      │  排序(高→低)
│   YouTube: H.264优先  │  检测0 formats
│   抖音: 去CDN变体      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   前端展示            │  封面/标题/UP主
│   DownloadModal      │  播放量/弹幕/描述
│                      │  画质选择列表
└──────────┬──────────┘
           │ 用户选择画质
           ▼
┌─────────────────────┐
│   创建下载任务        │
│   start_download()   │
│                      │
│   任务存入内存:       │
│   download_tasks{}   │
└──────────┬──────────┘
           │
     ┌─────┴─────┐
     │           │
     ▼           ▼
┌─────────┐ ┌─────────┐
│  B站下载  │ │ 通用下载  │
│         │ │         │
│ DASH:   │ │ YouTube:│
│ 视频流   │ │ best+   │
│ +音频流  │ │ bestaudio│
│ 并发下载  │ │         │
│ CDN备用  │ │ 抖音:   │
│ ffmpeg  │ │ best    │
│ 合并MP4  │ │         │
│         │ │ 芒果TV: │
│         │ │ HLS+remux│
└────┬────┘ └────┬────┘
     │           │
     └─────┬─────┘
           │
           ▼
┌─────────────────────┐
│   SSE 进度推送        │
│                      │
│   字节进度:           │
│   downloaded/total   │
│                      │
│   HLS分片进度:        │
│   frag_idx/count     │
│                      │
│   百分比字符串回退:    │
│   _percent_str       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   下载完成            │
│                      │
│   → 文件存入downloads/│
│   → 记录到MySQL       │
│   → 前端显示"保存文件" │
│   → 用户点击下载到本地 │
└─────────────────────┘
```

### B站专用处理器架构

```
B站 URL (bilibili.com / b23.tv)
    │
    ▼
┌─────────────────────────────────┐
│   bilibili_extract_info()       │
│                                 │
│   1. 获取 buvid 指纹            │
│      /x/frontend/finger/spi     │
│                                 │
│   2. 获取 bili_ticket            │
│      /bapis/.../GenWebTicket    │
│                                 │
│   3. 加载 SESSDATA (可选)       │
│      cookies/bilibili_sessdata  │
│                                 │
│   4. 获取视频详情                │
│      /x/web-interface/view      │
│      → 标题/封面/UP主/播放量     │
│                                 │
│   5. 获取 DASH 流地址            │
│      /x/player/wbi/playurl      │
│      → 视频流 + 音频流 + 备用URL │
│                                 │
│   6. 画质去重 (每个分辨率一个)   │
│      优先 H.264 编码             │
│                                 │
│   7. 结果缓存 (10分钟)          │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│   B站下载任务                     │
│                                 │
│   1. 获取最新流URL (不用缓存)    │
│                                 │
│   2. 并发下载:                   │
│      ┌─────────┐ ┌─────────┐   │
│      │ 视频流   │ │ 音频流   │   │
│      │ (m4s)   │ │ (m4s)   │   │
│      └────┬────┘ └────┬────┘   │
│           │ 失败?      │ 失败?   │
│           ▼           ▼        │
│      备用CDN-1    备用CDN-1     │
│      备用CDN-2    备用CDN-2     │
│                                 │
│   3. ffmpeg 合并:               │
│      video.m4s + audio.m4s     │
│      → output.mp4              │
│                                 │
│   4. 清理临时 .m4s 文件         │
└─────────────────────────────────┘
```

### 支持平台决策树

```
用户输入 URL
    │
    ├─ bilibili.com / b23.tv ──→ ✅ B站专用处理器 (直接可用)
    │
    ├─ youku.com ────────────→ ✅ yt-dlp (直接可用)
    │
    ├─ acfun.cn ─────────────→ ✅ yt-dlp (直接可用)
    │
    ├─ douyin.com ───────────→ ✅ yt-dlp (大部分可用)
    │   ├─ 短链 v.douyin.com ─→ 自动重定向
    │   └─ 精选页 jingxuan ───→ 自动提取 modal_id
    │
    ├─ mgtv.com ─────────────→ ✅ yt-dlp (免费视频可用)
    │                           ⚠️ VIP视频需登录
    │
    ├─ ixigua.com ───────────→ ⚠️ 需上传 cookies
    │
    ├─ v.qq.com ─────────────→ 🟠 CDN限速 (能解析，下载极慢)
    │
    ├─ iqiyi.com ────────────→ ❌ yt-dlp extractor 过时
    │
    ├─ weibo.com ────────────→ ❌ yt-dlp extractor 过时
    │
    ├─ kuaishou.com ─────────→ ❌ yt-dlp 无 extractor
    │
    ├─ xiaohongshu.com ──────→ ❌ extractor 失效
    │
    ├─ youtube.com ──────────→ ✅ 需梯子 + cookies(推荐)
    │
    └─ 其他 1800+ 平台 ──────→ ✅ yt-dlp 通用支持 (需测试)
```

## 功能特性

### 核心功能
- 视频链接解析（支持 1800+ 平台）
- 多画质选择（8K/4K/1080p/720p/480p/360p）
- 实时下载进度（SSE 推送）
- 音视频自动合并（DASH 格式）
- TS→MP4 自动转封装（HLS 格式）
- 下载完成后直接保存文件

### AI 智能功能（v2.0 新增）
- AI 视频内容总结（DeepSeek 大模型，流式输出）
- 自动章节时间线划分（带时间戳）
- 关键要点提取（3-7 个核心知识点）
- 思维导图生成（Mermaid mindmap，支持全屏+SVG/PNG下载）
- AI 问答对话（基于视频内容的多轮对话）
- 字幕自动获取与下载（B站 `/x/v2/dm/view` API，无需 SESSDATA）
- SRT 字幕文件导出

### 平台支持
- B站专用 API 处理器（绕过 412 反爬）
- 抖音链接自动规范化（短链/精选页/标准链接）
- YouTube H.264+AAC 兼容性优化
- 芒果TV HLS 下载 + ffmpeg 转封装
- CDN 备用节点自动切换

### 用户系统
- 注册/登录（JWT 认证）
- 下载历史记录
- 会员套餐展示（免费/Pro/Premium）
- Cookies 上传（解锁更多平台）
- B站 SESSDATA 配置（解锁高清画质）

### 用户系统
- 注册/登录（JWT 认证，支持邮箱登录）
- 下载历史记录
- 会员套餐展示（免费/Pro/Premium）
- Cookies 上传（解锁更多平台）
- B站 SESSDATA 配置（解锁高清画质）

### UI 设计（v2.0 重新设计）
- 清爽极简白底设计（#f8fafc 浅灰背景）
- 深蓝主色（#2563eb）+ 翠绿强调（#10b981）
- 双栏弹窗布局（左栏视频信息+下载，右栏 AI 总结）
- 移动端底部弹出式弹窗
- 响应式布局（手机/平板/电脑）
- 视频信息丰富展示（封面/UP主/播放量/弹幕/描述）
- 平台状态实时指示灯

### SEO 优化（v2.0 新增）
- robots.txt + sitemap.xml
- Open Graph + Twitter Card 标签
- JSON-LD 结构化数据（WebSite + WebApplication）
- 静态 HTML 内容页（/features, /faq，可被搜索引擎直接索引）
- FAQ 页含 FAQPage schema（搜索结果富片段）
- OG 预览图（SVG 格式）

### 部署架构
- 前后端统一端口（FastAPI 服务 Vue 构建产物，单端口 8000）
- SPA 兜底路由（Vue Router HTML5 history mode）
- 静态资源带 hash 缓存

## 支持平台

| 平台 | 状态 | 最高画质 | 说明 |
|------|------|----------|------|
| B站 | ✅ 可用 | 480p（未登录）/ 8K（有SESSDATA） | 自定义 API 处理器 |
| 优酷 | ✅ 可用 | 720p | yt-dlp 直接支持 |
| AcFun | ✅ 可用 | 多画质 | yt-dlp 直接支持 |
| 抖音 | ✅ 可用 | 720p | yt-dlp，部分需 cookies |
| 芒果TV | ✅ 可用 | 720p | 免费视频可用，VIP 需登录 |
| 西瓜视频 | ⚠️ 需 cookies | — | 上传 cookies 后可用 |
| 腾讯视频 | 🟠 CDN 限速 | — | 能解析，下载极慢 |
| 爱奇艺 | ❌ 不可用 | — | yt-dlp extractor 过时 |
| 微博 | ❌ 不可用 | — | yt-dlp extractor 过时 |
| 快手 | ❌ 不可用 | — | yt-dlp 无 extractor |
| 小红书 | ❌ 不可用 | — | extractor 失效 |

## 项目结构

```
AI_video/
├── backend/
│   ├── app.py                  # FastAPI 主入口（前后端统一端口）
│   ├── config.py               # 配置（数据库、JWT、DeepSeek、路径）
│   ├── database.py             # SQLAlchemy 连接
│   ├── models.py               # 数据模型（users/download_history/orders）
│   ├── requirements.txt        # Python 依赖
│   ├── api/
│   │   ├── auth.py             # 认证 API（注册/登录/JWT/邮箱登录）
│   │   ├── bilibili.py         # B站专用处理器（API解析+DASH下载+CDN备用+字幕获取）
│   │   ├── downloader.py       # yt-dlp 封装（平台检测+URL规范化+格式处理）
│   │   ├── history.py          # 下载历史 API
│   │   ├── routes.py           # 主路由（解析/下载/SSE进度/文件获取/Cookie/平台状态）
│   │   ├── ai.py               # AI 总结+问答 API（DeepSeek SSE 流式）
│   │   └── subtitle.py         # 字幕获取统一接口（B站API+yt-dlp+兜底）
│   ├── cookies/                # cookies 存储目录
│   └── downloads/              # 视频下载临时目录
│
├── frontend/
│   ├── public/
│   │   ├── favicon.ico         # 网站图标
│   │   ├── favicon.svg         # SVG 网站图标
│   │   ├── og-image.svg        # OG 预览图
│   │   ├── robots.txt          # 爬虫规则
│   │   ├── sitemap.xml         # 站点地图
│   │   ├── features.html       # 功能介绍页（SEO 静态页）
│   │   └── faq.html            # FAQ 页（SEO 静态页 + FAQ 富片段）
│   ├── src/
│   │   ├── App.vue             # 根组件
│   │   ├── main.js             # 入口
│   │   ├── api/index.js        # Axios + fetch SSE API 封装
│   │   ├── assets/main.css     # Tailwind + 自定义样式（极简白主题）
│   │   ├── components/
│   │   │   ├── Navbar.vue          # 导航栏
│   │   │   ├── HeroSection.vue     # 首屏输入区
│   │   │   ├── DownloadModal.vue   # 视频信息+下载弹窗（双栏布局）
│   │   │   ├── VideoSummary.vue    # AI 总结组件（4Tab: 总结/导图/字幕/问答）
│   │   │   ├── ProgressPanel.vue   # 下载进度
│   │   │   ├── FeaturesSection.vue # 功能特性
│   │   │   ├── StepsSection.vue    # 使用步骤
│   │   │   ├── PricingSection.vue  # 定价
│   │   │   ├── PlatformsSection.vue # 平台状态
│   │   │   ├── FooterSection.vue   # 页脚
│   │   │   └── LoginModal.vue      # 登录/注册弹窗
│   │   ├── composables/
│   │   │   ├── useDownloader.js    # 下载逻辑
│   │   │   └── useAiSummary.js     # AI 总结逻辑（SSE 消费+状态管理）
│   │   ├── router/index.js     # Vue Router
│   │   ├── stores/user.js      # Pinia 状态管理
│   │   └── views/              # 页面视图
│   ├── index.html              # HTML 入口（SEO meta/OG/JSON-LD）
│   ├── vite.config.js
│   └── package.json
│
├── README.md                   # 项目说明
├── ISSUES_AND_FIXES.md         # 问题记录
└── PROJECT_SUMMARY.md          # 本文档
```

## 快速启动

### 1. 安装依赖
```bash
# 后端
cd backend
pip install -r requirements.txt

# 前端
cd frontend
npm install
```

### 2. 配置 MySQL
```sql
CREATE DATABASE video_downloader CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
```

### 3. 启动服务
```bash
# 构建前端（只需一次）
cd frontend && npm run build

# 启动后端（前后端统一端口 8000）
cd backend && python app.py
```

### 4. 访问
浏览器打开 `http://localhost:8000`

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/auth/register` | POST | 用户注册（用户名+邮箱+密码） |
| `/api/auth/login` | POST | 用户登录（支持用户名或邮箱） |
| `/api/auth/me` | GET | 获取当前用户信息 |
| `/api/info` | POST | 解析视频信息 |
| `/api/download` | POST | 开始下载 |
| `/api/progress/{task_id}` | GET | SSE 下载进度 |
| `/api/file/{task_id}` | GET | 获取下载文件 |
| `/api/history` | GET | 下载历史 |
| `/api/platforms` | GET | 平台状态列表 |
| `/api/cookies/upload` | POST | 上传 cookies.txt |
| `/api/cookies/status` | GET | cookies 状态 |
| `/api/bilibili/sessdata` | POST/GET | B站 SESSDATA 配置 |
| `/api/summarize` | POST | AI 视频总结（SSE 流式） |
| `/api/ai-chat` | POST | AI 问答（SSE 流式） |
| `/api/transcript` | POST | 获取视频字幕/转录文本 |

## SEO 页面

| 路径 | 说明 |
|------|------|
| `/features` | 功能介绍页（纯 HTML，搜索引擎可直接索引） |
| `/faq` | FAQ 页（含 FAQPage JSON-LD，搜索结果富片段） |
| `/robots.txt` | 爬虫规则 |
| `/sitemap.xml` | 站点地图（3 个 URL） |

## 技术亮点

### 1. B站反爬绕过
直接调用 B站 API（`/x/web-interface/view` + `/x/player/wbi/playurl`），通过 buvid 指纹 + bili_ticket 绕过 WBI 签名反爬，支持 CDN 备用节点自动切换。

### 2. URL 智能规范化
`normalize_url()` 函数自动处理多种链接格式：
- 抖音短链（`v.douyin.com`）→ 跟随重定向
- 抖音精选页（`jingxuan?modal_id=`）→ 提取视频 ID
- YouTube 缩短链接（`youtu.be`）→ 展开
- B站短链（`b23.tv`）→ 跟随重定向

### 3. 多平台下载策略
- B站：DASH 并发下载 + ffmpeg 合并 + CDN 备用
- YouTube：强制 H.264+AAC 编码 + 自动合并
- 抖音：`format: best` 自动选择 + CDN 重试
- 芒果TV：HLS 下载 + `remux_video: mp4` 转封装

### 4. SSE 实时进度
通过 Server-Sent Events 实时推送下载进度，支持三种进度计算方式：
- 字节进度（普通下载）
- 分片进度（HLS 下载）
- 百分比字符串（回退）

### 5. AI 视频总结（v2.0）
- 字幕获取：B站通过 `/x/v2/dm/view` API（无需 SESSDATA），其他平台通过 yt-dlp
- LLM 调用：DeepSeek API（1M 上下文，OpenAI 兼容 SDK，流式输出）
- 思维导图：LLM 生成 Mermaid mindmap 语法，前端 mermaid 库渲染
- 字幕下载：前端直接将 segments 转为 SRT 格式
- CDN 兜底：mermaid 动态导入失败时自动从 jsDelivr CDN 加载

### 6. SEO 优化（v2.0）
- robots.txt + sitemap.xml 引导搜索引擎爬取
- JSON-LD 结构化数据：WebSite（含 SearchAction）、WebApplication、FAQPage
- 静态 HTML 内容页：features.html、faq.html（可被 Google 直接索引）
- OG + Twitter Card 标签：社交分享时显示品牌预览
- SPA 兜底路由：FastAPI 服务 Vue 构建产物，index.html 设置 no-cache

## 遇到的问题

详见 [ISSUES_AND_FIXES.md](ISSUES_AND_FIXES.md)，共记录 23 个问题及修复方案。

关键问题：
1. B站 412 反爬 → 自定义 API 处理器
2. 抖音链接格式不支持 → URL 自动规范化
3. YouTube 没声音 → H.264+AAC 格式选择
4. 芒果TV 下载是 TS 格式 → ffmpeg_location + remux
5. 腾讯视频下载极慢 → CDN 限速（平台限制）
6. B站字幕获取失败（需 SESSDATA）→ 改用 `/x/v2/dm/view` API（无需登录）
