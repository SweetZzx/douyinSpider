# -*- encoding: utf-8 -*-
"""
音频提取服务模块
"""

import os
import asyncio
import subprocess
from typing import Optional
from pathlib import Path
from loguru import logger
import httpx


class AudioExtractor:
    """音频提取器 - 从抖音视频中提取音频"""

    def __init__(self, output_dir: str = "./extracted_audio"):
        """
        初始化音频提取器

        Args:
            output_dir: 音频输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"音频提取器初始化完成，输出目录: {self.output_dir}")

    async def extract_audio_from_url(
        self,
        video_url: str,
        video_id: str,
        output_format: str = "mp3"
    ) -> Optional[dict]:
        """
        从视频URL提取音频

        Args:
            video_url: 视频下载链接
            video_id: 视频ID（用于命名输出文件）
            output_format: 输出格式 (mp3/wav)

        Returns:
            提取结果 {
                "success": True/False,
                "audio_path": "音频文件路径",
                "duration": 时长(秒),
                "file_size": 文件大小(字节),
                "error": 错误信息
            }
        """
        temp_video = None
        try:
            # 文件路径
            temp_video = self.output_dir / f"temp_{video_id}.mp4"
            output_audio = self.output_dir / f"{video_id}.{output_format}"

            # 如果音频文件已存在，直接返回
            if output_audio.exists():
                logger.info(f"音频文件已存在: {output_audio}")
                return {
                    "success": True,
                    "audio_path": str(output_audio),
                    "duration": self._get_audio_duration(str(output_audio)),
                    "file_size": output_audio.stat().st_size,
                    "error": None
                }

            # 1. 下载视频
            logger.info(f"正在下载视频: {video_id}")
            await self._download_video(video_url, temp_video)

            # 检查视频文件是否有效
            if not temp_video.exists() or temp_video.stat().st_size < 1000:
                raise Exception(f"下载的视频文件无效或太小: {temp_video.stat().st_size if temp_video.exists() else 0} bytes")

            # 2. 提取音频
            logger.info(f"正在提取音频: {video_id}")
            duration = await self._extract_audio(str(temp_video), str(output_audio), output_format)

            # 3. 获取文件大小
            file_size = output_audio.stat().st_size

            # 4. 清理临时视频文件
            temp_video.unlink()

            logger.success(f"音频提取成功: {output_audio} (时长: {duration:.2f}秒, 大小: {file_size}字节)")

            return {
                "success": True,
                "audio_path": str(output_audio),
                "duration": duration,
                "file_size": file_size,
                "error": None
            }

        except Exception as e:
            logger.error(f"音频提取失败: {e}")
            # 清理可能残留的临时文件
            if temp_video and temp_video.exists():
                try:
                    temp_video.unlink()
                except:
                    pass

            return {
                "success": False,
                "audio_path": None,
                "duration": 0,
                "file_size": 0,
                "error": str(e)
            }

    async def _download_video(self, url: str, output_path: Path, max_retries: int = 3):
        """下载视频文件（流式下载优化版，带重试机制）"""
        from backend.config import get_cookie

        # 获取Cookie
        cookie = get_cookie()

        for attempt in range(max_retries):
            try:
                timeout = httpx.Timeout(180.0, connect=60.0)

                async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                    # 设置请求头模拟浏览器
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Referer": "https://www.douyin.com/"
                    }

                    # 添加Cookie（如果有）
                    if cookie:
                        headers["Cookie"] = cookie

                    logger.info(f"尝试下载视频 (第{attempt + 1}/{max_retries}次): {url}")

                    # 使用流式下载，边下载边写入
                    async with client.stream('GET', url, headers=headers) as response:
                        response.raise_for_status()

                        downloaded_size = 0
                        # 使用异步写入
                        with open(output_path, 'wb') as f:
                            async for chunk in response.aiter_bytes(chunk_size=16384):  # 增大chunk_size到16KB
                                f.write(chunk)
                                downloaded_size += len(chunk)

                        logger.success(f"视频下载完成: {output_path.stat().st_size} 字节")
                        return

            except httpx.HTTPStatusError as e:
                logger.warning(f"下载失败 (HTTP {e.response.status_code}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                    continue
                else:
                    raise
            except Exception as e:
                logger.warning(f"下载失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                    continue
                else:
                    raise Exception(f"视频下载失败，已重试{max_retries}次")

    async def _extract_audio(
        self,
        input_path: str,
        output_path: str,
        output_format: str = "mp3"
    ) -> float:
        """
        使用FFmpeg提取音频（优化版）

        Returns:
            音频时长（秒）
        """
        try:
            # 优化：先尝试直接复制音频流（不重新编码，速度最快）
            # 检查视频中的音频格式
            check_cmd = [
                'ffprobe',
                '-v', 'error',
                '-select_streams', 'a:0',
                '-show_entries', 'stream=codec_name',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                input_path
            ]

            check_result = subprocess.run(
                check_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10
            )

            audio_codec = check_result.stdout.decode('utf-8').strip() if check_result.returncode == 0 else ''

            # FFmpeg命令 - 根据情况选择最优方案
            cmd = ['ffmpeg', '-i', input_path, '-vn', '-y']

            # 如果是mp3且输出mp3，直接copy（最快）
            if 'mp3' in audio_codec.lower() and output_format == 'mp3':
                cmd.extend(['-acodec', 'copy'])
                logger.debug(f"使用直接复制模式（原始编码: {audio_codec}）")
            # 否则需要重新编码（AAC转MP3必须重新编码）
            else:
                if output_format == 'mp3':
                    cmd.extend([
                        '-acodec', 'libmp3lame',
                        '-q:a', '4',           # 质量设置（4是中等质量，处理更快）
                    ])
                else:
                    cmd.extend(['-acodec', 'pcm_s16le'])
                logger.debug(f"使用重新编码模式（原始编码: {audio_codec} → {output_format}）")

            cmd.append(output_path)

            # 执行FFmpeg（异步执行以避免阻塞）
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=180  # 3分钟超时
                )
            )

            if result.returncode != 0:
                error_msg = result.stderr.decode('utf-8', errors='ignore')
                logger.error(f"FFmpeg错误详情:\n{error_msg}")
                raise Exception(f"FFmpeg处理失败: {error_msg}")

            # 获取音频时长
            duration = self._get_audio_duration(output_path)

            return duration

        except subprocess.TimeoutExpired:
            raise Exception("FFmpeg处理超时（超过2分钟）")
        except Exception as e:
            raise Exception(f"音频提取失败: {str(e)}")

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

    async def extract_audio_batch(
        self,
        video_list: list[dict]
    ) -> list[dict]:
        """
        批量提取音频

        Args:
            video_list: 视频列表，每个元素包含 {aweme_id, download_url}

        Returns:
            结果列表 [{aweme_id, success, audio_path, duration, file_size, error}]
        """
        results = []
        total = len(video_list)

        logger.info(f"开始批量提取音频，共 {total} 个视频")

        for idx, video in enumerate(video_list, 1):
            aweme_id = video.get('aweme_id')
            download_url = video.get('download_url')

            if not aweme_id or not download_url:
                logger.warning(f"跳过无效视频: {video}")
                results.append({
                    'aweme_id': aweme_id,
                    'success': False,
                    'audio_path': None,
                    'duration': 0,
                    'file_size': 0,
                    'error': '缺少必要参数'
                })
                continue

            logger.info(f"处理进度: {idx}/{total} - {aweme_id}")

            result = await self.extract_audio_from_url(
                download_url,
                aweme_id
            )

            results.append({
                'aweme_id': aweme_id,
                'success': result['success'],
                'audio_path': result.get('audio_path'),
                'duration': result.get('duration', 0),
                'file_size': result.get('file_size', 0),
                'error': result.get('error')
            })

            # 添加短暂延迟，避免请求过快
            await asyncio.sleep(0.5)

        success_count = sum(1 for r in results if r['success'])
        logger.info(f"批量提取完成: {success_count}/{total} 成功")

        return results


# 创建全局实例
audio_extractor = AudioExtractor()
