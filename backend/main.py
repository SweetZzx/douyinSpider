# -*- encoding: utf-8 -*-
"""
FastAPI 主入口
"""

import sys
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.config import settings
from backend.routers import api


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
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api.router, prefix="/api", tags=["API"])


# ==================== 启动入口 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=77,
        reload=True,
    )
