"""新闻源健康检查服务实现"""
import logging
from datetime import datetime
from typing import Any

from v1.DDD.domain.http_news_links_crawl.model.entity.health_check_record_entity import HealthCheckRecordEntity
from v1.DDD.domain.http_news_links_crawl.model.valobj.health_check_status_vo import HealthCheckStatusVO
from v1.DDD.domain.http_news_links_crawl.model.valobj.news_source_status_vo import NewsSourceStatusVO
from v1.DDD.domain.http_news_links_crawl.model.valobj.response_parse_result_status_vo import (
    ResponseParseResultStatusVO,
)
from v1.DDD.domain.http_news_links_crawl.repository.base_news_links_crawl_repository import INewsCrawlRepository
from v1.DDD.domain.http_news_links_crawl.service.config.news_resource.abstract_news_source_config import (
    AbstractNewsSourceConfig,
)
from v1.DDD.domain.http_news_links_crawl.service.single_news_link_crawl.news_source_health_check.base_news_source_health_check_service import (
    INewsSourceHealthCheckService,
)
from v1.DDD.infrastructure.http.httpx_adapter import HttpAdapter, HttpRequestError, HttpStatusError

logger = logging.getLogger(__name__)


class NewsSourceHealthCheckService(INewsSourceHealthCheckService):
    """
    新闻源健康检查服务实现

    职责：
    - 执行单个新闻源的健康检查
    - 根据连续失败次数自动标记异常源
    """

    def __init__(self, http_adapter: HttpAdapter, repository: INewsCrawlRepository):
        self.http_adapter = http_adapter
        self.repository = repository

    async def check_source_health(
        self, source_config: AbstractNewsSourceConfig
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
        logger.info(f"开始健康检查: {source_config.name} ({source_config.source_id})")

        # 1. 构建测试参数
        test_params = self._build_test_params(source_config)
        logger.debug(f"测试参数: {test_params}")

        # 2 & 3. 发送请求并解析
        check_status = HealthCheckStatusVO.SUCCESS
        links_found = 0
        http_status_code = None
        error_message = None

        try:
            # 发送 HTTP 请求
            request = source_config.build_request(test_params)
            response = await self.http_adapter.send(request)

            # 解析响应
            try:
                parse_result = source_config.parse_response(response)

                # 4. 判断解析结果
                if parse_result.status == ResponseParseResultStatusVO.SUCCESS:
                    if len(parse_result.urls) > 0:
                        check_status = HealthCheckStatusVO.SUCCESS
                        links_found = len(parse_result.urls)
                        logger.info(f"健康检查成功: 发现 {links_found} 条链接")
                    else:
                        check_status = HealthCheckStatusVO.EMPTY_RESULT
                        error_message = "响应正常但未发现任何链接"
                        logger.warning(f"健康检查警告: {error_message}")
                else:
                    # 解析错误（站点结构变化、部分失败等）
                    check_status = HealthCheckStatusVO.PARSE_ERROR
                    error_message = parse_result.errors[0] if parse_result.errors else "未知解析错误"
                    logger.error(f"健康检查失败(解析错误): {error_message}")

            except Exception as e:
                check_status = HealthCheckStatusVO.PARSE_ERROR
                error_message = f"解析异常: {str(e)}"
                logger.exception(f"健康检查失败(解析异常): {error_message}")

        except (HttpRequestError, HttpStatusError) as e:
            # HTTP 错误
            check_status = HealthCheckStatusVO.HTTP_ERROR
            if isinstance(e, HttpStatusError):
                http_status_code = e.status_code
                error_message = f"HTTP {e.status_code}: {str(e)}"
            else:
                error_message = f"请求错误: {str(e)}"
            logger.error(f"健康检查失败(HTTP错误): {error_message}")

        except Exception as e:
            # 其他未预期的异常
            check_status = HealthCheckStatusVO.HTTP_ERROR
            error_message = f"未知错误: {str(e)}"
            logger.exception(f"健康检查失败(未知错误): {error_message}")

        # 5. 创建并保存检查记录
        record = HealthCheckRecordEntity(
            resource_id=source_config.source_id,
            check_status=check_status,
            checked_at=datetime.now(),
            links_found=links_found,
            http_status_code=http_status_code,
            error_message=error_message,
        )

        await self.repository.save_health_check_record(record)
        logger.info(f"健康检查记录已保存: {check_status.desc}")

        # 6. 检查是否需要更新源状态（连续失败 3 次）
        await self._update_source_status_if_needed(source_config.source_id)

        return record

    def _build_test_params(self, source_config: AbstractNewsSourceConfig) -> dict[str, Any]:
        """
        构建测试请求参数

        为所有层构建第一个测试值

        Args:
            source_config: 新闻源配置

        Returns:
            测试参数字典
        """
        layer_schema = source_config.layer_schema
        if not layer_schema:
            return {}

        test_params = {}

        # 遍历所有层，为每层构建第一个测试值
        for layer in layer_schema:
            param_name = layer["param_name"]

            if layer["type"] == "enumerable":
                # 枚举类型：取第一个值
                first_value = layer["values"][0]
                test_params[param_name] = first_value

            elif layer["type"] == "sequential":
                # 顺序类型：取起始值
                start_value = layer["start"]
                test_params[param_name] = start_value

        return test_params

    async def _update_source_status_if_needed(self, resource_id: str) -> None:
        """
        检查最近的健康检查记录，如果连续 3 次失败则更新源状态为异常

        Args:
            resource_id: 新闻源标识
        """
        # 查询最近 3 次检查记录
        recent_checks = await self.repository.get_recent_health_checks(
            resource_id=resource_id, limit=3
        )

        # 如果不足 3 次，不做判断
        if len(recent_checks) < 3:
            logger.debug(f"健康检查记录不足 3 次，跳过状态更新")
            return

        # 检查是否连续 3 次都不是 SUCCESS
        all_failed = all(
            check.check_status != HealthCheckStatusVO.SUCCESS for check in recent_checks
        )

        if all_failed:
            logger.warning(
                f"新闻源 {resource_id} 连续 3 次健康检查失败，更新状态为异常"
            )
            await self.repository.update_source_status_by_health(
                resource_id=resource_id, status=NewsSourceStatusVO.PARSE_ERROR
            )
        else:
            logger.debug(f"新闻源 {resource_id} 健康状态正常")
