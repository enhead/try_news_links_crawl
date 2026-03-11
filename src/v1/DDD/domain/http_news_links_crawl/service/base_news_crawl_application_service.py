"""
新闻爬取应用服务接口

职责：
- 编排运行新闻源爬取流程
- 组装 NewsResourceCrawlFactorEntity
- 调用领域服务 INewsLinkCrawlService
- 加载新闻源配置（调用 NewsSourceConfigRegistry）
"""

from abc import ABC, abstractmethod

from v1.DDD.domain.http_news_links_crawl.model.entity.crawl_result_entity import CrawlResultEntity


class INewsCrawlApplicationService(ABC):
    """新闻爬取应用服务接口"""

    @abstractmethod
    async def load_all_source_configs(
        self,
        module_paths: str | list[str] | None = None
    ) -> list[str]:
        """
        加载所有新闻源配置

        内部调用 NewsSourceConfigRegistry 的自动注册功能，
        扫描并注册指定模块中的所有配置类

        Args:
            module_paths: 要导入的模块路径，支持：
                - None: 从配置中读取（.env 的 NEWS_SOURCE_MODULES）
                - str: 单个模块路径
                - list[str]: 多个模块路径数组

        Returns:
            list[str]: 成功注册的 resource_id 列表
        """

    @abstractmethod
    async def crawl_single_source(
        self,
        resource_id: str
    ) -> CrawlResultEntity:
        """
        运行单个新闻源爬取

        流程：
        1. 从 NewsSourceConfigRegistry 获取配置实例
        2. 组装 NewsResourceCrawlFactorEntity（包含 context）
        3. 调用 INewsLinkCrawlService.execute_crawl()

        Args:
            resource_id: 新闻源 ID（如 "sg_straits_times"）

        Returns:
            CrawlResultEntity: 爬取结果
        """

    @abstractmethod
    async def crawl_multiple_sources(
        self,
        resource_ids: list[str]
    ) -> list[CrawlResultEntity]:
        """
        运行多个新闻源爬取（顺序执行）

        对每个 resource_id 调用 crawl_single_source()

        Args:
            resource_ids: 新闻源 ID 数组

        Returns:
            list[CrawlResultEntity]: 每个源的爬取结果
        """
