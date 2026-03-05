# -*- encoding: utf-8 -*-
"""
API路由 - 整合所有接口
"""

import threading
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from loguru import logger
from slowapi import Limiter

from backend.config import settings, set_cookie, get_cookie
from backend.db.database import get_db
from backend.db import crud
from backend.db.models import Author, Video, AuthorGroup
from backend.routers import audio, transcribe
from backend.lib.douyin.request import Request
from backend.lib.douyin.client import DouyinClient
from backend.lib.douyin.parser import DataParser
from backend.lib.douyin.target import TargetHandler
from backend.utils.text import extract_valid_urls
from backend.auth import get_current_user


# 速率限制器（每分钟100次请求）
limiter = Limiter(key_func=lambda r: r.client.host if r.client else "127.0.0.1")

router = APIRouter()

# 内存存储任务状态
task_status = {}
task_results = {}


# ==================== 请求模型 ====================

class AddAuthorRequest(BaseModel):
    """添加UP主请求"""
    url: str  # UP主主页链接


class SetCookieRequest(BaseModel):
    """设置Cookie请求"""
    cookie: str


class CreateGroupRequest(BaseModel):
    """创建分组请求"""
    name: str


class UpdateGroupRequest(BaseModel):
    """更新分组请求"""
    name: str


class MoveAuthorRequest(BaseModel):
    """移动UP主到分组请求"""
    group_id: Optional[int] = None  # None表示移动到未分组


class ContentRewriteRequest(BaseModel):
    """文案仿写请求"""
    original_text: str  # 原始文案


class SavePromptRequest(BaseModel):
    """保存提示词请求"""
    prompt: str  # 提示词内容


class VideoRewriteRequest(BaseModel):
    """视频文案仿写请求"""
    video_id: int


# ==================== 基础接口 ====================

@router.get("")
def api_info():
    """API信息"""
    return {"name": settings.app_name, "version": settings.app_version}


@router.get("/health")
def health_check():
    """健康检查"""
    return {"status": "ok"}


@router.get("/settings")
async def get_settings_api(user: dict = Depends(get_current_user)):
    """获取设置"""
    return {
        "cookie_configured": bool(settings.cookie),
        "download_path": settings.download_path,
    }


@router.get("/settings/cookie/verify")
async def verify_cookie(user: dict = Depends(get_current_user)):
    """验证Cookie是否有效"""
    cookie = get_cookie()
    if not cookie:
        return {"valid": False, "message": "未配置Cookie"}

    try:
        req = Request(cookie=cookie)
        client = DouyinClient(req)

        # 尝试获取一个公开的用户视频列表来验证Cookie
        # 使用一个已知的公开用户ID进行测试
        test_user_id = "MS4wLjABAAAAiGywoJJrulAYh3vmkMdRbmdv_WRSjFms2t6Mwmf7iEzEp_iOyKZdqO9z2M3Bi68B"
        items, _, _, _ = client.fetch_awemes_list("post", test_user_id, 0, "", {})

        if items:
            return {"valid": True, "message": "Cookie有效"}
        else:
            return {"valid": False, "message": "Cookie可能已过期，无法获取数据"}

    except Exception as e:
        error_str = str(e)

        # 区分网络错误和真正的Cookie错误
        network_errors = [
            'SSLError', 'SSL:UNEXPECTED_EOF', 'EOF occurred in violation',
            'Connection', 'Timeout', 'Network', 'DNS',
            'Max retries exceeded', 'RemoteDisconnected'
        ]

        is_network_error = any(err in error_str for err in network_errors)

        if is_network_error:
            logger.warning(f"Cookie验证遇到网络错误: {e}")
            return {
                "valid": True,
                "message": "Cookie有效（但网络连接不稳定，暂时无法验证）"
            }
        else:
            # 真正的Cookie错误（如认证失败）
            logger.error(f"Cookie验证失败（Cookie问题）: {e}")
            return {"valid": False, "message": f"Cookie无效或已过期: {error_str[:50]}"}


@router.post("/settings/cookie")
@limiter.limit("20/minute")  # 每分钟最多20次设置Cookie
async def set_cookie_api(
    request: Request,
    data: Optional[SetCookieRequest] = None,
    cookie: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """设置Cookie - 支持query参数和request body两种方式"""
    # 优先使用request body，如果没有则使用query参数
    cookie_value = data.cookie if data else cookie

    if not cookie_value:
        raise HTTPException(status_code=400, detail="Cookie不能为空")

    set_cookie(cookie_value)
    return {"success": True, "message": "Cookie已保存"}


# ==================== 文案仿写提示词配置 ====================

@router.get("/settings/rewrite-prompt")
async def get_rewrite_prompt(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """获取文案仿写提示词"""
    from backend.config import DEFAULT_REWRITE_PROMPT

    config = crud.get_system_config(db, "rewrite_prompt")
    if config and config.value:
        return {"success": True, "prompt": config.value}
    else:
        # 返回默认提示词
        return {"success": True, "prompt": DEFAULT_REWRITE_PROMPT}


@router.post("/settings/rewrite-prompt")
async def save_rewrite_prompt(
    data: SavePromptRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """保存文案仿写提示词"""
    if not data.prompt or not data.prompt.strip():
        raise HTTPException(status_code=400, detail="提示词不能为空")

    crud.upsert_system_config(
        db,
        key="rewrite_prompt",
        value=data.prompt.strip(),
        description="文案仿写AI提示词",
        category="ai"
    )
    return {"success": True, "message": "提示词保存成功"}


@router.post("/settings/rewrite-prompt/reset")
async def reset_rewrite_prompt(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """重置为默认提示词"""
    from backend.config import DEFAULT_REWRITE_PROMPT

    crud.upsert_system_config(
        db,
        key="rewrite_prompt",
        value=DEFAULT_REWRITE_PROMPT,
        description="文案仿写AI提示词",
        category="ai"
    )
    return {"success": True, "message": "已重置为默认提示词"}


# ==================== 模型配置 ====================

class TranscribeModelConfig(BaseModel):
    """语音转写模型配置"""
    api_base: str  # API地址
    api_key: str  # API密钥
    model: str  # 模型名称


class RewriteModelConfig(BaseModel):
    """文案仿写模型配置"""
    api_base: str  # API地址
    api_key: str  # API密钥
    model: str  # 模型名称


@router.get("/settings/models")
async def get_model_config(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """获取模型配置"""
    from backend.config import settings

    # 语音转写配置
    transcribe_api_base = crud.get_system_config(db, "transcribe_api_base")
    transcribe_api_key = crud.get_system_config(db, "transcribe_api_key")
    transcribe_model = crud.get_system_config(db, "transcribe_model")

    # 文案仿写配置
    rewrite_api_base = crud.get_system_config(db, "rewrite_api_base")
    rewrite_api_key = crud.get_system_config(db, "rewrite_api_key")
    rewrite_model = crud.get_system_config(db, "rewrite_model")

    return {
        "success": True,
        "transcribe": {
            "api_base": transcribe_api_base.value if transcribe_api_base else "",
            "api_key": transcribe_api_key.value if transcribe_api_key else "",
            "model": transcribe_model.value if transcribe_model else "paraformer-zh",
        },
        "rewrite": {
            "api_base": rewrite_api_base.value if rewrite_api_base else settings.zhipu_api_base,
            "api_key": rewrite_api_key.value if rewrite_api_key else settings.zhipu_api_key[:20] + "...",  # 隐藏完整密钥
            "model": rewrite_model.value if rewrite_model else settings.zhipu_model,
        }
    }


@router.post("/settings/models/transcribe")
async def save_transcribe_model_config(
    data: TranscribeModelConfig,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """保存语音转写模型配置"""
    crud.upsert_system_config(
        db,
        key="transcribe_api_base",
        value=data.api_base.strip(),
        description="语音转写API地址",
        category="model"
    )

    crud.upsert_system_config(
        db,
        key="transcribe_api_key",
        value=data.api_key.strip(),
        description="语音转写API密钥",
        category="model"
    )

    crud.upsert_system_config(
        db,
        key="transcribe_model",
        value=data.model.strip(),
        description="语音转写模型",
        category="model"
    )

    return {"success": True, "message": "语音转写模型配置保存成功"}


@router.post("/settings/models/rewrite")
async def save_rewrite_model_config(
    data: RewriteModelConfig,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """保存文案仿写模型配置"""
    crud.upsert_system_config(
        db,
        key="rewrite_api_base",
        value=data.api_base.strip(),
        description="文案仿写API地址",
        category="model"
    )

    crud.upsert_system_config(
        db,
        key="rewrite_api_key",
        value=data.api_key.strip(),
        description="文案仿写API密钥",
        category="model"
    )

    crud.upsert_system_config(
        db,
        key="rewrite_model",
        value=data.model.strip(),
        description="文案仿写模型",
        category="model"
    )

    return {"success": True, "message": "文案仿写模型配置保存成功"}


# ==================== 分组管理 ====================

@router.get("/groups")
async def get_groups(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """获取所有分组"""
    groups = crud.get_all_groups(db)
    return [g.to_dict() for g in groups]


@router.post("/groups")
async def create_group(
    data: CreateGroupRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """创建分组"""
    group = crud.create_group(db, data.name)
    return {"success": True, "group": group.to_dict()}


@router.put("/groups/{group_id}")
async def update_group(
    group_id: int,
    data: UpdateGroupRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """更新分组名称"""
    group = crud.get_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")
    group = crud.update_group(db, group, name=data.name)
    return {"success": True, "group": group.to_dict()}


@router.delete("/groups/{group_id}")
async def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """删除分组"""
    success = crud.delete_group(db, group_id)
    if not success:
        raise HTTPException(status_code=404, detail="分组不存在")
    return {"success": True, "message": "删除成功"}


@router.put("/authors/{author_id}/group")
async def move_author_to_group(
    author_id: int,
    data: MoveAuthorRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """移动UP主到分组"""
    success = crud.move_author_to_group(db, author_id, data.group_id)
    if not success:
        raise HTTPException(status_code=404, detail="UP主不存在")
    return {"success": True, "message": "移动成功"}


# ==================== UP主管理 ====================

@router.get("/authors")
async def get_authors(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """获取所有UP主列表"""
    authors = crud.get_all_authors(db)
    return [a.to_dict() for a in authors]


@router.post("/authors")
async def add_author(
    data: AddAuthorRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """添加UP主"""
    cookie = get_cookie()
    if not cookie:
        raise HTTPException(status_code=400, detail="请先配置Cookie")

    try:
        # 从输入中提取有效URL（处理手机分享的文本）
        url = extract_valid_urls(data.url)
        if not url:
            raise HTTPException(status_code=400, detail="无法识别有效的链接")

        # 解析URL获取目标信息
        req = Request(cookie=cookie)
        handler = TargetHandler(req, url, "post", settings.download_path)
        handler.parse_target_id()

        client = DouyinClient(req)
        sec_user_id = None

        # 如果是单个视频链接，从视频中获取作者ID
        if handler.type == "aweme":
            logger.info(f"检测到视频链接，正在获取作者信息: {handler.id}")
            aweme_detail = client.fetch_aweme_detail(handler.id)
            author_info = aweme_detail.get("author", {})
            sec_user_id = author_info.get("sec_uid", "")
            nickname = author_info.get("nickname", "未知用户")
            signature = author_info.get("signature", "")
            avatar_thumb = author_info.get("avatar_thumb", {})
            avatar_list = avatar_thumb.get("url_list", []) if avatar_thumb else []
            avatar = avatar_list[0] if avatar_list else ""
        else:
            # 用户主页链接
            sec_user_id = handler.id
            if not sec_user_id:
                raise HTTPException(status_code=400, detail="无法解析UP主ID")

            # 通过API获取UP主信息（从第一个视频获取）
            items, _, _, _ = client.fetch_awemes_list("post", sec_user_id, 0, "", {})

            nickname = "未知用户"
            avatar = ""
            signature = ""

            if items:
                # 从第一个视频中提取作者信息
                first_item = items[0]
                if first_item.get("aweme_info"):
                    first_item = first_item["aweme_info"]

                author_info = first_item.get("author", {})
                nickname = author_info.get("nickname", "未知用户")
                signature = author_info.get("signature", "")

                avatar_thumb = author_info.get("avatar_thumb", {})
                avatar_list = avatar_thumb.get("url_list", []) if avatar_thumb else []
                avatar = avatar_list[0] if avatar_list else ""

                logger.info(f"获取UP主信息: {nickname}")

        if not sec_user_id:
            raise HTTPException(status_code=400, detail="无法获取UP主ID")

        # 检查是否已存在
        existing = crud.get_author_by_sec_id(db, sec_user_id)
        if existing:
            return {"success": True, "author": existing.to_dict(), "message": "UP主已存在"}

        # 创建UP主
        author = crud.create_author(
            db,
            sec_user_id=sec_user_id,
            nickname=nickname,
            avatar=avatar,
            signature=signature,
        )

        # 后台爬取视频（首次添加，不标记为新视频）
        thread = threading.Thread(
            target=_crawl_author_videos,
            args=(sec_user_id, author.id, cookie, db),
            kwargs={"mark_as_new": False},
            daemon=True
        )
        thread.start()

        return {"success": True, "author": author.to_dict(), "message": "UP主添加成功，正在获取视频..."}

    except Exception as e:
        logger.error(f"添加UP主失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/authors/{author_id}")
async def delete_author(
    author_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """删除UP主"""
    success = crud.delete_author(db, author_id)
    if not success:
        raise HTTPException(status_code=404, detail="UP主不存在")
    return {"success": True, "message": "删除成功"}


@router.post("/authors/{author_id}/refresh")
async def refresh_author(
    author_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """刷新UP主视频"""
    author = crud.get_author_by_id(db, author_id)
    if not author:
        raise HTTPException(status_code=404, detail="UP主不存在")

    cookie = get_cookie()
    if not cookie:
        raise HTTPException(status_code=400, detail="请先配置Cookie")

    # 后台爬取
    thread = threading.Thread(
        target=_crawl_author_videos,
        args=(author.sec_user_id, author.id, cookie, db),
        daemon=True
    )
    thread.start()

    return {"success": True, "message": "正在刷新视频..."}


# ==================== 视频检查 ====================

@router.post("/videos/check")
async def check_new_videos(user: dict = Depends(get_current_user)):
    """手动触发检查所有UP主的新视频"""
    from backend.services.scheduler import check_new_videos

    cookie = get_cookie()
    if not cookie:
        raise HTTPException(status_code=400, detail="请先配置Cookie")

    # 后台执行检查
    thread = threading.Thread(target=check_new_videos, daemon=True)
    thread.start()

    return {"success": True, "message": "正在检查新视频..."}


# ==================== 视频管理 ====================

@router.get("/videos")
async def get_videos(
    author_id: Optional[int] = None,
    group_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """获取视频列表"""
    if author_id:
        videos = crud.get_videos_by_author(db, author_id)
        total = len(videos)
    elif group_id is not None:
        videos = crud.get_videos_by_group(db, group_id, limit, offset)
        total = crud.count_videos_by_group(db, group_id)
    else:
        videos = crud.get_all_videos(db, limit, offset)
        total = crud.count_videos(db)

    new_count = crud.count_new_videos(db)

    return {
        "total": total,
        "new_count": new_count,
        "videos": [v.to_dict() for v in videos],
    }


@router.get("/videos/new")
async def get_new_videos(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """获取新视频（用于提醒）"""
    videos = crud.get_new_videos(db)
    return {"count": len(videos), "videos": [v.to_dict() for v in videos]}


@router.post("/videos/{video_id}/read")
async def mark_video_read(
    video_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """标记视频为已读"""
    success = crud.mark_video_as_read(db, video_id)
    if not success:
        raise HTTPException(status_code=404, detail="视频不存在")
    return {"success": True}


@router.post("/videos/read-all")
async def mark_all_read(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """标记所有视频为已读"""
    count = crud.mark_all_videos_as_read(db)
    return {"success": True, "count": count}


# ==================== 数据看板 ====================

@router.get("/dashboard")
async def get_dashboard(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """获取数据看板"""
    authors = crud.get_all_authors(db)
    new_videos = crud.get_new_videos(db)
    total_videos = crud.count_videos(db)

    return {
        "author_count": len(authors),
        "video_count": total_videos,
        "new_video_count": len(new_videos),
        "new_videos": [v.to_dict() for v in new_videos[:10]],  # 最近10个新视频
    }


# ==================== 后台爬取任务 ====================

def _crawl_author_videos(sec_user_id: str, author_id: int, cookie: str, db: Session, mark_as_new: bool = True):
    """
    后台爬取UP主视频

    Args:
        sec_user_id: UP主的sec_user_id
        author_id: 数据库中的UP主ID
        cookie: Cookie字符串
        db: 数据库会话
        mark_as_new: 是否将新视频标记为"新视频"（首次添加UP主时应为False）
    """
    try:
        req = Request(cookie=cookie)
        client = DouyinClient(req)

        max_cursor = 0
        has_more = True
        latest_time = 0
        new_count = 0

        while has_more:
            items, max_cursor, _, has_more = client.fetch_awemes_list(
                "post", sec_user_id, max_cursor, "", {}
            )

            for item in items:
                if item.get("aweme_info"):
                    item = item["aweme_info"]

                aweme_id = item.get("aweme_id", item.get("awemeId"))
                if not aweme_id:
                    continue

                # 检查是否已存在
                existing = crud.get_video_by_aweme_id(db, aweme_id)
                if existing:
                    # 如果是增量更新（mark_as_new=True），遇到已存在视频则提前退出
                    # 因为视频列表是按时间倒序排列的，后面的肯定都存在
                    if mark_as_new:
                        logger.info(f"遇到已存在视频 {aweme_id}，提前结束检查")
                        has_more = False
                        break
                    continue

                # 解析视频数据
                create_time = item.get("create_time", item.get("createTime", 0))
                if create_time > latest_time:
                    latest_time = create_time

                # 获取下载链接
                video = item.get("video", {})
                play_addr = video.get("play_addr")
                if play_addr:
                    download_url = play_addr.get("url_list", [""])[-1]
                else:
                    download_url = ""

                # 获取封面
                cover = video.get("cover", {})
                cover_url = cover.get("url_list", [""])[-1] if cover else ""

                # 保存到数据库
                crud.create_video(
                    db,
                    author_id=author_id,
                    aweme_id=aweme_id,
                    desc=item.get("desc", "")[:500],
                    cover=cover_url,
                    video_url=f"https://www.douyin.com/video/{aweme_id}",
                    download_url=download_url,
                    create_time=create_time,
                    duration=video.get("duration", 0),
                    digg_count=item.get("statistics", {}).get("digg_count", 0),
                    comment_count=item.get("statistics", {}).get("comment_count", 0),
                    share_count=item.get("statistics", {}).get("share_count", 0),
                    collect_count=item.get("statistics", {}).get("collect_count", 0),
                    is_new=mark_as_new,  # 根据参数决定是否标记为新视频
                )
                new_count += 1
                logger.info(f"新视频: {aweme_id} - {item.get('desc', '')[:30]}")

            logger.info(f"已爬取 {new_count} 个新视频")

        # 更新UP主信息
        author = crud.get_author_by_id(db, author_id)
        if author:
            crud.update_author(
                db, author,
                latest_video_time=latest_time,
                video_count=author.video_count + new_count
            )

        logger.success(f"UP主 {sec_user_id} 爬取完成，新增 {new_count} 个视频")

    except Exception as e:
        logger.error(f"爬取失败: {e}")


# ==================== 兼容旧接口 ====================

@router.post("/task/start")
def start_task(data: AddAuthorRequest):
    """兼容旧接口：启动任务爬取"""
    cookie = get_cookie()
    if not cookie:
        raise HTTPException(status_code=400, detail="请先配置Cookie")

    task_id = f"task_{uuid.uuid4().hex[:8]}"
    task_status[task_id] = {
        "id": task_id,
        "status": "running",
        "progress": 0,
        "total": 0,
        "message": "正在获取视频列表...",
    }
    task_results[task_id] = []

    def _run():
        try:
            req = Request(cookie=cookie)
            handler = TargetHandler(req, data.url, "post", settings.download_path)
            handler.parse_target_id()

            client = DouyinClient(req)
            max_cursor = 0
            has_more = True
            results = []

            while has_more:
                items, max_cursor, _, has_more = client.fetch_awemes_list(
                    "post", handler.id, max_cursor, "", {}
                )
                DataParser.parse_awemes(items, results, [], 0, has_more, "post", "")

                task_status[task_id]["total"] = len(results)
                task_status[task_id]["progress"] = len(results)

            # 转换结果
            videos = []
            for item in results:
                videos.append({
                    "id": item.get("id", ""),
                    "desc": item.get("desc", ""),
                    "author_nickname": item.get("author_nickname", ""),
                    "cover": item.get("cover", ""),
                    "video_url": f"https://www.douyin.com/video/{item.get('id', '')}",
                    "download_url": item.get("download_addr", ""),
                    "create_time": item.get("time", 0),
                    "digg_count": item.get("digg_count", 0),
                    "comment_count": item.get("comment_count", 0),
                })

            task_results[task_id] = videos
            task_status[task_id]["status"] = "completed"
            task_status[task_id]["total"] = len(videos)

        except Exception as e:
            task_status[task_id]["status"] = "error"
            task_status[task_id]["message"] = str(e)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    return {"task_id": task_id, "status": "running"}


@router.get("/task/status")
def get_task_status(task_id: Optional[str] = None):
    """获取任务状态"""
    if task_id:
        return task_status.get(task_id, {})
    return list(task_status.values())


@router.get("/task/results/{task_id}")
def get_task_results(task_id: str):
    """获取任务结果"""
    if task_id not in task_results:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task_results[task_id]


# ==================== 注册子路由 ====================

# 音频提取路由
router.include_router(audio.router, prefix="/audio", tags=["Audio"])

# 语音转写路由
router.include_router(transcribe.router, prefix="/transcribe", tags=["Transcribe"])


# ==================== 文案仿写 ====================

class VideoRewriteRequest(BaseModel):
    """视频文案仿写请求"""
    video_id: int


@router.post("/content-rewrite")
async def rewrite_content(
    data: ContentRewriteRequest,
    user: dict = Depends(get_current_user)
):
    """文案仿写接口（纯文本，不保存）"""
    from backend.services.content_rewrite import content_rewrite_service

    if not data.original_text or not data.original_text.strip():
        raise HTTPException(status_code=400, detail="原文案不能为空")

    try:
        rewritten_text = await content_rewrite_service.rewrite(data.original_text.strip())
        return {
            "success": True,
            "original_text": data.original_text,
            "rewritten_text": rewritten_text
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"文案仿写失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/videos/{video_id}/rewrite")
async def rewrite_video_content(
    video_id: int,
    template_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """视频文案仿写接口（保存到数据库）"""
    from backend.services.content_rewrite import content_rewrite_service

    # 获取视频
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    # 获取转写文本
    transcript = crud.get_transcript_by_video(db, video.id)
    if not transcript or not transcript.text:
        raise HTTPException(status_code=400, detail="请先提取文案")

    original_text = transcript.text

    try:
        # 如果指定了模板ID，使用模板内容
        if template_id:
            template = crud.get_prompt_template_by_id(db, template_id)
            if template and template.content:
                rewritten_text = await content_rewrite_service.rewrite_with_prompt(
                    original_text,
                    template.content
                )
            else:
                # 模板不存在，使用默认方法
                rewritten_text = await content_rewrite_service.rewrite(original_text)
        else:
            # 调用仿写服务
            rewritten_text = await content_rewrite_service.rewrite(original_text)

        # 保存到数据库
        crud.save_video_rewrite(db, video.id, rewritten_text)

        return {
            "success": True,
            "video_id": video.id,
            "original_text": original_text,
            "rewritten_text": rewritten_text
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"文案仿写失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class UpdateRewriteRequest(BaseModel):
    """更新仿写文案请求"""
    rewritten_text: str
    prompt: Optional[str] = None


class PromptTemplateRequest(BaseModel):
    """提示词模板请求"""
    name: str
    content: str
    description: str = ""
    category: str = "rewrite"
    is_default: bool = False
    sort_order: int = 0


class UpdatePromptTemplateRequest(BaseModel):
    """更新提示词模板请求"""
    name: Optional[str] = None
    content: Optional[str] = None
    description: Optional[str] = None
    is_default: Optional[bool] = None
    sort_order: Optional[int] = None


@router.put("/videos/{video_id}/rewrite")
async def update_video_rewrite(
    video_id: int,
    data: UpdateRewriteRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """手动更新视频的仿写文案"""
    # 获取视频
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    # 如果提供了prompt，进行智能纠错
    if data.prompt and data.prompt.strip():
        from backend.services.content_rewrite import content_rewrite_service
        try:
            rewritten_text = await content_rewrite_service.rewrite_with_prompt(
                data.rewritten_text.strip(),
                data.prompt.strip()
            )
        except Exception as e:
            logger.error(f"智能纠错失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    else:
        rewritten_text = data.rewritten_text.strip()

    # 保存到数据库
    crud.save_video_rewrite(db, video.id, rewritten_text)

    return {
        "success": True,
        "message": "仿写文案保存成功",
        "rewritten_text": rewritten_text
    }


# ==================== 提示词模板管理 ====================

@router.get("/prompt-templates")
async def get_prompt_templates(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """获取提示词模板列表

    Args:
        category: 可选，筛选指定分类的模板。不传则返回所有分类。
    """
    templates = crud.get_all_prompt_templates(db, category)
    return {
        "success": True,
        "templates": [t.to_dict() for t in templates]
    }


@router.post("/prompt-templates")
async def create_prompt_template(
    data: PromptTemplateRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """创建提示词模板"""
    template = crud.create_prompt_template(
        db,
        name=data.name,
        content=data.content,
        description=data.description,
        category=data.category,
        is_default=data.is_default,
        sort_order=data.sort_order
    )
    return {
        "success": True,
        "template": template.to_dict(),
        "message": "提示词模板创建成功"
    }


@router.get("/prompt-templates/{template_id}")
async def get_prompt_template(
    template_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """获取单个提示词模板"""
    template = crud.get_prompt_template_by_id(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    return {
        "success": True,
        "template": template.to_dict()
    }


@router.put("/prompt-templates/{template_id}")
async def update_prompt_template(
    template_id: int,
    data: UpdatePromptTemplateRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """更新提示词模板"""
    template = crud.get_prompt_template_by_id(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    # 获取非None的字段
    update_data = {k: v for k, v in data.dict().items() if v is not None}

    try:
        template = crud.update_prompt_template(db, template, **update_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "success": True,
        "template": template.to_dict(),
        "message": "提示词模板更新成功"
    }


@router.delete("/prompt-templates/{template_id}")
async def delete_prompt_template(
    template_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """删除提示词模板"""
    try:
        crud.delete_prompt_template(db, template_id)
        return {
            "success": True,
            "message": "提示词模板删除成功"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=404, detail="模板不存在")


@router.post("/prompt-templates/{template_id}/set-default")
async def set_default_template(
    template_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """设置默认模板"""
    template = crud.get_prompt_template_by_id(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    template = crud.update_prompt_template(db, template, is_default=True)

    return {
        "success": True,
        "template": template.to_dict(),
        "message": "已设置为默认模板"
    }


@router.post("/prompt-templates/{template_id}/copy")
async def copy_prompt_template(
    template_id: int,
    new_name: Optional[str] = None,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """复制提示词模板"""
    template = crud.get_prompt_template_by_id(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    try:
        new_template = crud.copy_prompt_template(db, template_id, new_name)
        return {
            "success": True,
            "template": new_template.to_dict(),
            "message": "提示词模板复制成功"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== AI对话 ====================

class ChatRequest(BaseModel):
    """对话请求"""
    message: str  # 用户消息
    history: list[dict[str, str]] = []  # 对话历史
    custom_prompt: str = ""  # 自定义提示词（可选）


@router.post("/chat")
async def chat_with_ai(
    request: ChatRequest,
    user: dict = Depends(get_current_user)
):
    """与AI对话"""
    try:
        from backend.services.content_rewrite import content_rewrite_service
        from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

        # 构建消息列表
        messages = []

        # 添加系统提示词（如果有自定义提示词则使用自定义的）
        if request.custom_prompt and request.custom_prompt.strip():
            system_prompt = request.custom_prompt.strip()
        else:
            system_prompt = """你是一个专业的文案写作助手，擅长创作各种类型的短视频文案。

你的任务：
1. 理解用户的需求和目标受众
2. 创作吸引人、有创意的短视频文案
3. 保持文案简洁、有力、易于传播
4. 适当使用emoji，增加亲和力
5. 根据不同平台特点调整风格（抖音、快手等）

写作技巧：
- 开头要抓住注意力
- 中间内容要有价值或趣味性
- 结尾要有明确的行动召唤
- 保持口语化、接地气
- 避免过于正式或生硬的表达

请直接输出文案内容，不要包含解释或说明。"""

        messages.append(SystemMessage(content=system_prompt))

        # 添加历史对话
        for msg in request.history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

        # 添加当前消息
        messages.append(HumanMessage(content=request.message))

        # 调用AI服务
        response = await content_rewrite_service.llm.ainvoke(messages)
        ai_response = response.content.strip()

        return {
            "success": True,
            "response": ai_response
        }

    except Exception as e:
        logger.error(f"AI对话失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"对话失败: {str(e)}")
