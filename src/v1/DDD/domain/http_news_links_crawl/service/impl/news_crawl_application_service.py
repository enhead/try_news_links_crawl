"""
新闻爬取应用服务实现

职责：
- 编排运行新闻源爬取流程
- 组装 NewsResourceCrawlFactorEntity
- 调用领域服务 INewsLinkCrawlService
- 加载新闻源配置（调用 NewsSourceConfigRegistry）
"""

import logging

from v1.DDD.app.src.main.config.app_config import NewsSourceConfig
from v1.DDD.domain.http_news_links_crawl.model.entity.crawl_context import CrawlContext
from v1.DDD.domain.http_news_links_crawl.model.entity.crawl_result_entity import CrawlResultEntity
from v1.DDD.domain.http_news_links_crawl.model.entity.news_resource_crawl_factor_entity import NewsResourceCrawlFactorEntity
from v1.DDD.domain.http_news_links_crawl.repository.base_news_links_crawl_repository import INewsCrawlRepository
from v1.DDD.domain.http_news_links_crawl.service.base_news_crawl_application_service import INewsCrawlApplicationService
from v1.DDD.domain.http_news_links_crawl.service.config.news_resource.registry.news_source_config_registry import NewsSourceConfigRegistry
from v1.DDD.domain.http_news_links_crawl.service.single_news_link_crawl.base_news_link_crawl_service import INewsLinkCrawlService
from v1.DDD.infrastructure.http.httpx_adapter import HttpAdapter

logger = logging.getLogger(__name__)


class NewsCrawlApplicationService(INewsCrawlApplicationService):
    """新闻爬取应用服务实现"""

    def __init__(
        self,
        repository: INewsCrawlRepository,
        http_adapter: HttpAdapter,
        crawl_service: INewsLinkCrawlService,
        news_source_config: NewsSourceConfig
    ):
        """
        初始化应用服务

        Args:
            repository: 新闻爬取仓储
            http_adapter: HTTP 适配器
            crawl_service: 领域服务
            news_source_config: 新闻源配置
        """
        self._repository = repository
        self._http_adapter = http_adapter
        self._crawl_service = crawl_service
        self._news_source_config = news_source_config

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
        # 如果不传参数，从配置中读取
        if module_paths is None:
            module_paths = self._news_source_config.module_paths
            logger.info(f"从配置中读取模块路径: {module_paths}")

        logger.info("开始加载新闻源配置")

        try:
            registered_ids = NewsSourceConfigRegistry.auto_register_from_module(
                module_paths=module_paths
            )
            logger.info(f"成功加载 {len(registered_ids)} 个新闻源配置: {registered_ids}")
            return registered_ids
        except ImportError as e:
            logger.error(f"加载新闻源配置失败: {e}")
            raise

    async def crawl_single_source(
        self,
        resource_id: str
    ) -> CrawlResultEntity:
        """
        运行单个新闻源爬取

        流程：
        1. 从 NewsSourceConfigRegistry 获取配置实例
        2. 创建数据库会话（管理事务边界）
        3. 组装 NewsResourceCrawlFactorEntity（包含 context 和 session）
        4. 调用 INewsLinkCrawlService.execute_crawl()
        5. 提交事务（成功）或回滚（失败）

        Args:
            resource_id: 新闻源 ID（如 "sg_straits_times"）

        Returns:
            CrawlResultEntity: 爬取结果

        Raises:
            KeyError: resource_id 未注册
            ValueError: 数据库中未找到对应新闻源
            Exception: 爬取过程中的其他异常
        """
        logger.info(f"开始爬取新闻源: {resource_id}")

        try:
            # 1. 从 Registry 获取配置（单例）
            source_config = await NewsSourceConfigRegistry.create_config(
                resource_id,
                self._repository
            )

            # 2. 🎯 创建 session，管理整个爬取流程的事务边界
            async with self._repository.session_factory() as session:
                logger.debug(f"开始数据库事务: {resource_id}")

                # 记录开始时间
                from datetime import datetime
                started_at = datetime.now()

                try:
                    # 3. 组装 CrawlContext（传入 session）
                    context = CrawlContext(
                        source_config=source_config,
                        http_adapter=self._http_adapter,
                        news_crawl_repository=self._repository,
                        session=session  # 🎯 传入 session
                    )

                    # 4. 组装 NewsResourceCrawlFactorEntity
                    crawl_factor = NewsResourceCrawlFactorEntity(context=context)

                    # 5. 调用领域服务
                    result = await self._crawl_service.execute_crawl(crawl_factor)

                    # 记录结束时间
                    finished_at = datetime.now()

                    # 6. 🎯 保存爬取日志（在同一事务中）
                    log_id = await self._repository.save_crawl_log(
                        session=session,
                        resource_id=resource_id,
                        result=result.layer_result,  # 传入顶层结果
                        started_at=started_at,
                        finished_at=finished_at
                    )
                    logger.info(f"爬取日志已保存: {resource_id}, log_id={log_id}")

                    # 7. 🎯 提交事务（包含链接保存 + 日志保存）
                    logger.info(
                        f"提交事务: {resource_id}, "
                        f"发现链接={len(result.layer_result.urls_found)}, "
                        f"新链接={len(result.layer_result.urls_new)}"
                    )
                    await session.commit()                  # TODO：事务提交在这里，注意了
                    logger.info(f"事务提交成功: {resource_id}")

                    logger.info(
                        f"爬取完成: {resource_id}, "
                        f"发现链接={len(result.layer_result.urls_found)}, "
                        f"新链接={len(result.layer_result.urls_new)}"
                    )

                    return result

                except Exception as e:
                    # 🎯 异常时回滚事务
                    await session.rollback()
                    logger.error(
                        f"爬取失败，事务已回滚: {resource_id}, "
                        f"错误类型={type(e).__name__}, 详情={e}"
                    )
                    raise

        except KeyError as e:
            logger.error(f"新闻源未注册: {resource_id}, 错误={e}")
            # TODO: 集成健康检查机制 - 记录未注册的源
            raise
        except ValueError as e:
            logger.error(f"数据库中未找到新闻源: {resource_id}, 错误={e}")
            # TODO: 集成健康检查机制 - 记录数据库不一致问题
            raise
        except Exception as e:
            logger.error(f"爬取失败: {resource_id}, 错误类型={type(e).__name__}, 详情={e}")
            # TODO: 集成健康检查机制 - 记录爬取失败，判断是否需要标记为异常
            # TODO: 完善错误处理 - 区分网络异常、解析异常、数据库异常等
            raise

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
        logger.info(f"开始批量爬取 {len(resource_ids)} 个新闻源")

        results = []
        success_count = 0
        failed_count = 0

        for resource_id in resource_ids:
            try:
                result = await self.crawl_single_source(resource_id)
                results.append(result)
                success_count += 1
            except Exception as e:
                logger.warning(
                    f"跳过失败的新闻源: {resource_id}, "
                    f"错误类型={type(e).__name__}, "
                    f"详情={e}"
                )
                failed_count += 1
                # TODO: 完善错误处理 - 提供更详细的失败信息（是否需要返回失败列表？）
                # 继续处理其他源，不中断

        logger.info(
            f"批量爬取完成: 成功={success_count}, 失败={failed_count}, "
            f"总计={len(resource_ids)}"
        )

        return results
