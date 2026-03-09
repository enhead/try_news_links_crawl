"""NewsSource 映射器：ORM Model <-> 领域对象"""

from v1.DDD.domain.http_news_links_crawl.model.entity.news_source_metadata import NewsSourceMetadata
from v1.DDD.domain.http_news_links_crawl.model.valobj.news_source_status_vo import NewsSourceStatusVO
from v1.DDD.infrastructure.persistent.models import NewsSourceModel


class NewsSourceMapper:
    """NewsSourceModel 与领域对象之间的映射器"""

    @staticmethod
    def to_dict(model: NewsSourceModel) -> dict:
        """
        ORM Model 转字典

        Args:
            model: NewsSourceModel ORM 对象

        Returns:
            字典表示
        """
        return {
            "resource_id": model.resource_id,
            "name": model.name,
            "domain": model.domain,
            "url": model.url,
            "country": model.country,
            "language": model.language,
            "status": model.status,
        }

    @staticmethod
    def to_entity(model: NewsSourceModel) -> NewsSourceMetadata:
        """
        ORM Model 转领域实体

        Args:
            model: NewsSourceModel ORM 对象

        Returns:
            NewsSourceMetadata 领域对象
        """
        return NewsSourceMetadata(
            resource_id=model.resource_id,
            name=model.name,
            domain=model.domain,
            url=model.url,
            country=model.country,
            language=model.language,
            status=NewsSourceStatusVO.from_code(model.status),
        )

    @staticmethod
    def to_entity_list(models: list[NewsSourceModel]) -> list[NewsSourceMetadata]:
        """
        批量转换 ORM Model 列表为领域实体列表

        Args:
            models: NewsSourceModel 列表

        Returns:
            NewsSourceMetadata 列表
        """
        return [NewsSourceMapper.to_entity(model) for model in models]
