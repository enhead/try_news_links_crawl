"""
新闻源健康检查服务接口
"""
from abc import ABC, abstractmethod

from v1.DDD.domain.http_news_links_crawl.model.entity.health_check_record_entity import HealthCheckRecordEntity
from v1.DDD.domain.http_news_links_crawl.service.config.news_resource.abstract_news_source_config import AbstractNewsSourceConfig


class INewsSourceHealthCheckService(ABC):
    """
    新闻源健康检查服务接口

    职责：
    - 执行单个新闻源的健康检查
    - 根据连续失败次数自动标记异常源
    """

    @abstractmethod
    async def check_source_health(
        self,
        source_config: AbstractNewsSourceConfig
    ) -> HealthCheckRecordEntity:
        """
        执行单个新闻源的健康检查

        检查流程：
        1. 构建测试请求参数（取第一层第一个枚举值）
        2. 发送 HTTP 请求
        3. 调用 parse_response 解析
        4. 判断检查结果（成功/HTTP错误/解析错误/空结果）
        5. 保存检查记录到数据库
        6. 检查是否需要更新 news_source.status（连续失败 3 次）

        Args:
            source_config: 新闻源配置

        Returns:
            健康检查记录实体
        """
        ...
