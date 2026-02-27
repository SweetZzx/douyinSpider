# -*- encoding: utf-8 -*-
"""
数据库模型定义
"""

from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from backend.db.database import Base


class AuthorGroup(Base):
    """UP主分组表"""
    __tablename__ = "author_groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment="分组名称")
    sort_order = Column(Integer, default=0, comment="排序顺序")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")

    # 关联UP主
    authors = relationship("Author", back_populates="group")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Author(Base):
    """UP主表"""
    __tablename__ = "up_authors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sec_user_id = Column(String(128), unique=True, nullable=False, index=True, comment="抖音用户ID")
    nickname = Column(String(100), default="", comment="昵称")
    avatar = Column(String(500), default="", comment="头像URL")
    signature = Column(String(500), default="", comment="签名")
    video_count = Column(Integer, default=0, comment="视频数量")
    latest_video_time = Column(BigInteger, default=0, comment="最新视频时间戳")
    group_id = Column(Integer, ForeignKey("author_groups.id"), nullable=True, index=True, comment="分组ID")
    created_at = Column(DateTime, default=datetime.now, comment="添加时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # 关联分组
    group = relationship("AuthorGroup", back_populates="authors")
    # 关联视频
    videos = relationship("Video", back_populates="author", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "sec_user_id": self.sec_user_id,
            "nickname": self.nickname,
            "avatar": self.avatar,
            "signature": self.signature,
            "video_count": self.video_count,
            "latest_video_time": self.latest_video_time,
            "group_id": self.group_id,
            "group_name": self.group.name if self.group else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Video(Base):
    """视频表"""
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    author_id = Column(Integer, ForeignKey("up_authors.id"), nullable=False, index=True, comment="UP主ID")
    aweme_id = Column(String(50), unique=True, nullable=False, index=True, comment="抖音视频ID")
    desc = Column(String(500), default="", comment="视频描述/标题")
    cover = Column(String(500), default="", comment="封面URL")
    video_url = Column(String(200), default="", comment="视频页面URL")
    download_url = Column(Text, default="", comment="下载地址")
    create_time = Column(BigInteger, default=0, comment="发布时间戳")
    duration = Column(Integer, default=0, comment="时长(毫秒)")
    digg_count = Column(Integer, default=0, comment="点赞数")
    comment_count = Column(Integer, default=0, comment="评论数")
    share_count = Column(Integer, default=0, comment="分享数")
    collect_count = Column(Integer, default=0, comment="收藏数")
    is_new = Column(Boolean, default=True, comment="是否新视频")
    created_at = Column(DateTime, default=datetime.now, comment="入库时间")

    # 关联UP主
    author = relationship("Author", back_populates="videos")

    def to_dict(self):
        return {
            "id": self.id,
            "author_id": self.author_id,
            "author_nickname": self.author.nickname if self.author else "",
            "aweme_id": self.aweme_id,
            "desc": self.desc,
            "cover": self.cover,
            "video_url": self.video_url or f"https://www.douyin.com/video/{self.aweme_id}",
            "download_url": self.download_url,
            "create_time": self.create_time,
            "duration": self.duration,
            "digg_count": self.digg_count,
            "comment_count": self.comment_count,
            "share_count": self.share_count,
            "collect_count": self.collect_count,
            "is_new": self.is_new,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
