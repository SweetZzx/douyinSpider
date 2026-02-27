# -*- encoding: utf-8 -*-
"""
后台定时任务调度器
"""

import threading
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from backend.config import get_cookie
from backend.db.database import SessionLocal
from backend.db import crud
from backend.lib.douyin.request import Request
from backend.lib.douyin.client import DouyinClient

scheduler = BackgroundScheduler()


def check_new_videos():
    """检查所有UP主的新视频"""
    cookie = get_cookie()
    if not cookie:
        logger.warning("未配置Cookie，跳过视频检查")
        return

    db = SessionLocal()
    try:
        authors = crud.get_all_authors(db)
        if not authors:
            return

        logger.info(f"开始检查 {len(authors)} 个UP主的新视频...")

        for author in authors:
            try:
                _check_author_videos(author.sec_user_id, author.id, cookie, db)
            except Exception as e:
                logger.error(f"检查UP主 {author.nickname} 失败: {e}")

        logger.success("视频检查完成")

    except Exception as e:
        logger.error(f"检查任务失败: {e}")
    finally:
        db.close()


def _check_author_videos(sec_user_id: str, author_id: int, cookie: str, db):
    """检查单个UP主的新视频（增量检查）"""
    req = Request(cookie=cookie)
    client = DouyinClient(req)

    # 只获取最近的视频
    max_cursor = 0
    new_count = 0

    # 只检查第一页（约20个视频）
    items, _, _, _ = client.fetch_awemes_list(
        "post", sec_user_id, max_cursor, "", {}
    )

    for item in items[:20]:  # 只检查前20个
        if item.get("aweme_info"):
            item = item["aweme_info"]

        aweme_id = item.get("aweme_id", item.get("awemeId"))
        if not aweme_id:
            continue

        # 检查是否已存在
        existing = crud.get_video_by_aweme_id(db, aweme_id)
        if existing:
            # 视频列表是按时间倒序排列的，遇到已存在视频则提前退出
            # 因为后面的视频肯定也都存在
            logger.info(f"遇到已存在视频 {aweme_id}，跳过后续检查")
            break

        # 解析视频数据
        create_time = item.get("create_time", item.get("createTime", 0))

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

        # 保存到数据库（定时检查发现的新视频标记为 is_new=True）
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
            is_new=True,
        )
        new_count += 1
        logger.info(f"发现新视频: {aweme_id} - {item.get('desc', '')[:30]}")

    # 更新UP主视频数
    if new_count > 0:
        author = crud.get_author_by_id(db, author_id)
        if author:
            crud.update_author(db, author, video_count=author.video_count + new_count)
        logger.success(f"UP主 {sec_user_id} 新增 {new_count} 个视频")


def start_scheduler(interval_minutes: int = 30):
    """启动定时调度器"""
    scheduler.add_job(
        check_new_videos,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id="check_new_videos",
        name="检查新视频",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(f"定时任务已启动，每 {interval_minutes} 分钟检查一次新视频")


def stop_scheduler():
    """停止调度器"""
    scheduler.shutdown()
    logger.info("定时任务已停止")
