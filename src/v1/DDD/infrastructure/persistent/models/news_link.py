"""NewsLink ORM 模型"""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import JSON, Date, DateTime, Index, String, Text
from sqlalchemy.dialects.mysql import MEDIUMTEXT, TINYINT, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class NewsLinkModel(Base, TimestampMixin):
    """新闻链接表 ORM 模型"""

    __tablename__ = "news_link"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 新闻源关联（冗余字段）
    resource_id: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    country: Mapped[str] = mapped_column(VARCHAR(20), nullable=False)
    name: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    domain: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    language: Mapped[str] = mapped_column(VARCHAR(20), nullable=False)

    # 链接信息
    url: Mapped[str] = mapped_column(VARCHAR(255), nullable=False, unique=True)
    crawl_params: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    category: Mapped[str] = mapped_column(VARCHAR(100), nullable=False)

    # 流水线状态
    is_parse: Mapped[int] = mapped_column(TINYINT, nullable=False, default=0)
    is_translated: Mapped[int] = mapped_column(TINYINT, nullable=False, default=0)
    success: Mapped[int] = mapped_column(TINYINT, nullable=False, default=0)

    __table_args__ = (
        Index("idx_resource_id", "resource_id"),
        Index("idx_is_parse", "is_parse"),
        Index("idx_success", "success"),
        Index("idx_country", "country"),
        Index("idx_domain", "domain"),
    )
