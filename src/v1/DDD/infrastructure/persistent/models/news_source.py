"""NewsSource ORM 模型"""

from sqlalchemy import Index, String
from sqlalchemy.dialects.mysql import TINYINT, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class NewsSourceModel(Base, TimestampMixin):
    """新闻源表 ORM 模型"""

    __tablename__ = "news_source"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    resource_id: Mapped[str] = mapped_column(VARCHAR(255), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    domain: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    url: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False)
    language: Mapped[str] = mapped_column(VARCHAR(20), nullable=False)
    status: Mapped[int] = mapped_column(TINYINT, nullable=False, default=0)

    __table_args__ = (
        Index("idx_domain", "domain"),
        Index("idx_status", "status"),
        Index("idx_country", "country"),
    )
