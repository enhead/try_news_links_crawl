from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from v1.DDD.domain.http_news_links_crawl.model.entity.crawl_node_result_entity import DiscoveredNewsLinkUrl


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
        discovered: list[DiscoveredNewsLinkUrl],
    ) -> list[DiscoveredNewsLinkUrl]:
        """
        返回 discovered 中不在 news_link 表里的部分（即新链接）。

        入参传完整对象而非 list[str] 的原因：
            实现层需要返回 DiscoveredNewsLinkUrl 对象（含 crawl_params），
            直接传完整对象，实现层提取 url 做 IN 查询后，
            missing 只需从入参过滤即可，无需重新关联。

        实现层约束：
            必须用 WHERE url IN (...) 单次查询完成，禁止逐条查询。

        Args:
            discovered: 本页解析出的全部链接对象，可为空列表。

        Returns:
            discovered 中不在 DB 里的链接列表，可直接赋给 CrawlNodeResultEntity.urls_new。
        """
        ...

    @abstractmethod
    async def save_batch(
        self,
        source_id: str,
        links: list[DiscoveredNewsLinkUrl],
    ) -> BatchSaveResult:
        """
        批量写入新链接到 news_link 表。

        入参 links 即 CrawlNodeResultEntity.urls_new，调用方无需任何转换。
        source_id 单独传入，因为 DiscoveredNewsLinkUrl 只描述"发现了什么"，
        不持有归属信息（归属来自 SourceConfig）。

        实现层约束：
            必须使用 INSERT IGNORE 或 ON DUPLICATE KEY 保证幂等性，
            同一 URL 重复写入不报错，不产生重复行。

        Args:
            source_id: 新闻源标识，对应 news_source.source_id。
            links:     待写入的链接列表，通常直接传 CrawlNodeResultEntity.urls_new。

        Returns:
            BatchSaveResult，含实际写入条数与跳过的重复 URL。
        """
        ...