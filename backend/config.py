# -*- encoding: utf-8 -*-
"""
配置管理模块
"""

import os
from typing import Optional

from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from loguru import logger

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

    # 智谱AI配置
    zhipu_api_key: str = ""
    zhipu_api_base: str = "https://open.bigmodel.cn/api/paas/v4"
    zhipu_model: str = "glm-4.7"
    zhipu_temperature: float = 0.7
    zhipu_max_tokens: int = 2000

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
    """设置Cookie并持久化到.env文件"""
    settings.cookie = cookie

    # 持久化到.env文件
    env_path = ".env"
    try:
        # 读取现有内容
        lines = []
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

        # 查找并替换COOKIE行，或者添加新行
        cookie_found = False
        for i, line in enumerate(lines):
            if line.strip().startswith('COOKIE='):
                lines[i] = f'COOKIE={cookie}\n'
                cookie_found = True
                break

        if not cookie_found:
            # 如果没有找到COOKIE行，在文件开头添加
            lines.insert(0, f'COOKIE={cookie}\n')

        # 写回文件
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        logger.info(f"Cookie已保存到{env_path}")
    except Exception as e:
        # 如果保存失败，只在内存中更新，不影响运行
        print(f"警告：无法保存Cookie到.env文件: {e}")


# ==================== 默认提示词 ====================

DEFAULT_REWRITE_PROMPT = """你是一个专业的短视频文案仿写助手，擅长将抖音视频文案改写成风格相似但内容原创的新文案。

你的任务是：
1. 分析原文案的核心信息、语气、风格
2. 保留原文案的吸引力和表达方式
3. 用不同的词汇和句式重新组织内容
4. 保持文案的长度和结构相似

改写要求：
- 保持原文案的核心主题和情感
- 使用不同的表达方式，避免直接替换同义词
- 保持口语化、接地气的风格
- 适当加入emoji，保持抖音文案的特色
- 不要改变原文案的意思和立场
- 确保改写后的文案读起来自然流畅

输出格式：
请直接输出改写后的文案，不要包含任何解释或说明。

示例：
原文案：今天给大家分享一个超级实用的技巧，学会之后真的能省下不少钱！
改写：家人们，今天一定要教你们这个省钱小妙招，学会了真的能帮你省下一大笔！
"""
