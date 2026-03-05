# -*- encoding: utf-8 -*-
"""
FastAPI 主入口
"""

import sys
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from loguru import logger
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import ValidationError

from backend.config import settings
from backend.routers import api, auth
from backend.exceptions import (
    AppException,
    app_exception_handler,
    http_exception_handler,
    general_exception_handler,
)


# ==================== 速率限制配置 ====================

limiter = Limiter(key_func=get_remote_address)
app_state = {"rate_limit": "initialized"}


def setup_logger():
    """配置日志"""
    # 移除默认的处理器
    logger.remove()

    # 创建日志目录
    log_path = settings.log_path
    os.makedirs(log_path, exist_ok=True)

    # 控制台输出
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</> | <level>{level: <8}</> | <cyan>{name}</>:<cyan>{function}</>:<cyan>{line}</> - <level>{message}</>",
        colorize=True,
    )

    # 文件输出 - 所有日志
    logger.add(
        os.path.join(log_path, "app_{time:YYYY-MM-DD}.log"),
        level=settings.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation=settings.log_rotation,
        retention=settings.log_retention,
        encoding="utf-8",
    )

    # 文件输出 - 错误日志单独存放
    logger.add(
        os.path.join(log_path, "error_{time:YYYY-MM-DD}.log"),
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation=settings.log_rotation,
        retention=settings.log_retention,
        encoding="utf-8",
    )

    logger.info("日志系统初始化完成")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 初始化日志
    setup_logger()

    logger.info(f"{settings.app_name} v{settings.app_version} 启动中...")

    # 初始化数据库
    from backend.db.database import init_db
    try:
        init_db()
        logger.info("数据库初始化成功")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")

    # 启动后台监控任务
    from backend.services.scheduler import start_scheduler
    try:
        start_scheduler(interval_minutes=30)  # 每30分钟检查一次
        logger.info("后台监控任务已启动")
    except Exception as e:
        logger.error(f"启动监控任务失败: {e}")

    yield

    # 关闭调度器
    from backend.services.scheduler import stop_scheduler
    stop_scheduler()
    logger.info(f"{settings.app_name} 关闭中...")


# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="抖音UP主视频管理系统",
    lifespan=lifespan,
    state=app_state,
)

# 设置速率限制器
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ==================== 注册全局异常处理器 ====================

# 自定义应用异常
app.add_exception_handler(AppException, app_exception_handler)

# HTTP异常
app.add_exception_handler(HTTPException, http_exception_handler)

# 请求验证异常
app.add_exception_handler(RequestValidationError, http_exception_handler)

# 通用异常（捕获所有未处理的异常）
app.add_exception_handler(Exception, general_exception_handler)

# 配置CORS
# 生产环境CORS配置
if settings.debug:
    # 开发环境：允许本地开发服务器
    allowed_origins = [
        "http://localhost:5173",
        "http://localhost:7777",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:7777",
    ]
else:
    # 生产环境：从环境变量读取或使用默认值
    allowed_origins = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
    if not allowed_origins or allowed_origins == [""]:
        # 如果没有配置，使用前端域名（请根据实际情况修改）
        allowed_origins = ["http://localhost:7777"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# 注册路由
# 认证路由（无需认证）
app.include_router(auth.router, prefix="/api", tags=["Auth"])

# API路由（需要认证的路由已在各自路由中保护）
app.include_router(api.router, prefix="/api", tags=["API"])

# 创建音频文件目录并挂载静态文件服务
audio_dir = "./extracted_audio"
os.makedirs(audio_dir, exist_ok=True)
app.mount("/static/audio", StaticFiles(directory=audio_dir), name="audio")
logger.info(f"音频静态文件服务已挂载: /static/audio -> {audio_dir}")


# ==================== 启动入口 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=77,
        reload=True,
    )
