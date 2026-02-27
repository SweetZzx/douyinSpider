# -*- encoding: utf-8 -*-
"""
数据库连接配置
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from backend.config import settings

# MySQL连接配置（从settings读取）
DATABASE_URL = settings.database_url

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库（创建表）"""
    from backend.db.models import Author, Video, AuthorGroup
    Base.metadata.create_all(bind=engine)
