"""NewsLink 映射器：ORM Model <-> 字典"""

from v1.DDD.domain.http_news_links_crawl.model.aggregate.news_link_batch_aggregate import NewsLinkBatchAggregate
from ..news_link import NewsLinkModel


class NewsLinkMapper:
    """NewsLinkModel 与字典之间的映射器"""

    @staticmethod
    def to_dict(model: NewsLinkModel) -> dict:
        """
        ORM Model 转字典

        Args:
            model: NewsLinkModel ORM 对象

        Returns:
            字典表示
        """
        return {
            "id": model.id,
            "resource_id": model.resource_id,
            "country": model.country,
            "name": model.name,
            "domain": model.domain,
            "language": model.language,
            "url": model.url,
            "crawl_params": model.crawl_params,
            "category": model.category,
            "is_parse": model.is_parse,
            "is_translated": model.is_translated,
            "success": model.success,
            "created_at": model.created_at,
            "updated_at": model.updated_at,
        }

    @staticmethod
    def to_dict_list(models: list[NewsLinkModel]) -> list[dict]:
        """
        批量转换 ORM Model 列表为字典列表

        Args:
            models: NewsLinkModel 列表

        Returns:
            字典列表
        """
        return [NewsLinkMapper.to_dict(model) for model in models]

    @staticmethod
    def aggregate_to_insert_records(aggregate: NewsLinkBatchAggregate) -> list[dict]:
        """
        将聚合根转换为批量插入的记录列表

        Args:
            aggregate: 新闻链接批次聚合根

        Returns:
            可直接用于数据库插入的字典列表
        """
        metadata = aggregate.metadata
        records = []
        for link in aggregate.links:
            records.append({
                "resource_id": metadata.resource_id,
                "country": metadata.country,
                "name": metadata.name,
                "domain": metadata.domain,
                "language": metadata.language,
                "url": link.url,
                "crawl_params": link.crawl_params,
                "category": link.category,
            })
        return records
