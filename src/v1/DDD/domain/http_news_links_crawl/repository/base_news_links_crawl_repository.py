from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from v1.DDD.domain.http_news_links_crawl.model.aggregate.news_link_batch_aggregate import NewsLinkBatchAggregate


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

class INewsLinksCrawlRepository(ABC):
    """
    新闻链接爬虫的仓储接口。

    职责边界：
        只操作 news_link 表，只服务链接爬虫阶段的两个操作：
            1. check_exists_batch — CrawlNode 用来过滤出新链接
            2. save_batch         — Service 层用来把新链接持久化

    DDD 分层说明：
        此接口定义在 domain 层，不 import 任何 ORM 或数据库驱动。
        具体实现（SQLAlchemy / aiomysql 等）放在 infrastructure 层。
    """

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