"""NewsSourceHealthCheck ORM 模型"""

from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, Text
from sqlalchemy.dialects.mysql import VARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class NewsSourceHealthCheckModel(Base):
    """新闻源健康检查记录表 ORM 模型"""

    __tablename__ = "news_source_health_check"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    resource_id: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)

    # 检查结果
    check_status: Mapped[str] = mapped_column(VARCHAR(20), nullable=False)
    links_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    http_status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 时间
    checked_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (
        Index("idx_resource_id", "resource_id"),
        Index("idx_check_status", "check_status"),
        Index("idx_checked_at", "checked_at"),
    )
