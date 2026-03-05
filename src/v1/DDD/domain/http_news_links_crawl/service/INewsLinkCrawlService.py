from abc import ABC, abstractmethod

from v1.DDD.domain.http_news_links_crawl.model.entity.CrawlResultEntity import CrawlResultEntity


# 单个新闻源的新闻链接爬虫

class INewsLinkCrawlService(ABC):
    """
    单源爬虫入口
    """

    @abstractmethod
    def incrementalCrawl(self) -> CrawlResultEntity:
        """
        增量爬取入口
        TODO 参数返回类型都没有写
        :return:
        """
