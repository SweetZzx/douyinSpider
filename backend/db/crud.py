# -*- encoding: utf-8 -*-
"""
数据库CRUD操作
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from backend.db.models import Author, Video, AuthorGroup


# ==================== 分组操作 ====================

def get_all_groups(db: Session) -> List[AuthorGroup]:
    """获取所有分组"""
    return db.query(AuthorGroup).order_by(AuthorGroup.sort_order).all()


def get_group_by_id(db: Session, group_id: int) -> Optional[AuthorGroup]:
    """根据ID获取分组"""
    return db.query(AuthorGroup).filter(AuthorGroup.id == group_id).first()


def create_group(db: Session, name: str, sort_order: int = 0) -> AuthorGroup:
    """创建分组"""
    group = AuthorGroup(name=name, sort_order=sort_order)
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


def update_group(db: Session, group: AuthorGroup, **kwargs) -> AuthorGroup:
    """更新分组"""
    for key, value in kwargs.items():
        if hasattr(group, key):
            setattr(group, key, value)
    db.commit()
    db.refresh(group)
    return group


def delete_group(db: Session, group_id: int) -> bool:
    """删除分组（分组内的UP主会变为未分组）"""
    group = db.query(AuthorGroup).filter(AuthorGroup.id == group_id).first()
    if group:
        # 将分组内的UP主设置为未分组
        db.query(Author).filter(Author.group_id == group_id).update({"group_id": None})
        db.delete(group)
        db.commit()
        return True
    return False


def move_author_to_group(db: Session, author_id: int, group_id: Optional[int]) -> bool:
    """移动UP主到分组"""
    author = db.query(Author).filter(Author.id == author_id).first()
    if author:
        author.group_id = group_id
        db.commit()
        return True
    return False


# ==================== UP主操作 ====================

def get_author_by_sec_id(db: Session, sec_user_id: str) -> Optional[Author]:
    """根据sec_user_id获取UP主"""
    return db.query(Author).filter(Author.sec_user_id == sec_user_id).first()


def get_author_by_id(db: Session, author_id: int) -> Optional[Author]:
    """根据ID获取UP主"""
    return db.query(Author).filter(Author.id == author_id).first()


def get_all_authors(db: Session) -> List[Author]:
    """获取所有UP主"""
    return db.query(Author).order_by(Author.created_at.desc()).all()


def create_author(db: Session, sec_user_id: str, nickname: str = "",
                  avatar: str = "", signature: str = "") -> Author:
    """创建UP主"""
    author = Author(
        sec_user_id=sec_user_id,
        nickname=nickname,
        avatar=avatar,
        signature=signature,
    )
    db.add(author)
    db.commit()
    db.refresh(author)
    return author


def update_author(db: Session, author: Author, **kwargs) -> Author:
    """更新UP主信息"""
    for key, value in kwargs.items():
        if hasattr(author, key):
            setattr(author, key, value)
    author.updated_at = datetime.now()
    db.commit()
    db.refresh(author)
    return author


def delete_author(db: Session, author_id: int) -> bool:
    """删除UP主（同时删除其所有视频）"""
    author = db.query(Author).filter(Author.id == author_id).first()
    if author:
        db.delete(author)
        db.commit()
        return True
    return False


# ==================== 视频操作 ====================

def get_video_by_aweme_id(db: Session, aweme_id: str) -> Optional[Video]:
    """根据aweme_id获取视频"""
    return db.query(Video).filter(Video.aweme_id == aweme_id).first()


def get_videos_by_author(db: Session, author_id: int) -> List[Video]:
    """获取UP主的所有视频"""
    return db.query(Video).filter(Video.author_id == author_id)\
        .order_by(Video.create_time.desc()).all()


def get_videos_by_group(db: Session, group_id: int, limit: int = 100, offset: int = 0) -> List[Video]:
    """获取分组内所有UP主的视频（group_id=0表示未分组）"""
    from backend.db.models import Author
    # group_id=0 表示未分组
    if group_id == 0:
        author_ids = [a.id for a in db.query(Author).filter(Author.group_id == None).all()]
    else:
        author_ids = [a.id for a in db.query(Author).filter(Author.group_id == group_id).all()]
    if not author_ids:
        return []
    return db.query(Video).filter(Video.author_id.in_(author_ids))\
        .order_by(Video.create_time.desc()).offset(offset).limit(limit).all()


def count_videos_by_group(db: Session, group_id: int) -> int:
    """统计分组内视频数量（group_id=0表示未分组）"""
    from backend.db.models import Author
    # group_id=0 表示未分组
    if group_id == 0:
        author_ids = [a.id for a in db.query(Author).filter(Author.group_id == None).all()]
    else:
        author_ids = [a.id for a in db.query(Author).filter(Author.group_id == group_id).all()]
    if not author_ids:
        return 0
    return db.query(Video).filter(Video.author_id.in_(author_ids)).count()


def get_new_videos(db: Session) -> List[Video]:
    """获取所有新视频（用于提醒）"""
    return db.query(Video).filter(Video.is_new == True)\
        .order_by(Video.create_time.desc()).all()


def get_all_videos(db: Session, limit: int = 100, offset: int = 0) -> List[Video]:
    """获取所有视频（分页）"""
    return db.query(Video).order_by(Video.create_time.desc())\
        .offset(offset).limit(limit).all()


def count_videos(db: Session) -> int:
    """统计视频总数"""
    return db.query(Video).count()


def count_new_videos(db: Session) -> int:
    """统计新视频数量"""
    return db.query(Video).filter(Video.is_new == True).count()


def create_video(db: Session, author_id: int, aweme_id: str, **kwargs) -> Video:
    """创建视频"""
    video = Video(
        author_id=author_id,
        aweme_id=aweme_id,
        **kwargs
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    return video


def upsert_video(db: Session, author_id: int, aweme_id: str, **kwargs) -> Video:
    """创建或更新视频（如果已存在则更新）"""
    video = get_video_by_aweme_id(db, aweme_id)
    if video:
        # 更新已有视频
        for key, value in kwargs.items():
            if hasattr(video, key):
                setattr(video, key, value)
        db.commit()
        db.refresh(video)
        return video
    else:
        # 创建新视频
        return create_video(db, author_id, aweme_id, **kwargs)


def mark_video_as_read(db: Session, video_id: int) -> bool:
    """标记视频为已读"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if video:
        video.is_new = False
        db.commit()
        return True
    return False


def mark_all_videos_as_read(db: Session) -> int:
    """标记所有视频为已读"""
    count = db.query(Video).filter(Video.is_new == True).update({"is_new": False})
    db.commit()
    return count


def clear_new_videos_for_author(db: Session, author_id: int) -> int:
    """清除指定UP主的新视频标记"""
    count = db.query(Video).filter(
        Video.author_id == author_id,
        Video.is_new == True
    ).update({"is_new": False})
    db.commit()
    return count
