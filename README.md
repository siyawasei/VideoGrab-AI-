# VideoGrab - 万能视频下载器

一站式视频下载 + AI 智能分析平台。支持 YouTube、B站、抖音等 1800+ 平台的视频解析与下载，集成 AI 视频总结、字幕提取、思维导图生成等智能功能。

## 核心功能

- **视频解析与下载** — 支持 1800+ 平台，多画质选择（8K/4K/1080p/720p/480p），SSE 实时进度推送
- **B站专用处理器** — 绕过 WBI 签名反爬，DASH 并发下载 + CDN 备用节点自动切换 + ffmpeg 合并
- **AI 视频总结** — DeepSeek 大模型流式输出结构化总结（摘要/章节时间线/关键要点/标签）
- **思维导图** — 自动生成 Mermaid mindmap，支持全屏查看、SVG/PNG 下载
- **字幕提取与下载** — B站/YouTube/通用平台字幕自动获取，SRT 格式导出
- **AI 问答** — 基于视频内容的多轮对话，流式返回回答
- **用户系统** — 注册/登录（JWT）、下载历史、会员等级、Cookies/SESSDATA 配置
- **SEO 优化** — robots.txt、sitemap.xml、Open Graph、JSON-LD 结构化数据、静态 HTML 内容页

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | Vue 3 + Vite + Tailwind CSS 4 + Pinia + Vue Router + Mermaid + Marked |
| 后端 | Python FastAPI + yt-dlp 2026.06.09 + ffmpeg |
| 数据库 | MySQL 8 (localhost:3306) |
| AI 大模型 | DeepSeek API (deepseek-chat, OpenAI 兼容 SDK) |
| 实时通信 | Server-Sent Events (SSE) |

## 快速启动

### 1. 环境要求

- Python 3.10+
- Node.js 20+
- MySQL 8+
- ffmpeg（B站 DASH 合并和 HLS 转封装需要）

### 2. 安装依赖

```bash
# 后端
cd backend
pip install -r requirements.txt

# 前端
cd frontend
npm install
```

### 3. 配置数据库

确保 MySQL 服务已启动，创建数据库：

```sql
CREATE DATABASE IF NOT EXISTS video_downloader CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
```

数据库连接配置在 `backend/config.py`，默认账号 `root`，密码 `123456`。首次启动时自动建表。

### 4. 配置 AI 功能（可选）

AI 视频总结功能需要 DeepSeek API Key。二选一配置：

```bash
# 方式一：环境变量
export DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx

# 方式二：文件
echo "sk-xxxxxxxxxxxxxxxx" > backend/cookies/deepseek_key.txt
```

获取 API Key：https://platform.deepseek.com/

### 5. 启动服务

```bash
# 终端 1：启动后端（端口 8000）
cd backend
python app.py

# 终端 2：启动前端（端口 5173，开发模式）
cd frontend
npm run dev
```

浏览器打开 http://localhost:5173

### 6. 生产部署

```bash
# 构建前端
cd frontend
npm run build

# 启动后端（自动服务前端构建产物）
cd backend
python app.py
```

构建后访问 http://localhost:8000 即可（前后端统一端口）。

## 使用方式

### 下载视频

1. 在首页输入框粘贴视频链接（支持 YouTube、B站、抖音等）
2. 点击「解析视频」，等待解析完成
3. 在弹窗左栏选择画质，点击「开始下载」
4. 等待进度条完成，点击「保存文件」

### AI 视频总结

1. 解析视频后，弹窗右栏自动开始 AI 总结
2. 切换 Tab 查看：📝 总结 / 🧠 思维导图 / 📋 字幕 / 💬 问答
3. 思维导图支持全屏查看和 SVG/PNG 下载
4. 字幕支持 SRT 格式下载

### B站高清画质

1. 点击导航栏「Cookies」按钮
2. 在 B站按 F12 → Application → Cookies → bilibili.com → 复制 SESSDATA
3. 粘贴到输入框并保存
4. 再次解析 B站视频即可看到 720p/1080p/4K/8K 画质

## 支持平台

| 平台 | 状态 | 说明 |
|------|------|------|
| B站 | ✅ 可用 | 自定义 API 处理器，绕过 412 反爬 |
| YouTube | ✅ 可用 | 需代理访问，H.264+AAC 兼容性优化 |
| 抖音 | ✅ 可用 | 短链/精选页自动规范化 |
| 优酷 | ✅ 可用 | yt-dlp 直接支持 |
| AcFun | ✅ 可用 | yt-dlp 直接支持 |
| 芒果TV | ✅ 可用 | 免费视频可用，HLS→MP4 转封装 |
| 西瓜视频 | ⚠️ 需 Cookies | 上传 cookies 后可用 |
| 腾讯视频 | 🟠 CDN 限速 | 能解析，下载极慢 |
| 爱奇艺 | ❌ 不可用 | yt-dlp extractor 过时 |

## 项目结构

```
AI_video/
├── backend/
│   ├── app.py                  # FastAPI 主入口（路由注册、SPA 兜底、SEO 静态页）
│   ├── config.py               # 配置（数据库、JWT、路径、DeepSeek API、SMTP）
│   ├── database.py             # SQLAlchemy 连接池
│   ├── models.py               # 数据模型（User/DownloadHistory/Order）
│   ├── requirements.txt        # Python 依赖
│   ├── api/
│   │   ├── auth.py             # 认证（注册/登录/JWT/邮箱验证码）
│   │   ├── bilibili.py         # B站专用（API 解析/DASH 下载/CDN 备用/字幕）
│   │   ├── downloader.py       # yt-dlp 封装（URL 规范化/平台检测/格式处理）
│   │   ├── routes.py           # 主路由（解析/下载/SSE 进度/Cookie/平台状态）
│   │   ├── history.py          # 下载历史
│   │   ├── ai.py               # AI 功能（视频总结/AI 问答/字幕获取）
│   │   └── subtitle.py         # 字幕统一接口（B站/yt-dlp/json3/VTT）
│   ├── cookies/                # cookies/SESSDATA 存储（.gitignore）
│   └── downloads/              # 视频下载临时目录（.gitignore）
│
├── frontend/
│   ├── index.html              # 入口 HTML（SEO meta/OG/JSON-LD）
│   ├── package.json            # 依赖
│   ├── vite.config.js          # Vite 配置（Vue + Tailwind + API 代理）
│   ├── public/
│   │   ├── robots.txt          # 爬虫规则（含 AI 爬虫 Allow）
│   │   ├── sitemap.xml         # 站点地图
│   │   ├── features.html       # 功能介绍静态页
│   │   └── faq.html            # FAQ 静态页（含 FAQPage schema）
│   └── src/
│       ├── api/index.js        # API 封装（Axios + fetch SSE）
│       ├── components/         # 12 个 Vue 组件
│       ├── composables/        # useDownloader + useAiSummary
│       ├── router/index.js     # Vue Router
│       ├── stores/user.js      # Pinia 用户状态
│       └── views/              # HomeView + HistoryView
│
├── product.md                  # 产品成功报告
├── ISSUES_AND_FIXES.md         # 问题记录（23 条）
├── PROJECT_SUMMARY.md          # 项目技术总结
└── README.md                   # 本文档
```

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/auth/register` | POST | 用户注册 |
| `/api/auth/login` | POST | 用户登录 |
| `/api/auth/me` | GET | 获取用户信息 |
| `/api/info` | POST | 解析视频信息 |
| `/api/download` | POST | 创建下载任务 |
| `/api/progress/{task_id}` | GET | SSE 下载进度 |
| `/api/file/{task_id}` | GET | 下载文件 |
| `/api/history` | GET | 下载历史 |
| `/api/platforms` | GET | 平台状态列表 |
| `/api/cookies/upload` | POST | 上传 cookies |
| `/api/bilibili/sessdata` | POST/GET | B站 SESSDATA |
| `/api/summarize` | POST | AI 视频总结（SSE） |
| `/api/ai-chat` | POST | AI 问答（SSE） |
| `/api/transcript` | POST | 获取视频字幕 |

## 文档

- [product.md](product.md) — 产品成功报告（功能清单、问题记录、Phase 2/3 规划、SEO 分析、技术架构）
- [ISSUES_AND_FIXES.md](ISSUES_AND_FIXES.md) — 开发过程中遇到的 23 个问题及修复方案
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) — 项目技术总结（架构图、数据流、平台支持）
- [AI_SUMMARY_PLAN.md](AI_SUMMARY_PLAN.md) — AI 视频总结功能实施方案

## License

MIT
