from abc import ABC, abstractmethod

from v1.DDD.domain.http_news_links_crawl.model.entity.crawl_result_entity import CrawlResultEntity
from v1.DDD.domain.http_news_links_crawl.model.entity.news_resource_crawl_factor_entity import NewsResourceCrawlFactorEntity


class INewsLinkCrawlService(ABC):
    """
    单源新闻链接爬取领域服务接口

    职责：
    - 构建初始 LayerFactorEntity
    - 执行 Layer 树的爬取流程
    - 返回爬取结果

    不负责：
    - 构建 Layer 树（由调用者完成）
    - 保存结果（由 Node 层或调用者处理）
    """

    @abstractmethod
    async def execute_crawl(
        self,
        crawl_factor: NewsResourceCrawlFactorEntity
    ) -> CrawlResultEntity:
        """
        执行爬取

        Args:
            crawl_factor: 新闻源爬取因子（封装 root_layer 和 context）

        Returns:
            CrawlResultEntity: 爬取结果（内部封装 CrawlNodeResultEntity）
        """
