# -*- encoding: utf-8 -*-
"""
语音转文字服务模块（基于智谱GLM-ASR）
支持音频文件转写，自动处理长音频（切片）
"""

import os
import subprocess
import json
import tempfile
from typing import Optional
from pathlib import Path
from datetime import datetime
from loguru import logger
import asyncio

from dotenv import load_dotenv
from zhipuai import ZhipuAI

load_dotenv()


class Transcriber:
    """语音转文字服务 - 支持多种ASR服务"""

    def __init__(self, output_dir: str = "./transcripts"):
        """
        初始化转写服务

        Args:
            output_dir: 转写结果保存目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 默认配置（智谱AI）
        self.default_api_base = "https://open.bigmodel.cn/api/paas/v4"
        self.default_api_key = os.getenv("ZHIPU_API_KEY", "")
        self.default_model = "glm-asr-2512"

        self._api_base = None
        self._api_key = None
        self._model = None

        if not self.default_api_key:
            logger.warning("默认API Key未配置，语音转写功能可能不可用")
        else:
            logger.info("语音识别服务初始化成功")

    @property
    def api_base(self) -> str:
        """获取API地址（优先使用数据库配置）"""
        if self._api_base is None:
            self._api_base = self._load_config_from_db("transcribe_api_base")
        return self._api_base or self.default_api_base

    @property
    def api_key(self) -> str:
        """获取API密钥（优先使用数据库配置）"""
        if self._api_key is None:
            self._api_key = self._load_config_from_db("transcribe_api_key")
        return self._api_key or self.default_api_key

    @property
    def model(self) -> str:
        """获取模型名称（优先使用数据库配置）"""
        if self._model is None:
            self._model = self._load_config_from_db("transcribe_model")
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

    def reload_config(self):
        """重新加载配置（用于配置更新后）"""
        self._api_base = None
        self._api_key = None
        self._model = None

    async def transcribe_audio(
        self,
        audio_path: str,
        video_id: str
    ) -> Optional[dict]:
        """
        转写音频文件

        Args:
            audio_path: 音频文件路径
            video_id: 视频ID（用于保存结果）

        Returns:
            转写结果 {
                "success": True/False,
                "text": "完整文本",
                "segments": [],
                "language": "语言",
                "duration": 时长,
                "error": 错误信息
            }
        """
        if not self.api_key:
            return {
                "success": False,
                "text": None,
                "segments": [],
                "language": None,
                "duration": 0,
                "error": "智谱AI API Key未配置，请设置ZHIPU_API_KEY"
            }

        try:
            # 检查音频文件是否存在
            audio_file = Path(audio_path)
            if not audio_file.exists():
                return {
                    "success": False,
                    "text": None,
                    "segments": [],
                    "language": None,
                    "duration": 0,
                    "error": f"音频文件不存在: {audio_path}"
                }

            logger.info(f"开始转写音频: {audio_path}")

            # 获取音频时长
            duration = self._get_audio_duration(audio_path)

            # 智谱AI限制：单次最多30秒，且需要单声道
            max_duration = 30

            if duration <= max_duration:
                logger.info(f"短视频（{duration:.1f}秒），直接转写")
                result_text = await self._transcribe_single(audio_file)
            else:
                # 长视频需要切片处理
                logger.info(f"长视频（{duration:.1f}秒），切片后转写")
                result_text = await self._transcribe_with_slices(audio_file, max_duration)

            if result_text:
                # 保存转写结果到JSON文件
                result_file = self.output_dir / f"{video_id}.json"
                result_data = {
                    "text": result_text,
                    "segments": [{'text': result_text, 'begin_time': 0, 'end_time': duration * 1000}],
                    "video_id": video_id,
                    "audio_path": audio_path,
                    "created_at": datetime.now().isoformat()
                }

                with open(result_file, 'w', encoding='utf-8') as f:
                    json.dump(result_data, f, ensure_ascii=False, indent=2)

                logger.success(f"转写成功: {audio_path} -> {len(result_text)} 字符")
                logger.info(f"转写结果已保存: {result_file}")

                return {
                    "success": True,
                    "text": result_text,
                    "segments": [{'text': result_text, 'begin_time': 0, 'end_time': duration * 1000}],
                    "language": "zh",
                    "duration": duration,
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "text": None,
                    "segments": [],
                    "language": None,
                    "duration": duration,
                    "error": "转写返回空结果"
                }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"语音转写失败: {error_msg}")
            return {
                "success": False,
                "text": None,
                "segments": [],
                "language": None,
                "duration": 0,
                "error": error_msg
            }

    async def _transcribe_single(self, audio_file: Path) -> Optional[str]:
        """
        转写单个音频文件（≤30秒）

        Args:
            audio_file: 音频文件路径

        Returns:
            转写文本或None
        """
        try:
            # 转换为单声道16kHz（智谱AI要求）
            mono_file = await self._convert_to_mono(audio_file)
            if not mono_file:
                return None

            # 调用智谱AI API
            client = ZhipuAI(api_key=self.api_key)

            with open(mono_file, 'rb') as f:
                response = client.audio.transcriptions.create(
                    model=self.model,  # 使用配置的模型
                    file=f,
                    stream=False
                )

            # 解析响应
            text = None
            if hasattr(response, 'text') and response.text:
                text = response.text
            elif hasattr(response, 'segments') and response.segments:
                text = ''.join(seg.get('text', '') for seg in response.segments)

            # 清理临时文件
            if mono_file != audio_file and mono_file.exists():
                mono_file.unlink()

            return text

        except Exception as e:
            logger.error(f"单音频转写失败: {e}")
            return None

    async def _transcribe_with_slices(
        self,
        audio_file: Path,
        segment_duration: int = 25
    ) -> Optional[str]:
        """
        将音频切片后分别转写

        Args:
            audio_file: 音频文件路径
            segment_duration: 每段时长（秒），留5秒余量

        Returns:
            转写文本或None
        """
        try:
            # 创建临时目录
            temp_dir = tempfile.mkdtemp()
            temp_path = Path(temp_dir)

            # 分割音频
            output_pattern = str(temp_path / "segment_%03d.wav")
            cmd = [
                'ffmpeg', '-i', str(audio_file),
                '-f', 'segment',
                '-segment_time', str(segment_duration),
                '-ac', '1',  # 单声道
                '-ar', '16000',  # 16kHz采样率
                '-acodec', 'pcm_s16le',
                output_pattern
            ]

            logger.info(f"正在分割音频（每段{segment_duration}秒）...")
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
            )

            if result.returncode != 0:
                logger.error(f"音频分割失败: {result.stderr.decode()}")
                return None

            # 查找所有片段
            segments = sorted(temp_path.glob("segment_*.wav"))

            if not segments:
                logger.error("未找到音频片段")
                return None

            logger.info(f"音频已分割为{len(segments)}个片段，开始转写...")

            # 转写每个片段
            all_text = []
            client = ZhipuAI(api_key=self.api_key)

            for i, segment in enumerate(segments, 1):
                logger.info(f"转写片段 {i}/{len(segments)}: {segment.name}")

                try:
                    with open(segment, 'rb') as f:
                        response = client.audio.transcriptions.create(
                            model="glm-asr-2512",  # 使用新一代模型，CER更低
                            file=f,
                            stream=False
                        )

                    # 解析结果
                    text = None
                    if hasattr(response, 'text') and response.text:
                        text = response.text
                    elif hasattr(response, 'segments') and response.segments:
                        text = ''.join(seg.get('text', '') for seg in response.segments)

                    if text:
                        all_text.append(text)
                        logger.info(f"片段{i}转写成功: {len(text)}字符")
                    else:
                        logger.warning(f"片段{i}转写返回空结果")

                except Exception as e:
                    logger.warning(f"片段{i}转写失败: {e}")

                # 避免请求过快
                await asyncio.sleep(0.5)

            # 清理临时文件
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

            if all_text:
                combined_text = ''.join(all_text)
                logger.success(f"所有片段转写完成，总计{len(combined_text)}字符")
                return combined_text
            else:
                logger.error("所有片段转写均失败")
                return None

        except Exception as e:
            logger.error(f"切片转写失败: {e}")
            return None

    async def _convert_to_mono(self, audio_file: Path) -> Optional[Path]:
        """
        转换音频为单声道16kHz格式

        Args:
            audio_file: 原音频文件

        Returns:
            转换后的音频文件路径，失败返回None
        """
        try:
            # 检查是否已经是单声道16kHz
            check_cmd = [
                'ffprobe', '-v', 'error',
                '-select_streams', 'a:0',
                '-show_entries', 'stream=channels,sample_rate',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                str(audio_file)
            ]

            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(check_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
            )

            if result.returncode == 0:
                info = result.stdout.decode('utf-8').strip().split('\n')
                if len(info) >= 2:
                    channels = int(info[0].strip())
                    sample_rate = int(info[1].strip())

                    # 如果已经符合要求，直接返回原文件
                    if channels == 1 and sample_rate == 16000:
                        logger.debug("音频已是单声道16kHz，无需转换")
                        return audio_file

            # 需要转换
            logger.debug("转换为单声道16kHz...")
            mono_file = audio_file.with_suffix('.mono.wav')

            cmd = [
                'ffmpeg', '-i', str(audio_file),
                '-ac', '1',  # 单声道
                '-ar', '16000',  # 16kHz采样率
                '-acodec', 'pcm_s16le',
                '-y',
                str(mono_file)
            ]

            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
            )

            if result.returncode == 0:
                return mono_file
            else:
                logger.error(f"音频转换失败: {result.stderr.decode()}")
                return None

        except Exception as e:
            logger.error(f"音频转换异常: {e}")
            return None

    def _get_audio_duration(self, audio_path: str) -> float:
        """获取音频时长（秒）"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                audio_path
            ]

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10
            )

            if result.returncode == 0:
                duration = float(result.stdout.decode('utf-8').strip())
                return duration
            else:
                logger.warning(f"无法获取音频时长: {audio_path}")
                return 0.0

        except Exception as e:
            logger.warning(f"获取音频时长失败: {e}")
            return 0.0

    async def transcribe_from_audio_extraction(
        self,
        video_id: str,
        aweme_id: str,
        audio_path: str
    ) -> Optional[dict]:
        """
        从已提取的音频进行转写

        Args:
            video_id: 数据库中的视频ID
            aweme_id: 抖音视频ID
            audio_path: 音频文件路径

        Returns:
            转写结果
        """
        return await self.transcribe_audio(audio_path, aweme_id)


# 创建全局实例
transcriber = Transcriber()
