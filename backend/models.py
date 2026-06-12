"""SQLAlchemy 数据库模型定义"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, BigInteger, DateTime, ForeignKey, Enum, DECIMAL
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    membership = Column(Enum("free", "pro", "premium", name="membership_type"), default="free", nullable=False)
    daily_downloads_used = Column(Integer, default=0, nullable=False)
    daily_downloads_limit = Column(Integer, default=5, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    downloads = relationship("DownloadHistory", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")


class DownloadHistory(Base):
    """下载历史表"""
    __tablename__ = "download_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    url = Column(Text, nullable=False)
    title = Column(String(500), nullable=True)
    thumbnail = Column(Text, nullable=True)
    platform = Column(String(50), nullable=True)
    quality = Column(String(20), nullable=True)
    file_size = Column(BigInteger, nullable=True)
    status = Column(Enum("pending", "downloading", "completed", "failed", name="download_status"),
                    default="pending", nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    user = relationship("User", back_populates="downloads")


class Order(Base):
    """订单表"""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    plan = Column(Enum("pro", "premium", name="plan_type"), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    status = Column(Enum("pending", "paid", "cancelled", name="order_status"),
                    default="pending", nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    user = relationship("User", back_populates="orders")
