"""数据库连接和 Session 管理"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from config import DATABASE_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI 依赖注入：获取数据库 Session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """创建所有数据表"""
    import models  # noqa: F401 — 确保模型被导入
    Base.metadata.create_all(bind=engine)
