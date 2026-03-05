# -*- encoding: utf-8 -*-
"""
JWT认证模块
"""

import os
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from loguru import logger

# JWT配置
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise ValueError(
        "JWT_SECRET_KEY environment variable must be set. "
        "Please add it to your .env file: "
        "JWT_SECRET_KEY=<your-secret-key>"
    )
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7天

# 安全HTTP Bearer
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码（使用bcrypt）

    Args:
        plain_password: 明文密码
        hashed_password: bcrypt哈希密码

    Returns:
        密码是否匹配
    """
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except (ValueError, TypeError) as e:
        logger.warning(f"密码验证失败: {e}")
        return False


def get_password_hash(password: str) -> str:
    """获取密码哈希（使用bcrypt）

    Args:
        password: 明文密码

    Returns:
        bcrypt哈希字符串
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建JWT访问令牌

    Args:
        data: 要编码到令牌中的数据
        expires_delta: 过期时间增量

    Returns:
        JWT令牌字符串
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """解码JWT访问令牌

    Args:
        token: JWT令牌字符串

    Returns:
        解码后的数据

    Raises:
        JWTError: 令牌无效或过期
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"JWT解码失败: {e}")
        raise


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """获取当前认证用户（依赖注入）

    Args:
        credentials: HTTP Bearer凭证

    Returns:
        用户信息字典

    Raises:
        HTTPException: 认证失败
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # 从Bearer token中获取JWT
        token = credentials.credentials
        payload = decode_access_token(token)

        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception

        return {
            "username": username,
            "exp": payload.get("exp"),
        }

    except JWTError:
        raise credentials_exception


# 预设的用户名和密码哈希（admin/admin）
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD_HASH = get_password_hash("admin")


def authenticate_user(username: str, password: str) -> bool:
    """验证用户凭据

    Args:
        username: 用户名
        password: 密码

    Returns:
        是否验证成功
    """
    # 验证用户名
    if username != DEFAULT_USERNAME:
        logger.warning(f"用户名不存在: {username}")
        return False

    # 验证密码
    if not verify_password(password, DEFAULT_PASSWORD_HASH):
        logger.warning(f"密码错误: {username}")
        return False

    logger.info(f"用户登录成功: {username}")
    return True
