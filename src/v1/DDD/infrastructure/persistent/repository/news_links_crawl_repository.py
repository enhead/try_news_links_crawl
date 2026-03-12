from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from v1.DDD.domain.http_news_links_crawl.model.aggregate.news_link_batch_aggregate import NewsLinkBatchAggregate
from v1.DDD.domain.http_news_links_crawl.model.entity.layer_node_result_entity import CrawlNodeResultEntity
from v1.DDD.domain.http_news_links_crawl.model.entity.news_source_metadata import NewsSourceMetadata
from v1.DDD.domain.http_news_links_crawl.repository.base_news_links_crawl_repository import (
    INewsCrawlRepository,
    BatchSaveResult,
)
from v1.DDD.infrastructure.persistent.dao import CrawlLogDAO, NewsLinkDAO, NewsSourceDAO
from v1.DDD.infrastructure.persistent.models.mapper import (
    CrawlLogMapper,
    NewsLinkMapper,
    NewsSourceMapper,
)


class NewsLinksCrawlRepository(INewsCrawlRepository):
    """
    新闻链接爬虫仓储实现（无状态设计）

    ## 架构设计（方案A：Application Service 管理事务）

    ### 职责边界
    1. **仓储职责**：
       - 封装数据访问逻辑（通过 DAO）
       - 领域模型与数据模型的映射（通过 Mapper）
       - 不负责事务管理（session 由外部传入）

    2. **事务管理责任**：
       - ❌ 仓储层不创建 session，不调用 commit/rollback
       - ✅ Application Service 层统一管理事务边界

    ### 实现细节
    - 持有 `session_factory`（仅用于只读操作）
    - 持有 DAO 实例（DAO 无状态，可复用）
    - 写操作方法接受 `session` 参数（由调用方管理事务）
    - 只读操作方法自己创建临时 session（用完即关）

    ### 企业级最佳实践
    遵循 Spring `@Transactional` 和 DDD Unit of Work 模式：
    ```python
    # Application Service 层代码示例
    async with repository.session_factory() as session:
        try:
            # 业务逻辑（可能调用多个仓储方法）
            await repository.save_batch(session, aggregate)
            await repository.save_crawl_log(session, ...)
            # 统一提交事务
            await session.commit()
        except Exception:
            # 统一回滚
            await session.rollback()
            raise
    ```
    """

    def __init__(self, session_factory):
        """
        初始化仓储

        Args:
            session_factory: 会话工厂（用于只读操作）
        """
        self._session_factory = session_factory

        # 创建 DAO 实例（DAO 无状态，可以复用）
        self._news_link_dao = NewsLinkDAO()
        self._news_source_dao = NewsSourceDAO()
        self._crawl_log_dao = CrawlLogDAO()

    @property
    def session_factory(self):
        """
        暴露 session_factory 给 Application Service 层

        用途：
            Application Service 使用此工厂创建 session，管理事务边界。

        使用场景：
            ```python
            # Application Service 层
            async with self._repository.session_factory() as session:
                try:
                    # 创建 CrawlContext（传入 session）
                    context = CrawlContext(..., session=session)
                    # 执行业务逻辑
                    result = await self._crawl_service.execute_crawl(factor)
                    # 提交事务
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise
            ```

        架构说明：
            - 仓储层只读操作会自己创建临时 session
            - 写操作需要外部传入 session（由 Application Service 管理）
        """
        return self._session_factory

    # ------------------------------------------------------------------
    # 新闻源元数据查询
    # ------------------------------------------------------------------

    async def get_source_by_resource_id(self, resource_id: str) -> NewsSourceMetadata | None:
        """根据 resource_id 查询新闻源元数据"""
        async with self._session_factory() as session:
            model = await self._news_source_dao.find_by_resource_id(session, resource_id)
            if model is None:
                return None
            return NewsSourceMapper.to_entity(model)

    async def get_all_active_sources(self) -> list[NewsSourceMetadata]:
        """获取所有可调度的新闻源（status=0）"""
        async with self._session_factory() as session:
            models = await self._news_source_dao.find_all_by_status(session, status=0)
            return NewsSourceMapper.to_entity_list(models)

    async def get_all_sources(self) -> list[NewsSourceMetadata]:
        """获取所有新闻源（不过滤状态）"""
        async with self._session_factory() as session:
            models = await self._news_source_dao.find_all(session)
            return NewsSourceMapper.to_entity_list(models)

    # ------------------------------------------------------------------
    # 新闻链接去重和保存
    # ------------------------------------------------------------------

    async def check_exists_batch(
        self, aggregate: NewsLinkBatchAggregate
    ) -> NewsLinkBatchAggregate:
        """批量检查链接是否存在，返回包含新链接的聚合对象"""
        if not aggregate.links:
            return aggregate

        async with self._session_factory() as session:
            urls = [link.url for link in aggregate.links]
            existing_urls = await self._news_link_dao.check_urls_exist(session, urls)
            new_links = [link for link in aggregate.links if link.url not in existing_urls]

            return NewsLinkBatchAggregate(
                metadata=aggregate.metadata,
                links=new_links,
            )

    async def save_batch(
        self, session: AsyncSession, aggregate: NewsLinkBatchAggregate
    ) -> BatchSaveResult:
        """
        批量保存链接（事务方法 - 不负责 commit）

        职责边界：
            - ✅ 仓储层：执行数据库插入操作
            - ❌ 仓储层：不调用 session.commit() / session.rollback()
            - ✅ 调用方（Application Service）：管理事务的 commit/rollback

        实现细节：
            - 使用 INSERT IGNORE 保证幂等性（重复 URL 不报错）
            - 返回实际保存数量和跳过的 URL
            - 所有操作在传入的 session 中执行

        Args:
            session: 数据库会话（由 Application Service 创建和管理）
            aggregate: 包含新闻源配置和待保存链接的聚合对象

        Returns:
            BatchSaveResult - 包含实际写入条数和跳过的重复 URL

        Note:
            此方法必须在事务上下文中调用，调用方负责 commit/rollback。
        """
        if not aggregate.links:
            return BatchSaveResult(saved_count=0, skipped_urls=[])

        records = NewsLinkMapper.aggregate_to_insert_records(aggregate)
        saved_count = await self._news_link_dao.bulk_insert_ignore(session, records)
        skipped_urls = [r["url"] for r in records[saved_count:]] if saved_count < len(records) else []

        return BatchSaveResult(saved_count=saved_count, skipped_urls=skipped_urls)

    # ------------------------------------------------------------------
    # 爬取日志保存
    # ------------------------------------------------------------------

    async def save_crawl_log(
        self,
        session: AsyncSession,
        resource_id: str,
        result: CrawlNodeResultEntity,
        started_at: datetime,
        finished_at: datetime,
    ) -> int:
        """
        保存爬取日志（事务方法 - 不负责 commit）

        职责边界：
            - ✅ 仓储层：执行数据库插入操作，返回主键 ID
            - ❌ 仓储层：不调用 session.commit() / session.rollback()
            - ✅ 调用方（Application Service）：管理事务的 commit/rollback

        典型使用场景：
            与 save_batch() 在同一事务中执行，保证数据一致性。
            ```python
            async with session_factory() as session:
                # 保存链接
                await repository.save_batch(session, aggregate)
                # 保存日志
                await repository.save_crawl_log(session, resource_id, result, ...)
                # 统一提交
                await session.commit()
            ```

        Args:
            session: 数据库会话（由 Application Service 创建和管理）
            resource_id: 新闻源唯一标识
            result: 爬取结果（顶层组合节点）
            started_at: 爬取开始时间
            finished_at: 爬取结束时间

        Returns:
            int - 插入记录的主键 ID

        Note:
            此方法必须在事务上下文中调用，调用方负责 commit/rollback。
        """
        record = CrawlLogMapper.result_to_insert_record(
            resource_id=resource_id,
            result=result,
            started_at=started_at,
            finished_at=finished_at,
        )
        log_id = await self._crawl_log_dao.insert(session, record)
        return log_id