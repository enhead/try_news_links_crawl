from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from v1.DDD.domain.http_news_links_crawl.model.aggregate.news_link_batch_aggregate import NewsLinkBatchAggregate
    from v1.DDD.domain.http_news_links_crawl.model.entity.news_source_metadata import NewsSourceMetadata


# ---------------------------------------------------------------------------
# 出参数据类
# ---------------------------------------------------------------------------

@dataclass
class BatchSaveResult:
    """
    批量写入的结果，供调用方记录日志和统计。
    saved_count / skipped_urls 无法从入参推算，因此需要返回。
    """

    saved_count: int                                        # 实际写入成功的条数
    skipped_urls: list[str] = field(default_factory=list)  # 因 uq_url 冲突跳过的 URL


# ---------------------------------------------------------------------------
# 仓储接口
# ---------------------------------------------------------------------------

class INewsCrawlRepository(ABC):
    """
    新闻爬虫系统的仓储接口。

    职责边界：
        1. 新闻源元数据查询（news_source 表）
           - get_source_by_resource_id  — 根据 resource_id 查询单个新闻源
           - get_all_active_sources     — 获取所有可调度的新闻源（status=0）
           - get_all_sources            — 获取所有新闻源

        2. 新闻链接的去重和保存（news_link 表）
           - check_exists_batch — CrawlNode 用来过滤出新链接
           - save_batch         — Service 层用来把新链接持久化

    DDD 分层说明：
        此接口定义在 domain 层，不 import 任何 ORM 或数据库驱动。
        具体实现（SQLAlchemy / aiomysql 等）放在 infrastructure 层。
    """

    # ------------------------------------------------------------------
    # 新闻源元数据查询
    # ------------------------------------------------------------------

    @abstractmethod
    async def get_source_by_resource_id(self, resource_id: str) -> "NewsSourceMetadata | None":
        """
        根据 resource_id 查询新闻源元数据。

        Args:
            resource_id: 新闻源唯一标识

        Returns:
            NewsSourceMetadata 对象，如果不存在则返回 None
        """
        ...

    # 下面两个现在不急
    @abstractmethod
    async def get_all_active_sources(self) -> list["NewsSourceMetadata"]:
        """
        获取所有可调度的新闻源（status=0）。

        Returns:
            NewsSourceMetadata 列表
        """
        ...

    @abstractmethod
    async def get_all_sources(self) -> list["NewsSourceMetadata"]:
        """
        获取所有新闻源（不过滤状态）。

        Returns:
            NewsSourceMetadata 列表
        """
        ...

    # ------------------------------------------------------------------
    # 新闻链接去重和保存
    # ------------------------------------------------------------------

    @abstractmethod
    async def check_exists_batch(
        self,
        aggregate: "NewsLinkBatchAggregate",
    ) -> "NewsLinkBatchAggregate":
        """
        返回聚合对象中不在 news_link 表里的链接（即新链接）

        实现层约束：
            必须用 WHERE url IN (...) 单次查询完成，禁止逐条查询。

        Args:
            aggregate: 包含待检查链接的聚合对象

        Returns:
            包含不在 DB 里的链接的新聚合对象
        """
        ...


    # TODO 待完善：批量保存操作我先简单实现了
    @abstractmethod
    async def save_batch(
        self,
        aggregate: "NewsLinkBatchAggregate",
    ) -> BatchSaveResult:
        """
        批量写入新链接到 news_link 表

        实现层约束：
            必须使用 INSERT IGNORE 或 ON DUPLICATE KEY 保证幂等性，
            同一 URL 重复写入不报错，不产生重复行。

        Args:
            aggregate: 包含新闻源配置和待保存链接的聚合对象

        Returns:
            BatchSaveResult，含实际写入条数与跳过的重复 URL
        """
        ...