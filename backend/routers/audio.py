# -*- encoding: utf-8 -*-
"""
音频提取API路由
"""

import asyncio
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from loguru import logger

from backend.db.database import get_db
from backend.db import crud
from backend.db.models import Video, AudioExtraction
from backend.services.audio_extractor import audio_extractor

router = APIRouter()


# ==================== 请求模型 ====================

class ExtractAudioRequest(BaseModel):
    """提取音频请求"""
    video_ids: list[int]  # 视频ID列表


class ExtractAudioResponse(BaseModel):
    """提取音频响应"""
    success: bool
    message: str
    count: int


# ==================== API端点 ====================

@router.post("/extract")
async def extract_audio(
    request: ExtractAudioRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    批量提取视频音频

    从视频中提取音频轨道，保存为MP3文件
    """
    # 获取视频信息
    videos = []
    for video_id in request.video_ids:
        video = db.query(Video).filter(Video.id == video_id).first()
        if video and video.download_url:
            videos.append({
                'id': video.id,
                'aweme_id': video.aweme_id,
                'download_url': video.download_url
            })

    if not videos:
        raise HTTPException(status_code=404, detail="未找到有效视频")

    # 后台任务处理
    def extract_task():
        asyncio.run(_extract_audio_batch(videos, db))

    background_tasks.add_task(extract_task)

    return ExtractAudioResponse(
        success=True,
        message=f"正在提取 {len(videos)} 个视频的音频",
        count=len(videos)
    )


@router.get("/videos/{video_id}/audio")
async def get_video_audio(video_id: int, db: Session = Depends(get_db)):
    """获取视频的音频提取状态"""
    # 检查视频是否存在
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    # 获取音频提取记录
    extraction = crud.get_audio_extraction_by_video(db, video_id)

    if not extraction:
        return {
            "video_id": video_id,
            "aweme_id": video.aweme_id,
            "has_audio": False,
            "audio_path": None,
            "audio_url": None,
            "status": "not_extracted"
        }

    # 将本地文件路径转换为HTTP URL
    audio_url = None
    if extraction.audio_path:
        # 提取文件名并构建HTTP URL
        import os
        filename = os.path.basename(extraction.audio_path)
        audio_url = f"/static/audio/{filename}"

    return {
        "video_id": video_id,
        "aweme_id": video.aweme_id,
        "has_audio": extraction.status == "completed",
        "audio_path": extraction.audio_path,
        "audio_url": audio_url,
        "status": extraction.status,
        "duration": extraction.duration,
        "file_size": extraction.file_size,
        "error_message": extraction.error_message
    }


@router.get("/extractions")
async def get_audio_extractions(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """获取所有音频提取记录"""
    extractions = crud.get_all_audio_extractions(db, limit, offset)
    return {
        "total": len(extractions),
        "extractions": [e.to_dict() for e in extractions]
    }


@router.delete("/extractions/{extraction_id}")
async def delete_audio_extraction(extraction_id: int, db: Session = Depends(get_db)):
    """删除音频提取记录"""
    success = crud.delete_audio_extraction(db, extraction_id)
    if not success:
        raise HTTPException(status_code=404, detail="记录不存在")
    return {"success": True, "message": "删除成功"}


# ==================== 后台任务 ====================

async def _extract_audio_batch(videos: list[dict], db: Session):
    """
    批量提取音频的后台任务

    Args:
        videos: 视频列表 [{id, aweme_id, download_url}]
        db: 数据库会话
    """
    total = len(videos)
    success_count = 0

    logger.info(f"开始批量音频提取任务，共 {total} 个视频")

    for idx, video_info in enumerate(videos, 1):
        video_id = video_info['id']
        aweme_id = video_info['aweme_id']
        download_url = video_info['download_url']

        try:
            # 创建或更新提取记录
            existing_extraction = crud.get_audio_extraction_by_video(db, video_id)

            if existing_extraction and existing_extraction.status == "completed":
                logger.info(f"跳过已提取的视频: {aweme_id}")
                continue

            # 更新状态为处理中
            if existing_extraction:
                extraction = crud.update_audio_extraction(
                    db, existing_extraction,
                    status="processing",
                    error_message=""
                )
            else:
                extraction = crud.create_audio_extraction(
                    db, video_id,
                    status="processing"
                )

            # 执行提取
            result = await audio_extractor.extract_audio_from_url(
                download_url,
                aweme_id
            )

            if result['success']:
                # 更新为成功
                crud.update_audio_extraction(
                    db, extraction,
                    audio_path=result['audio_path'],
                    file_size=result['file_size'],
                    duration=result['duration'],
                    status="completed",
                    error_message=""
                )
                success_count += 1
                logger.info(f"[{idx}/{total}] 音频提取成功: {aweme_id}")
            else:
                # 更新为失败
                crud.update_audio_extraction(
                    db, extraction,
                    status="failed",
                    error_message=result.get('error', 'Unknown error')[:500]
                )
                logger.error(f"[{idx}/{total}] 音频提取失败: {aweme_id} - {result.get('error')}")

        except Exception as e:
            logger.error(f"[{idx}/{total}] 处理视频异常: {aweme_id} - {e}")
            # 标记为失败
            try:
                existing_extraction = crud.get_audio_extraction_by_video(db, video_id)
                if existing_extraction:
                    crud.update_audio_extraction(
                        db, existing_extraction,
                        status="failed",
                        error_message=str(e)[:500]
                    )
            except:
                pass

        # 添加短暂延迟
        await asyncio.sleep(1)

    logger.info(f"批量音频提取任务完成: {success_count}/{total} 成功")
