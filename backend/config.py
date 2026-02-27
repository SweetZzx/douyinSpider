# -*- encoding: utf-8 -*-
"""
配置管理模块
"""

import os
from typing import Optional

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """应用配置"""

    # 服务配置
    app_name: str = "Douyin Spider Web"
    app_version: str = "1.0.0"
    debug: bool = True

    # Cookie（从环境变量或配置文件读取）
    cookie: str = ""

    # 下载路径
    download_path: str = "./downloads"

    # 日志配置
    log_path: str = "./logs"
    log_level: str = "DEBUG"
    log_rotation: str = "10 MB"
    log_retention: str = "7 days"

    # 数据库配置
    database_url: str = "mysql+pymysql://root@localhost:3306/douyin_spider"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# 全局配置实例
settings = Settings()


def get_cookie() -> str:
    """获取Cookie"""
    return settings.cookie


def set_cookie(cookie: str):
    """设置Cookie"""
    settings.cookie = cookie
