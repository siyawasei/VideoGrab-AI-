"""用户认证 API（注册/登录/邮箱验证码）"""

import re
import random
import smtplib
import threading
from datetime import datetime, timedelta
from typing import Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt, JWTError

from database import get_db
from models import User
from config import (
    SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES,
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM_NAME,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

# ── 验证码存储（内存，5 分钟过期） ──────────────────────────
_verify_codes: dict = {}  # {email: {"code": "123456", "expires": datetime}}
CODE_TTL_MINUTES = 5


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    account: str  # 用户名或邮箱
    password: str


class SendCodeRequest(BaseModel):
    email: str


# ── 工具函数 ────────────────────────────────────────────────

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


def _validate_email(email: str) -> bool:
    """校验邮箱格式"""
    return bool(EMAIL_REGEX.match(email))


def _generate_code() -> str:
    """生成 6 位数字验证码"""
    return ''.join(random.choices('0123456789', k=6))


def _send_email(to_email: str, code: str) -> bool:
    """发送验证码邮件（异步线程）"""
    if not SMTP_HOST or not SMTP_USER or not SMTP_PASSWORD:
        print(f"[邮件] SMTP 未配置，验证码: {code} (发送到 {to_email})")
        return True  # 开发模式：打印验证码但不实际发送

    try:
        msg = MIMEMultipart()
        msg['From'] = f'{SMTP_FROM_NAME} <{SMTP_USER}>'
        msg['To'] = to_email
        msg['Subject'] = f'【{SMTP_FROM_NAME}】邮箱验证码'

        html = f"""
        <div style="font-family: 'Microsoft YaHei', Arial, sans-serif; max-width: 400px; margin: 0 auto; padding: 30px; background: #f8fafc; border-radius: 12px;">
            <h2 style="color: #2563eb; text-align: center;">{SMTP_FROM_NAME}</h2>
            <p style="color: #374151; font-size: 14px;">你好，你正在注册 {SMTP_FROM_NAME} 账号。</p>
            <div style="background: white; border: 2px solid #2563eb; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0;">
                <p style="color: #6b7280; font-size: 12px; margin: 0;">验证码</p>
                <p style="color: #111827; font-size: 32px; font-weight: bold; letter-spacing: 8px; margin: 10px 0;">{code}</p>
            </div>
            <p style="color: #9ca3af; font-size: 12px;">验证码 {CODE_TTL_MINUTES} 分钟内有效，请勿泄露给他人。</p>
        </div>
        """
        msg.attach(MIMEText(html, 'html', 'utf-8'))

        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, to_email, msg.as_string())

        print(f"[邮件] 验证码已发送到 {to_email}")
        return True
    except Exception as e:
        print(f"[邮件] 发送失败: {e}")
        return False


def create_access_token(data: dict) -> str:
    """创建 JWT Token"""
    to_encode = data.copy()
    expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """获取当前登录用户（必须登录）"""
    if not credentials:
        raise HTTPException(status_code=401, detail="未登录")
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token 无效")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token 过期或无效")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """获取当前登录用户（可选，未登录返回 None）"""
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None
    return db.query(User).filter(User.id == user_id).first()


# ── API 路由 ────────────────────────────────────────────────

@router.post("/send-code")
async def send_verification_code(req: SendCodeRequest, db: Session = Depends(get_db)):
    """发送邮箱验证码"""
    email = req.email.strip().lower()

    if not _validate_email(email):
        raise HTTPException(status_code=400, detail="邮箱格式不正确")

    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="该邮箱已被注册")

    # 防频繁发送（60 秒冷却）
    existing = _verify_codes.get(email)
    if existing and datetime.now() < existing["expires"] - timedelta(minutes=CODE_TTL_MINUTES - 1):
        raise HTTPException(status_code=429, detail="请等待 60 秒后再试")

    code = _generate_code()
    _verify_codes[email] = {
        "code": code,
        "expires": datetime.now() + timedelta(minutes=CODE_TTL_MINUTES),
    }

    # 异步发送邮件（不阻塞请求）
    threading.Thread(target=_send_email, args=(email, code), daemon=True).start()

    return {"code": 0, "message": "验证码已发送，请查收邮箱"}


@router.post("/register")
async def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """用户注册（用户名+密码）"""
    if len(req.username) < 2 or len(req.username) > 20:
        raise HTTPException(status_code=400, detail="用户名长度需在 2-20 个字符之间")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="密码长度至少 6 位")

    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")

    user = User(
        username=req.username,
        email=f"{req.username}@videograb.local",  # 自动生成占位邮箱
        password_hash=pwd_context.hash(req.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "code": 0,
        "message": "注册成功",
        "data": {
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            },
        },
    }


@router.post("/login")
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    """用户登录（支持用户名或邮箱）"""
    user = db.query(User).filter(
        (User.username == req.account) | (User.email == req.account)
    ).first()
    if not user or not pwd_context.verify(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名/邮箱或密码错误")

    token = create_access_token({"sub": user.id})
    return {
        "code": 0,
        "data": {
            "token": token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "membership": user.membership,
            },
        },
    }


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return {
        "code": 0,
        "data": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "membership": current_user.membership,
            "daily_downloads_used": current_user.daily_downloads_used,
            "daily_downloads_limit": current_user.daily_downloads_limit,
        },
    }
