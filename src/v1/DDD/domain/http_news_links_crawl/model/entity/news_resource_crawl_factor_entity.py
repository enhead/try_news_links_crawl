"""新闻源爬取因子实体"""

from dataclasses import dataclass

from v1.DDD.domain.http_news_links_crawl.model.entity.crawl_context import CrawlContext


@dataclass
class NewsResourceCrawlFactorEntity:
    """
    新闻源爬取因子实体

    封装单次爬取所需的完整参数
    """
    context: CrawlContext
