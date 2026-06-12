"""项目配置文件"""

import os

# 数据库配置
DB_HOST = "127.0.0.1"
DB_PORT = 3306
DB_USER = "root"
DB_PASSWORD = "123456"
DB_NAME = "video_downloader"
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

# JWT 配置
SECRET_KEY = "your-secret-key-change-in-production"
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
