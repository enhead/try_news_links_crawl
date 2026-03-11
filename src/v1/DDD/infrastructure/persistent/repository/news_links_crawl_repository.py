from sqlalchemy.ext.asyncio import AsyncSession

from v1.DDD.domain.http_news_links_crawl.model.aggregate.news_link_batch_aggregate import NewsLinkBatchAggregate
from v1.DDD.domain.http_news_links_crawl.model.entity.health_check_record_entity import HealthCheckRecordEntity
from v1.DDD.domain.http_news_links_crawl.model.entity.news_source_metadata import NewsSourceMetadata
from v1.DDD.domain.http_news_links_crawl.model.valobj.news_source_status_vo import NewsSourceStatusVO
from v1.DDD.domain.http_news_links_crawl.repository.base_news_links_crawl_repository import (
    INewsCrawlRepository,
    BatchSaveResult,
)
from v1.DDD.infrastructure.persistent.dao import NewsLinkDAO, NewsSourceDAO, NewsSourceHealthCheckDAO
from v1.DDD.infrastructure.persistent.models.mapper import (
    NewsLinkMapper,
    NewsSourceMapper,
    NewsSourceHealthCheckMapper,
)


class NewsLinksCrawlRepository(INewsCrawlRepository):
    """
    新闻链接爬虫仓储实现（无状态）

    设计说明：
    - 持有 session_factory（用于只读操作）
    - 持有 DAO 实例（DAO 无状态，可以复用）
    - 所有写操作方法接受 session 参数
    - 保证事务一致性
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
        self._health_check_dao = NewsSourceHealthCheckDAO()

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
        """批量保存链接（事务方法）"""
        if not aggregate.links:
            return BatchSaveResult(saved_count=0, skipped_urls=[])

        records = NewsLinkMapper.aggregate_to_insert_records(aggregate)
        saved_count = await self._news_link_dao.bulk_insert_ignore(session, records)
        skipped_urls = [r["url"] for r in records[saved_count:]] if saved_count < len(records) else []

        return BatchSaveResult(saved_count=saved_count, skipped_urls=skipped_urls)

    # ------------------------------------------------------------------
    # 健康检查
    # ------------------------------------------------------------------

    async def save_health_check_record(
        self, session: AsyncSession, record: HealthCheckRecordEntity
    ) -> None:
        """保存健康检查记录（事务方法）"""
        insert_dict = NewsSourceHealthCheckMapper.to_insert_dict(record)
        await self._health_check_dao.insert(session, insert_dict)

    async def get_recent_health_checks(
        self, session: AsyncSession, resource_id: str, limit: int = 10
    ) -> list[HealthCheckRecordEntity]:
        """获取指定新闻源最近的健康检查记录（事务方法）"""
        models = await self._health_check_dao.find_recent_by_resource_id(
            session, resource_id=resource_id, limit=limit
        )
        return NewsSourceHealthCheckMapper.to_entity_list(models)

    async def update_source_status_by_health(
        self, session: AsyncSession, resource_id: str, status: NewsSourceStatusVO
    ) -> None:
        """根据健康检查结果更新新闻源状态（事务方法）"""
        await self._health_check_dao.update_source_status(
            session, resource_id=resource_id, status=status.code
        )