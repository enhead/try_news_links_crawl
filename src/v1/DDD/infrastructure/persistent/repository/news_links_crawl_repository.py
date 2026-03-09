from v1.DDD.domain.http_news_links_crawl.model.aggregate.news_link_batch_aggregate import NewsLinkBatchAggregate
from v1.DDD.domain.http_news_links_crawl.model.entity.news_source_metadata import NewsSourceMetadata
from v1.DDD.domain.http_news_links_crawl.repository.base_news_links_crawl_repository import (
    INewsCrawlRepository,
    BatchSaveResult,
)
from v1.DDD.infrastructure.persistent.dao import NewsLinkDAO, NewsSourceDAO
from v1.DDD.infrastructure.persistent.models.mapper import NewsLinkMapper, NewsSourceMapper


class NewsLinksCrawlRepository(INewsCrawlRepository):
    """新闻链接爬虫仓储实现"""

    def __init__(self, news_link_dao: NewsLinkDAO, news_source_dao: NewsSourceDAO):
        self.news_link_dao = news_link_dao
        self.news_source_dao = news_source_dao

    # ------------------------------------------------------------------
    # 新闻源元数据查询
    # ------------------------------------------------------------------

    async def get_source_by_resource_id(self, resource_id: str) -> NewsSourceMetadata | None:
        """根据 resource_id 查询新闻源元数据"""
        model = await self.news_source_dao.find_by_resource_id(resource_id)
        if model is None:
            return None
        return NewsSourceMapper.to_entity(model)

    async def get_all_active_sources(self) -> list[NewsSourceMetadata]:
        """获取所有可调度的新闻源（status=0）"""
        models = await self.news_source_dao.find_all_by_status(status=0)
        return NewsSourceMapper.to_entity_list(models)

    async def get_all_sources(self) -> list[NewsSourceMetadata]:
        """获取所有新闻源（不过滤状态）"""
        models = await self.news_source_dao.find_all()
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

        urls = [link.url for link in aggregate.links]
        existing_urls = await self.news_link_dao.check_urls_exist(urls)
        new_links = [link for link in aggregate.links if link.url not in existing_urls]

        return NewsLinkBatchAggregate(
            metadata=aggregate.metadata,
            links=new_links,
        )

    async def save_batch(self, aggregate: NewsLinkBatchAggregate) -> BatchSaveResult:
        """批量保存链接"""
        if not aggregate.links:
            return BatchSaveResult(saved_count=0, skipped_urls=[])

        records = NewsLinkMapper.aggregate_to_insert_records(aggregate)
        saved_count = await self.news_link_dao.bulk_insert_ignore(records)
        skipped_urls = [r["url"] for r in records[saved_count:]] if saved_count < len(records) else []

        return BatchSaveResult(saved_count=saved_count, skipped_urls=skipped_urls)