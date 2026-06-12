# VideoGrab - 万能视频下载器

支持 1800+ 平台的在线视频下载工具，深色渐变 + 玻璃拟态 UI，支持用户注册、会员体系、下载历史。

## 技术栈

- **前端**: Vue 3 + Vite + Tailwind CSS 4
- **后端**: Python FastAPI + yt-dlp
- **数据库**: MySQL 8 (localhost:3306)
- **实时进度**: Server-Sent Events (SSE)

## 快速启动

### 1. 安装依赖

**后端:**
```bash
cd backend
pip install -r requirements.txt
```

**前端:**
```bash
cd frontend
npm install
```

### 2. 确保 MySQL 运行

确保 MySQL 服务已启动，然后创建数据库：
```sql
CREATE DATABASE IF NOT EXISTS video_downloader CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
```

### 3. 启动服务

**启动后端 (端口 8000):**
```bash
cd backend
python app.py
```

**启动前端 (端口 5173):**
```bash
cd frontend
npm run dev
```

### 4. 访问

浏览器打开 `http://localhost:5173`

## 项目结构

```
AI_video/
├── backend/
│   ├── app.py              # FastAPI 主入口
│   ├── config.py           # 配置文件
│   ├── database.py         # 数据库连接
│   ├── models.py           # 数据模型
│   ├── requirements.txt    # Python 依赖
│   └── api/
│       ├── auth.py         # 认证 API
│       ├── downloader.py   # yt-dlp 封装
│       ├── routes.py       # 下载 API
│       └── history.py      # 历史记录 API
│
├── frontend/
│   ├── src/
│   │   ├── App.vue         # 根组件
│   │   ├── main.js         # 入口
│   │   ├── api/            # API 服务
│   │   ├── components/     # Vue 组件
│   │   ├── composables/    # 组合式函数
│   │   ├── router/         # 路由
│   │   ├── stores/         # Pinia 状态
│   │   └── views/          # 页面视图
│   └── vite.config.js
│
└── README.md
```

## 功能

- 视频链接解析（支持 1800+ 平台）
- 多画质选择（4K/1080p/720p）
- 实时下载进度（SSE）
- 用户注册/登录（JWT）
- 下载历史记录
- 会员套餐展示
- 响应式设计（手机/电脑）
