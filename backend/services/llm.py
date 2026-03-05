# -*- encoding: utf-8 -*-
"""
LLM服务模块 - 使用智谱AI
"""

from typing import Optional
from langchain_openai import ChatOpenAI
from backend.config import settings


def get_llm(
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    openai_api_key: Optional[str] = None,
    openai_api_base: Optional[str] = None,
    **kwargs
) -> ChatOpenAI:
    """
    获取LLM实例

    Args:
        model: 模型名称，默认使用配置文件中的模型
        temperature: 温度参数
        max_tokens: 最大token数
        openai_api_key: API密钥，默认使用配置文件中的密钥
        openai_api_base: API地址，默认使用配置文件中的地址
        **kwargs: 其他参数

    Returns:
        ChatOpenAI: LLM实例
    """
    model_name = model or settings.zhipu_model
    api_key = openai_api_key or settings.zhipu_api_key
    api_base = openai_api_base or settings.zhipu_api_base

    llm = ChatOpenAI(
        model=model_name,
        openai_api_key=api_key,
        openai_api_base=api_base,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs
    )
    return llm


def get_default_llm() -> ChatOpenAI:
    """获取默认LLM实例（单例模式）"""
    if not hasattr(get_default_llm, "_instance"):
        get_default_llm._instance = get_llm(
            temperature=settings.zhipu_temperature,
            max_tokens=settings.zhipu_max_tokens
        )
    return get_default_llm._instance
