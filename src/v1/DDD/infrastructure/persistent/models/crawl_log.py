"""CrawlLog ORM 模型"""

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, Index, Integer, String
from sqlalchemy.dialects.mysql import VARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class CrawlLogModel(Base):
    """爬虫执行日志表 ORM 模型"""

    __tablename__ = "crawl_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 新闻源关联
    resource_id: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)

    # 爬取结果汇总
    crawl_status: Mapped[str] = mapped_column(VARCHAR(20), nullable=False)
    total_categories: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success_categories: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_categories: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_links_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_links_new: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # 详细信息（JSON格式）
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # 时间
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    finished_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)

    # 创建时间（不继承 TimestampMixin，因为不需要 updated_at）
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default="CURRENT_TIMESTAMP",
    )

    __table_args__ = (
        Index("idx_resource_id", "resource_id"),
        Index("idx_crawl_status", "crawl_status"),
        Index("idx_started_at", "started_at"),
    )
