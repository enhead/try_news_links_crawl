"""新闻链接批量聚合根"""

from dataclasses import dataclass

from v1.DDD.domain.http_news_links_crawl.model.entity.layer_node_result_entity import DiscoveredNewsLinkUrl
from v1.DDD.domain.http_news_links_crawl.service.config.news_resource.abstract_news_source_config import (
    AbstractNewsSourceConfig,
)


@dataclass
class NewsLinkBatchAggregate:
    """
    批量新闻链接聚合根

    封装一次爬取的完整上下文：
    - source_config: 提供新闻源元数据和 category 提取能力
    - links: 待保存的链接列表

    用于 Repository 的 save_batch 和 check_exists_batch 接口
    """

    source_config: AbstractNewsSourceConfig
    links: list[DiscoveredNewsLinkUrl]
