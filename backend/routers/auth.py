# -*- encoding: utf-8 -*-
"""
认证路由
"""

from fastapi import APIRouter, HTTPException, status, Depends, Request
from pydantic import BaseModel
from loguru import logger

from backend.auth import authenticate_user, create_access_token, get_current_user
from backend.rate_limit import limiter


router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """令牌响应"""
    access_token: str
    token_type: str
    username: str


class UserResponse(BaseModel):
    """用户信息响应"""
    username: str
    logged_in: bool


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")  # 每分钟最多5次登录尝试
async def login(request: Request, data: LoginRequest):
    """用户登录

    Args:
        data: 登录请求（用户名和密码）

    Returns:
        访问令牌

    Raises:
        HTTPException: 登录失败
    """
    # 验证用户凭据
    if not authenticate_user(data.username, data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 创建访问令牌
    access_token = create_access_token(data={"sub": data.username})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        username=data.username
    )


@router.post("/verify", response_model=UserResponse)
async def verify_auth(user: dict = Depends(get_current_user)):
    """验证令牌有效性

    Args:
        user: 当前用户（从依赖注入获取）

    Returns:
        用户信息
    """
    return UserResponse(
        username=user["username"],
        logged_in=True
    )


@router.post("/logout")
async def logout():
    """用户登出（前端删除令牌）"""
    return {"message": "登出成功"}
