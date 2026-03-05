# -*- encoding: utf-8 -*-
"""
数据库CRUD操作
"""

from typing import List, Optional
from datetime import datetime
from contextlib import contextmanager
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger

from backend.db.models import Author, Video, AuthorGroup, AudioExtraction, Transcript, SystemConfig, PromptTemplate


# ==================== 事务管理 ====================

@contextmanager
def transaction_scope(db: Session):
    """事务上下文管理器，确保事务正确提交或回滚

    Args:
        db: 数据库会话

    Yields:
        数据库会话

    Example:
        with transaction_scope(db) as session:
            # 执行数据库操作
            create_author(session, ...)
            create_video(session, ...)
            # 如果发生异常，自动回滚
    """
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"事务执行失败，已回滚: {e}")
        raise
    finally:
        # 注意：不在这里关闭session，因为session由外部管理
        pass


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
    try:
        with transaction_scope(db):
            group = db.query(AuthorGroup).filter(AuthorGroup.id == group_id).first()
            if not group:
                return False

            # 将分组内的UP主设置为未分组
            db.query(Author).filter(Author.group_id == group_id).update({"group_id": None})
            db.delete(group)

        return True
    except SQLAlchemyError as e:
        logger.error(f"删除分组失败: {e}")
        raise


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
    try:
        with transaction_scope(db):
            author = db.query(Author).filter(Author.id == author_id).first()
            if not author:
                return False

            # 先删除所有关联的视频（SQLAlchemy会自动处理级联）
            # 如果模型中配置了cascade="all, delete-orphan"，这里会自动删除
            db.delete(author)

        return True
    except SQLAlchemyError as e:
        logger.error(f"删除UP主失败: {e}")
        raise


# ==================== 视频操作 ====================

def get_video_by_aweme_id(db: Session, aweme_id: str) -> Optional[Video]:
    """根据aweme_id获取视频"""
    return db.query(Video).filter(Video.aweme_id == aweme_id).first()


def get_videos_by_author(db: Session, author_id: int) -> List[Video]:
    """获取UP主的所有视频"""
    return db.query(Video).options(joinedload(Video.author))\
        .filter(Video.author_id == author_id)\
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
    return db.query(Video).options(joinedload(Video.author))\
        .filter(Video.author_id.in_(author_ids))\
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
    return db.query(Video).options(joinedload(Video.author))\
        .filter(Video.is_new == True)\
        .order_by(Video.create_time.desc()).all()


def get_all_videos(db: Session, limit: int = 100, offset: int = 0) -> List[Video]:
    """获取所有视频（分页）"""
    return db.query(Video).options(joinedload(Video.author))\
        .order_by(Video.create_time.desc())\
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


def save_video_rewrite(db: Session, video_id: int, rewritten_text: str) -> bool:
    """保存视频的仿写文案"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if video:
        video.rewritten_text = rewritten_text
        video.rewritten_at = datetime.now()
        db.commit()
        return True
    return False


# ==================== 音频提取操作 ====================

def create_audio_extraction(
    db: Session,
    video_id: int,
    audio_path: str = "",
    file_size: int = 0,
    duration: float = 0.0,
    format: str = "mp3",
    status: str = "pending",
    error_message: str = ""
) -> AudioExtraction:
    """创建音频提取记录"""
    extraction = AudioExtraction(
        video_id=video_id,
        audio_path=audio_path,
        file_size=file_size,
        duration=duration,
        format=format,
        status=status,
        error_message=error_message
    )
    db.add(extraction)
    db.commit()
    db.refresh(extraction)
    return extraction


def update_audio_extraction(db: Session, extraction: AudioExtraction, **kwargs) -> AudioExtraction:
    """更新音频提取记录"""
    for key, value in kwargs.items():
        if hasattr(extraction, key):
            setattr(extraction, key, value)
    db.commit()
    db.refresh(extraction)
    return extraction


def get_audio_extraction_by_video(db: Session, video_id: int) -> Optional[AudioExtraction]:
    """根据视频ID获取音频提取记录"""
    return db.query(AudioExtraction).filter(AudioExtraction.video_id == video_id).first()


def get_all_audio_extractions(db: Session, limit: int = 100, offset: int = 0) -> List[AudioExtraction]:
    """获取所有音频提取记录"""
    return db.query(AudioExtraction).order_by(AudioExtraction.created_at.desc()).limit(limit).offset(offset).all()


def delete_audio_extraction(db: Session, extraction_id: int) -> bool:
    """删除音频提取记录"""
    extraction = db.query(AudioExtraction).filter(AudioExtraction.id == extraction_id).first()
    if extraction:
        db.delete(extraction)
        db.commit()
        return True
    return False


# ==================== 语音转写操作 ====================

def create_transcript(
    db: Session,
    video_id: int,
    text: str = "",
    segments: list = None,
    language: str = "zh",
    duration: float = 0.0,
    confidence: float = 0.0,
    status: str = "pending",
    error_message: str = ""
) -> Transcript:
    """创建语音转写记录"""
    transcript = Transcript(
        video_id=video_id,
        text=text,
        segments=segments,
        language=language,
        duration=duration,
        confidence=confidence,
        status=status,
        error_message=error_message
    )
    db.add(transcript)
    db.commit()
    db.refresh(transcript)
    return transcript


def update_transcript(db: Session, transcript: Transcript, **kwargs) -> Transcript:
    """更新语音转写记录"""
    for key, value in kwargs.items():
        if hasattr(transcript, key):
            setattr(transcript, key, value)
    db.commit()
    db.refresh(transcript)
    return transcript


def get_transcript_by_video(db: Session, video_id: int) -> Optional[Transcript]:
    """根据视频ID获取转写记录"""
    return db.query(Transcript).filter(Transcript.video_id == video_id).first()


def get_all_transcripts(db: Session, limit: int = 100, offset: int = 0) -> List[Transcript]:
    """获取所有转写记录"""
    return db.query(Transcript).order_by(Transcript.created_at.desc()).limit(limit).offset(offset).all()


def delete_transcript(db: Session, transcript_id: int) -> bool:
    """删除转写记录"""
    transcript = db.query(Transcript).filter(Transcript.id == transcript_id).first()
    if transcript:
        db.delete(transcript)
        db.commit()
        return True
    return False


# ==================== 系统配置操作 ====================

def get_system_config(db: Session, key: str) -> Optional[SystemConfig]:
    """获取系统配置"""
    return db.query(SystemConfig).filter(SystemConfig.key == key).first()


def upsert_system_config(
    db: Session,
    key: str,
    value: str,
    description: str = None,
    category: str = "general"
) -> SystemConfig:
    """创建或更新系统配置"""
    config = get_system_config(db, key)
    if config:
        config.value = value
        if description is not None:
            config.description = description
        db.commit()
        db.refresh(config)
    else:
        config = SystemConfig(
            key=key,
            value=value,
            description=description or f"{key} 配置",
            category=category
        )
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


def get_all_configs_by_category(db: Session, category: str) -> List[SystemConfig]:
    """获取指定分类的所有配置"""
    return db.query(SystemConfig).filter(SystemConfig.category == category).all()


def delete_system_config(db: Session, key: str) -> bool:
    """删除系统配置"""
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if config:
        db.delete(config)
        db.commit()
        return True
    return False


# ==================== 提示词模板操作 ====================

def get_all_prompt_templates(db: Session, category: str = None) -> List[PromptTemplate]:
    """获取所有启用的提示词模板

    Args:
        category: 可选，筛选指定分类的模板。为None时返回所有分类。
    """
    query = db.query(PromptTemplate).filter(PromptTemplate.is_active == True)
    if category:
        query = query.filter(PromptTemplate.category == category)
    return query.order_by(PromptTemplate.sort_order, PromptTemplate.created_at.desc()).all()


def get_prompt_template_by_id(db: Session, template_id: int) -> Optional[PromptTemplate]:
    """根据ID获取提示词模板"""
    return db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()


def get_default_prompt_template(db: Session, category: str = "rewrite") -> Optional[PromptTemplate]:
    """获取默认提示词模板"""
    return db.query(PromptTemplate)\
        .filter(PromptTemplate.category == category)\
        .filter(PromptTemplate.is_default == True)\
        .filter(PromptTemplate.is_active == True)\
        .first()


def create_prompt_template(
    db: Session,
    name: str,
    content: str,
    description: str = "",
    category: str = "rewrite",
    is_default: bool = False,
    sort_order: int = 0
) -> PromptTemplate:
    """创建提示词模板"""
    try:
        with transaction_scope(db):
            # 如果设置为默认模板，先取消其他默认模板
            if is_default:
                db.query(PromptTemplate)\
                    .filter(PromptTemplate.category == category)\
                    .filter(PromptTemplate.is_default == True)\
                    .update({"is_default": False})

            template = PromptTemplate(
                name=name,
                content=content,
                description=description,
                category=category,
                is_default=is_default,
                sort_order=sort_order
            )
            db.add(template)
            db.flush()  # 获取ID但不提交事务
            db.refresh(template)

        return template
    except SQLAlchemyError as e:
        logger.error(f"创建提示词模板失败: {e}")
        raise


def update_prompt_template(db: Session, template: PromptTemplate, **kwargs) -> PromptTemplate:
    """更新提示词模板"""
    # 保护默认模板：不允许修改默认模板的核心字段
    if template.is_default:
        # 默认模板只能修改 description 和 sort_order
        allowed_fields = {'description', 'sort_order'}
        for key in kwargs.keys():
            if key not in allowed_fields:
                raise ValueError(f"默认模板不能修改 {key} 字段，请复制后创建新模板")

    for key, value in kwargs.items():
        if hasattr(template, key):
            setattr(template, key, value)

    # 如果设置为默认模板，先取消其他默认模板
    if kwargs.get('is_default', False):
        db.query(PromptTemplate)\
            .filter(PromptTemplate.category == template.category)\
            .filter(PromptTemplate.id != template.id)\
            .filter(PromptTemplate.is_default == True)\
            .update({"is_default": False})

    db.commit()
    db.refresh(template)
    return template


def delete_prompt_template(db: Session, template_id: int) -> bool:
    """删除提示词模板（软删除）"""
    template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
    if not template:
        return False

    # 保护系统模板：不允许删除
    if template.is_system:
        raise ValueError("系统默认模板不能删除，请复制后创建新模板")

    template.is_active = False
    db.commit()
    return True


def copy_prompt_template(db: Session, template_id: int, new_name: str = None) -> PromptTemplate:
    """复制提示词模板"""
    original_template = get_prompt_template_by_id(db, template_id)
    if not original_template:
        raise ValueError("模板不存在")

    # 生成新名称
    name = new_name or f"{original_template.name} (副本)"

    # 检查名称是否已存在
    existing = db.query(PromptTemplate)\
        .filter(PromptTemplate.name == name)\
        .filter(PromptTemplate.is_active == True)\
        .first()

    if existing:
        # 如果名称存在，添加序号
        counter = 1
        while True:
            new_name_try = f"{name} ({counter})"
            existing = db.query(PromptTemplate)\
                .filter(PromptTemplate.name == new_name_try)\
                .filter(PromptTemplate.is_active == True)\
                .first()
            if not existing:
                name = new_name_try
                break
            counter += 1

    # 创建副本
    new_template = PromptTemplate(
        name=name,
        content=original_template.content,
        description=original_template.description,
        category=original_template.category,
        is_default=False,  # 副本不是默认模板
        sort_order=original_template.sort_order
    )
    db.add(new_template)
    db.commit()
    db.refresh(new_template)
    return new_template
