# -*- encoding: utf-8 -*-
"""
语音转文字API路由
"""

import asyncio
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from loguru import logger

from backend.db.database import get_db
from backend.db import crud
from backend.db.models import Video, AudioExtraction, Transcript, PromptTemplate
from backend.services.transcriber import transcriber

router = APIRouter()


# ==================== 请求模型 ====================

class TranscribeRequest(BaseModel):
    """语音转写请求"""
    video_ids: list[int]  # 视频ID列表
    force: bool = False  # 是否强制重新转写（忽略已完成的记录）


class TranscribeResponse(BaseModel):
    """语音转写响应"""
    success: bool
    message: str
    count: int


class UpdateTranscriptRequest(BaseModel):
    """更新转写文案请求"""
    text: str
    correct: bool = False  # 是否进行智能纠错


# ==================== API端点 ====================

@router.post("/transcribe")
async def transcribe_videos(
    request: TranscribeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    批量转写视频语音

    对已提取音频的视频进行语音识别
    """
    # 获取视频信息
    videos = []
    for video_id in request.video_ids:
        video = db.query(Video).filter(Video.id == video_id).first()
        if video:
            # 检查是否已有音频
            audio_extraction = crud.get_audio_extraction_by_video(db, video_id)
            if audio_extraction and audio_extraction.status == "completed":
                videos.append({
                    'id': video.id,
                    'aweme_id': video.aweme_id,
                    'audio_path': audio_extraction.audio_path,
                    'force': request.force  # 传递 force 标志
                })
            else:
                logger.warning(f"视频 {video.aweme_id} 未提取音频，跳过转写")

    if not videos:
        raise HTTPException(status_code=400, detail="没有可转写的视频（请先提取音频）")

    # 后台任务处理
    def transcribe_task():
        asyncio.run(_transcribe_batch(videos, db))

    background_tasks.add_task(transcribe_task)

    return TranscribeResponse(
        success=True,
        message=f"正在转写 {len(videos)} 个视频的语音",
        count=len(videos)
    )


@router.get("/videos/{video_id}/transcript")
async def get_video_transcript(video_id: int, db: Session = Depends(get_db)):
    """获取视频的转写状态"""
    # 检查视频是否存在
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    # 获取转写记录
    transcript = crud.get_transcript_by_video(db, video_id)

    if not transcript:
        return {
            "video_id": video_id,
            "aweme_id": video.aweme_id,
            "has_transcript": False,
            "text": None,
            "segments": None,
            "status": "not_transcribed"
        }

    return {
        "video_id": video_id,
        "aweme_id": video.aweme_id,
        "has_transcript": transcript.status == "completed",
        "text": transcript.text if transcript.status == "completed" else None,
        "segments": transcript.segments if transcript.status == "completed" else None,
        "status": transcript.status,
        "language": transcript.language,
        "duration": transcript.duration,
        "confidence": transcript.confidence,
        "error_message": transcript.error_message
    }


@router.get("/transcripts")
async def get_transcripts(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """获取所有转写记录"""
    transcripts = crud.get_all_transcripts(db, limit, offset)
    return {
        "total": len(transcripts),
        "transcripts": [t.to_dict() for t in transcripts]
    }


@router.delete("/transcripts/{transcript_id}")
async def delete_transcript(transcript_id: int, db: Session = Depends(get_db)):
    """删除转写记录"""
    success = crud.delete_transcript(db, transcript_id)
    if not success:
        raise HTTPException(status_code=404, detail="记录不存在")
    return {"success": True, "message": "删除成功"}


@router.put("/videos/{video_id}/transcript")
async def update_video_transcript(
    video_id: int,
    request: UpdateTranscriptRequest,
    db: Session = Depends(get_db)
):
    """手动更新视频的转写文案"""
    # 检查视频是否存在
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    # 如果需要智能纠错
    if request.correct:
        from backend.services.content_rewrite import content_rewrite_service

        # 构建上下文信息
        video_title = video.desc or "无标题"  # desc 字段存储的是视频标题

        # 固定的智能纠错提示词（包含视频标题上下文，针对美妆品牌等专有名词优化）
        prompt = f"""视频标题：{video_title}

请对以上视频的转写文案进行智能纠错。

任务要求：
1. 修正错别字和同音字错误（如："在"→"再"，"的"→"得"，"粘"→"贴"等）
2. 修正标点符号使用（中文使用全角标点）
3. 修正语法错误，使语句通顺
4. 保持原文的意思和风格
5. 修复语音转写可能出现的断句错误

特别注意：
- 参考视频标题来识别和保留品牌名、产品名、专业术语（如：雅诗兰黛、兰蔻、粉底液、遮瑕膏等）
- 对于美妆、时尚领域的专有名词，即使不在常用词表中，也要保留原文
- 保持口语化风格，不要过度书面化
- 只返回纠错后的文案，不要任何解释或说明

原文案：
{request.text}

纠错后的文案："""

        try:
            corrected_text = await content_rewrite_service.rewrite_with_prompt(request.text, prompt)
            final_text = corrected_text
            logger.info(f"原文案智能纠错成功: video_id={video_id}, title={video_title}")
        except Exception as e:
            logger.error(f"智能纠错失败: {e}")
            final_text = request.text  # 纠错失败则使用原文
    else:
        final_text = request.text

    # 获取或创建转写记录
    transcript = crud.get_transcript_by_video(db, video_id)
    if transcript:
        # 更新现有记录
        crud.update_transcript(
            db, transcript,
            text=final_text,
            status="completed",
            error_message=""
        )
    else:
        # 创建新记录
        transcript = crud.create_transcript(
            db, video_id,
            text=final_text,
            status="completed"
        )

    return {
        "success": True,
        "message": "文案保存成功" if not request.correct else "智能纠错完成",
        "text": transcript.text
    }


# ==================== 后台任务 ====================

async def _transcribe_batch(videos: list[dict], db: Session):
    """
    批量转写语音的后台任务

    Args:
        videos: 视频列表 [{id, aweme_id, audio_path}]
        db: 数据库会话
    """
    total = len(videos)
    success_count = 0

    logger.info(f"开始批量语音转写任务，共 {total} 个视频")

    for idx, video_info in enumerate(videos, 1):
        video_id = video_info['id']
        aweme_id = video_info['aweme_id']
        audio_path = video_info['audio_path']

        try:
            # 创建或更新转写记录
            existing_transcript = crud.get_transcript_by_video(db, video_id)

            # 如果不是强制模式，且已转写完成，则跳过
            if not video_info.get('force', False) and existing_transcript and existing_transcript.status == "completed":
                logger.info(f"跳过已转写的视频: {aweme_id}")
                continue

            # 更新状态为处理中
            if existing_transcript:
                transcript = crud.update_transcript(
                    db, existing_transcript,
                    status="processing",
                    error_message=""
                )
            else:
                transcript = crud.create_transcript(
                    db, video_id,
                    status="processing"
                )

            # 执行转写
            result = await transcriber.transcribe_from_audio_extraction(
                str(video_id),
                aweme_id,
                audio_path
            )

            if result['success']:
                # 更新为成功
                crud.update_transcript(
                    db, transcript,
                    text=result['text'],
                    segments=result['segments'],
                    language=result.get('language', 'zh'),
                    duration=result.get('duration', 0),
                    confidence=result.get('confidence', 0),
                    status="completed",
                    error_message=""
                )
                success_count += 1
                logger.info(f"[{idx}/{total}] 语音转写成功: {aweme_id}")
            else:
                # 更新为失败
                crud.update_transcript(
                    db, transcript,
                    status="failed",
                    error_message=result.get('error', 'Unknown error')[:500]
                )
                logger.error(f"[{idx}/{total}] 语音转写失败: {aweme_id} - {result.get('error')}")

        except Exception as e:
            logger.error(f"[{idx}/{total}] 处理视频异常: {aweme_id} - {e}")
            # 标记为失败
            try:
                existing_transcript = crud.get_transcript_by_video(db, video_id)
                if existing_transcript:
                    crud.update_transcript(
                        db, existing_transcript,
                        status="failed",
                        error_message=str(e)[:500]
                    )
            except:
                pass

        # 添加短暂延迟
        await asyncio.sleep(1)

    logger.info(f"批量语音转写任务完成: {success_count}/{total} 成功")
