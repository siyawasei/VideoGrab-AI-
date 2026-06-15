"""项目配置文件 — 所有敏感信息从环境变量读取"""

import os
import secrets as _secrets

# 数据库配置
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "video_downloader")
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

# JWT 配置（未设置时自动生成随机密钥，每次重启后旧 token 失效）
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "") or _secrets.token_hex(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24小时

# 下载目录
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")

# Cookies 目录
COOKIES_DIR = os.path.join(os.path.dirname(__file__), "cookies")

# 会员配置
MEMBERSHIP_LIMITS = {
    "free": {"daily_downloads": 5, "max_quality": "720p"},
    "pro": {"daily_downloads": 9999, "max_quality": "2160p"},
    "premium": {"daily_downloads": 9999, "max_quality": "2160p"},
}

# DeepSeek API 配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# 邮件 SMTP 配置（注册验证码，可选）
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "VideoGrab")
