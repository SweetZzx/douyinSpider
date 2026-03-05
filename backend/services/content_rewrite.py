# -*- encoding: utf-8 -*-
"""
文案仿写服务
"""

import json
import re
from typing import Optional
from pydantic import BaseModel, Field
from loguru import logger

from langchain_core.messages import SystemMessage, HumanMessage
from backend.services.llm import get_default_llm
from backend.config import settings, DEFAULT_REWRITE_PROMPT


# ==================== 系统提示词 ====================

BASE_PROMPT = DEFAULT_REWRITE_PROMPT


# ==================== 服务实现 ====================

class ContentRewriteService:
    """文案仿写服务 - 支持多种LLM服务"""

    def __init__(self):
        # 默认配置（智谱AI）
        self.default_api_base = settings.zhipu_api_base
        self.default_api_key = settings.zhipu_api_key
        self.default_model = settings.zhipu_model

        self._api_base = None
        self._api_key = None
        self._model = None
        self.default_prompt = BASE_PROMPT
        self._prompt = None

    @property
    def api_base(self) -> str:
        """获取API地址（优先使用数据库配置）"""
        if self._api_base is None:
            self._api_base = self._load_config_from_db("rewrite_api_base")
        return self._api_base or self.default_api_base

    @property
    def api_key(self) -> str:
        """获取API密钥（优先使用数据库配置）"""
        if self._api_key is None:
            self._api_key = self._load_config_from_db("rewrite_api_key")
        return self._api_key or self.default_api_key

    @property
    def model(self) -> str:
        """获取模型名称（优先使用数据库配置）"""
        if self._model is None:
            self._model = self._load_config_from_db("rewrite_model")
        return self._model or self.default_model

    def _load_config_from_db(self, key: str) -> Optional[str]:
        """从数据库加载配置"""
        try:
            from backend.db.database import get_db_session
            from backend.db import crud

            with get_db_session() as db:
                config = crud.get_system_config(db, key)
                if config and config.value and config.value.strip():
                    return config.value.strip()
        except Exception as e:
            logger.error(f"加载配置失败 {key}: {e}")
        return None

    @property
    def llm(self):
        """获取LLM实例（使用当前配置）"""
        from backend.services.llm import get_llm
        return get_llm(
            model=self.model,
            openai_api_base=self.api_base,
            openai_api_key=self.api_key
        )

    @property
    def prompt(self) -> str:
        """获取当前提示词（优先使用数据库配置）"""
        if self._prompt is None:
            self._prompt = self._load_prompt_from_db()
        return self._prompt or self.default_prompt

    def _load_prompt_from_db(self) -> Optional[str]:
        """从数据库加载自定义提示词"""
        try:
            from backend.db.database import get_db_session
            from backend.db import crud

            with get_db_session() as db:
                config = crud.get_system_config(db, "rewrite_prompt")
                if config and config.value:
                    return config.value
        except Exception as e:
            logger.error(f"加载自定义提示词失败: {e}")
        return None

    def reload_config(self):
        """重新加载配置（用于配置更新后）"""
        self._api_base = None
        self._api_key = None
        self._model = None
        self._prompt = None

    async def rewrite(self, original_text: str) -> str:
        """
        仿写文案

        Args:
            original_text: 原始文案内容

        Returns:
            str: 仿写后的文案

        Raises:
            ValueError: 如果原文案为空
            Exception: 如果LLM调用失败
        """
        if not original_text or not original_text.strip():
            raise ValueError("原文案不能为空")

        try:
            # 构建消息
            messages = [
                SystemMessage(content=self.prompt),
                HumanMessage(content=f"请仿写以下文案：\n\n{original_text}")
            ]

            # 调用LLM
            response = await self.llm.ainvoke(messages)
            rewritten_text = response.content.strip()

            # 清理可能的markdown代码块标记
            if rewritten_text.startswith("```"):
                # 移除markdown代码块
                match = re.search(r"```\w*\s*(.*?)\s*```", rewritten_text, re.DOTALL)
                if match:
                    rewritten_text = match.group(1).strip()

            logger.info(f"文案仿写成功: 原文长度={len(original_text)}, 改写长度={len(rewritten_text)}")

            return rewritten_text

        except ValueError as e:
            logger.error(f"文案仿写参数错误: {e}")
            raise
        except Exception as e:
            logger.error(f"文案仿写失败: {e}", exc_info=True)
            raise Exception(f"文案仿写失败: {str(e)}")

    async def rewrite_with_prompt(self, original_text: str, custom_prompt: str) -> str:
        """
        使用自定义提示词仿写文案

        Args:
            original_text: 原始文案内容
            custom_prompt: 自定义提示词

        Returns:
            str: 仿写后的文案

        Raises:
            ValueError: 如果文案为空
            Exception: 如果LLM调用失败
        """
        if not original_text or not original_text.strip():
            raise ValueError("文案不能为空")

        if not custom_prompt or not custom_prompt.strip():
            # 如果没有提供自定义prompt，使用默认的
            return await self.rewrite(original_text)

        try:
            # 构建消息
            messages = [
                SystemMessage(content=self.prompt),
                HumanMessage(content=f"{custom_prompt}\n\n文案：\n{original_text}")
            ]

            # 调用LLM
            response = await self.llm.ainvoke(messages)
            rewritten_text = response.content.strip()

            # 清理可能的markdown代码块标记
            if rewritten_text.startswith("```"):
                match = re.search(r"```\w*\s*(.*?)\s*```", rewritten_text, re.DOTALL)
                if match:
                    rewritten_text = match.group(1).strip()

            logger.info(f"自定义prompt文案处理成功: 原文长度={len(original_text)}, 改写长度={len(rewritten_text)}")

            return rewritten_text

        except ValueError as e:
            logger.error(f"文案处理参数错误: {e}")
            raise
        except Exception as e:
            logger.error(f"文案处理失败: {e}", exc_info=True)
            raise Exception(f"文案处理失败: {str(e)}")


# 全局实例
content_rewrite_service = ContentRewriteService()
