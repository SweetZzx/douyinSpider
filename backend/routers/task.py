# -*- encoding: utf-8 -*-
"""
任务API路由
"""

import threading
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger

from backend.config import settings, get_cookie
from backend.lib.douyin.request import Request
from backend.lib.douyin.client import DouyinClient
from backend.lib.douyin.parser import DataParser
from backend.lib.douyin.target import TargetHandler

router = APIRouter()

# 内存存储任务状态和结果
task_status = {}
task_results = {}


# ==================== 请求/响应模型 ====================

class StartTaskRequest(BaseModel):
    """启动任务请求"""
    target: str  # UP主链接或ID
    limit: int = 0  # 限制数量，0为不限


class TaskResponse(BaseModel):
    """任务响应"""
    task_id: str
    status: str
    message: str = ""


class TaskStatus(BaseModel):
    """任务状态"""
    task_id: str
    status: str  # running, completed, error
    progress: int = 0
    total: int = 0
    message: str = ""


class VideoData(BaseModel):
    """视频数据"""
    id: str
    desc: str
    author_nickname: str
    cover: str
    video_url: str
    download_url: str | list[str] = ""
    create_time: int
    digg_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    collect_count: int = 0


# ==================== API接口 ====================

@router.post("/start", response_model=TaskResponse)
def start_task(request: StartTaskRequest):
    """
    启动采集任务

    Args:
        request: 包含目标URL和限制数量

    Returns:
        任务ID和状态
    """
    # 检查Cookie
    cookie = get_cookie()
    if not cookie:
        raise HTTPException(status_code=400, detail="请先配置Cookie")

    # 生成任务ID
    task_id = f"task_{uuid.uuid4().hex[:8]}"

    # 初始化任务状态
    task_status[task_id] = {
        "id": task_id,
        "status": "running",
        "progress": 0,
        "total": 0,
        "message": "正在获取视频列表...",
        "start_time": datetime.now().isoformat(),
    }
    task_results[task_id] = []

    # 后台执行采集任务
    thread = threading.Thread(
        target=_run_crawl_task,
        args=(task_id, request.target, request.limit),
        daemon=True
    )
    thread.start()

    return TaskResponse(
        task_id=task_id,
        status="running",
        message="任务已启动"
    )


@router.get("/status")
def get_status(task_id: Optional[str] = None):
    """
    获取任务状态

    Args:
        task_id: 任务ID，如果不提供则返回所有任务

    Returns:
        任务状态信息
    """
    if task_id:
        if task_id not in task_status:
            raise HTTPException(status_code=404, detail="任务不存在")
        return task_status[task_id]
    return list(task_status.values())


@router.get("/results/{task_id}")
def get_results(task_id: str):
    """
    获取任务结果

    Args:
        task_id: 任务ID

    Returns:
        视频列表
    """
    if task_id not in task_results:
        raise HTTPException(status_code=404, detail="任务不存在")

    return task_results[task_id]


# ==================== 后台任务 ====================

def _run_crawl_task(task_id: str, target: str, limit: int):
    """
    后台采集任务

    Args:
        task_id: 任务ID
        target: 目标URL
        limit: 限制数量
    """
    try:
        cookie = get_cookie()
        req = Request(cookie=cookie)

        # 解析目标
        handler = TargetHandler(req, target, "post", settings.download_path)
        handler.parse_target_id()

        logger.info(f"[{task_id}] 目标解析完成: type={handler.type}, id={handler.id}")

        # 获取视频列表
        client = DouyinClient(req)
        max_cursor = 0
        has_more = True
        results = []
        logid = ""

        while has_more:
            items, max_cursor, logid, has_more = client.fetch_awemes_list(
                "post", handler.id, max_cursor, logid, {}
            )

            # 解析数据
            new_items, has_more = DataParser.parse_awemes(
                items, results, [], limit, has_more, "post", settings.download_path
            )

            # 更新进度
            task_status[task_id]["total"] = len(results)
            task_status[task_id]["progress"] = len(results)
            task_status[task_id]["message"] = f"已获取 {len(results)} 个视频..."

            logger.info(f"[{task_id}] 已获取 {len(results)} 个视频")

            # 检查限制
            if limit > 0 and len(results) >= limit:
                break

        # 转换结果格式
        videos = []
        for item in results:
            video = VideoData(
                id=item.get("id", ""),
                desc=item.get("desc", "无标题"),
                author_nickname=item.get("author_nickname", "未知"),
                cover=item.get("cover", ""),
                video_url=f"https://www.douyin.com/video/{item.get('id', '')}",
                download_url=item.get("download_addr", ""),
                create_time=item.get("time", 0),
                digg_count=item.get("digg_count", 0),
                comment_count=item.get("comment_count", 0),
                share_count=item.get("share_count", 0),
                collect_count=item.get("collect_count", 0),
            )
            videos.append(video.model_dump())

        # 保存结果
        task_results[task_id] = videos
        task_status[task_id]["status"] = "completed"
        task_status[task_id]["total"] = len(videos)
        task_status[task_id]["progress"] = len(videos)
        task_status[task_id]["message"] = f"采集完成，共获取 {len(videos)} 个视频"

        logger.success(f"[{task_id}] 任务完成，共 {len(videos)} 个视频")

    except Exception as e:
        logger.error(f"[{task_id}] 任务失败: {e}")
        task_status[task_id]["status"] = "error"
        task_status[task_id]["message"] = str(e)
