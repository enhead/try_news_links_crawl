from dataclasses import dataclass

from v1.DDD.domain.http_news_links_crawl.model.entity.layer_node_result_entity import CrawlNodeResultEntity


@dataclass
class CrawlResultEntity:
    """
    爬取结果实体

    封装 Layer 执行结果
    """

    layer_result: CrawlNodeResultEntity