"""新闻源健康检查服务包"""

from .base_news_source_health_check_service import INewsSourceHealthCheckService
from v1.DDD.domain.http_news_links_crawl.service.single_news_link_crawl.news_source_health_check.impl.news_source_health_check_service import NewsSourceHealthCheckService

__all__ = ["INewsSourceHealthCheckService", "NewsSourceHealthCheckService"]
