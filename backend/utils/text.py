# -*- encoding: utf-8 -*-
"""
文本处理工具模块
"""

import re
from typing import Union

import requests
from loguru import logger


def sanitize_filename(
    text: str, max_bytes: int = 100, add_ellipsis: bool = True
) -> str:
    """
    生成安全的文件名

    Args:
        text: 原始文本
        max_bytes: 最大字节数（默认 100，考虑中文字符）
        add_ellipsis: 超长时是否添加省略号

    Returns:
        安全的文件名字符串
    """
    if not text or not isinstance(text, str):
        return "无标题"

    text = text.strip()
    if not text:
        return "无标题"

    # 过滤特殊字符
    # Windows 文件名禁止字符: < > : " / \ | ? *
    safe_text = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", text)

    # 替换多个空格为单个空格
    safe_text = re.sub(r"\s+", " ", safe_text).strip()

    if not safe_text:
        return "无标题"

    # 按字节限制长度（考虑中文字符）
    if len(safe_text.encode("utf-8")) > max_bytes:
        # 按字节截断，避免截断中文字符
        safe_text_bytes = safe_text.encode("utf-8")[:max_bytes]
        # 解码时忽略不完整的字符
        safe_text = safe_text_bytes.decode("utf-8", errors="ignore").strip()
        # 添加省略号标识
        if safe_text and add_ellipsis:
            safe_text = safe_text + "..."

    return safe_text if safe_text else "无标题"


def quit(str: str = ""):
    """
    抛出异常而不是退出程序（适用于GUI应用）
    """
    if str:
        logger.error(str)
    raise Exception(str if str else "程序异常退出")


def url_redirect(url: str) -> str:
    """
    获取URL的最终重定向地址

    Args:
        url: 原始URL

    Returns:
        最终重定向的URL
    """
    r = requests.head(url, allow_redirects=True)
    return r.url


def extract_valid_urls(input_data: Union[str, list]) -> Union[str, list, None]:
    """
    提取有效的URL

    Args:
        input_data: 字符串或字符串列表

    Returns:
        提取的URL或URL列表
    """
    url_pattern = re.compile(r"https?://[^\s]+")

    if isinstance(input_data, str):
        match = url_pattern.search(input_data)
        return match.group(0) if match else input_data
    elif isinstance(input_data, list):
        return [extract_valid_urls(item) for item in input_data if item]
    return None
