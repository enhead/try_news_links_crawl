"""单源新闻链接爬取领域服务实现"""

import logging

from v1.DDD.domain.http_news_links_crawl.model.entity.crawl_result_entity import CrawlResultEntity
from v1.DDD.domain.http_news_links_crawl.model.entity.layer_factor_entity import LayerFactorEntity
from v1.DDD.domain.http_news_links_crawl.model.entity.news_resource_crawl_factor_entity import NewsResourceCrawlFactorEntity
from v1.DDD.domain.http_news_links_crawl.service.single_news_link_crawl.base_news_link_crawl_service import INewsLinkCrawlService
from v1.DDD.domain.http_news_links_crawl.service.single_news_link_crawl.crawl_layer.factory.layer_factory import CrawlLayerFactory

logger = logging.getLogger(__name__)


class NewsLinkCrawlService(INewsLinkCrawlService):
    """
    单源新闻链接爬取领域服务实现

    职责：
    - 构建初始 LayerFactorEntity
    - 执行 Layer 树的爬取流程
    - 返回爬取结果
    """

    async def execute_crawl(
        self,
        crawl_factor: NewsResourceCrawlFactorEntity
    ) -> CrawlResultEntity:
        """
        执行爬取

        Args:
            crawl_factor: 新闻源爬取因子

        Returns:
            CrawlResultEntity: 爬取结果
        """
        logger.info("开始执行爬取")

        source_config = crawl_factor.context.source_config
        # 构架layer的具体实现
        root_layer = CrawlLayerFactory.build(source_config.layer_schema)
        # 创建初始 Factor（空参数）
        initial_factor = LayerFactorEntity.create(crawl_factor.context)

        # 执行爬取
        layer_result = await root_layer.execute(initial_factor)

        logger.info(
            f"爬取完成: "
            f"发现链接={len(layer_result.urls_found)}, "
            f"新链接={len(layer_result.urls_new)}"
        )

        # 返回结果
        return CrawlResultEntity(layer_result=layer_result)
