"""NewsSourceHealthCheck 映射器：ORM Model <-> 领域对象"""

from v1.DDD.domain.http_news_links_crawl.model.entity.health_check_record_entity import HealthCheckRecordEntity
from v1.DDD.domain.http_news_links_crawl.model.valobj.health_check_status_vo import HealthCheckStatusVO
from v1.DDD.infrastructure.persistent.models import NewsSourceHealthCheckModel


class NewsSourceHealthCheckMapper:
    """NewsSourceHealthCheckModel 与领域对象之间的映射器"""

    @staticmethod
    def to_entity(model: NewsSourceHealthCheckModel) -> HealthCheckRecordEntity:
        """
        ORM Model 转领域实体

        Args:
            model: NewsSourceHealthCheckModel ORM 对象

        Returns:
            HealthCheckRecordEntity 领域对象
        """
        return HealthCheckRecordEntity(
            id=model.id,
            resource_id=model.resource_id,
            check_status=HealthCheckStatusVO.from_code(model.check_status),
            checked_at=model.checked_at,
            links_found=model.links_found,
            http_status_code=model.http_status_code,
            error_message=model.error_message,
        )

    @staticmethod
    def to_entity_list(
        models: list[NewsSourceHealthCheckModel],
    ) -> list[HealthCheckRecordEntity]:
        """
        批量转换 ORM Model 列表为领域实体列表

        Args:
            models: NewsSourceHealthCheckModel 列表

        Returns:
            HealthCheckRecordEntity 列表
        """
        return [NewsSourceHealthCheckMapper.to_entity(model) for model in models]

    @staticmethod
    def to_insert_dict(entity: HealthCheckRecordEntity) -> dict:
        """
        领域实体转数据库插入字典

        Args:
            entity: HealthCheckRecordEntity 领域对象

        Returns:
            数据库插入字典（不包含 id）
        """
        return {
            "resource_id": entity.resource_id,
            "check_status": entity.check_status.code,
            "checked_at": entity.checked_at,
            "links_found": entity.links_found,
            "http_status_code": entity.http_status_code,
            "error_message": entity.error_message,
        }
