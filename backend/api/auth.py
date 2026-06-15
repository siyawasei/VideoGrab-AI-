"""用户认证 API（注册/登录）"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt, JWTError

from database import get_db
from models import User
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/api/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    account: str  # 用户名或邮箱
    password: str


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


@router.post("/register")
async def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户名是否已存在
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="邮箱已被注册")

    user = User(
        username=req.username,
        email=req.email,
        password_hash=pwd_context.hash(req.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

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


@router.post("/login")
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    """用户登录（支持用户名或邮箱）"""
    # 支持用户名或邮箱登录
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
