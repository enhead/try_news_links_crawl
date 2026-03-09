"""新闻链接批量聚合根"""

from dataclasses import dataclass

from v1.DDD.domain.http_news_links_crawl.model.entity.layer_node_result_entity import DiscoveredNewsLinkUrl
from v1.DDD.domain.http_news_links_crawl.model.entity.news_source_metadata import NewsSourceMetadata


@dataclass
class NewsLinkBatchAggregate:
    """
    批量新闻链接聚合根

    封装一次爬取的完整数据：
    - metadata: 新闻源元数据（用于保存到数据库）
    - links: 待保存的链接列表（已包含 category）

    用于 Repository 的 save_batch 和 check_exists_batch 接口
    """

    metadata: NewsSourceMetadata
    links: list[DiscoveredNewsLinkUrl]
