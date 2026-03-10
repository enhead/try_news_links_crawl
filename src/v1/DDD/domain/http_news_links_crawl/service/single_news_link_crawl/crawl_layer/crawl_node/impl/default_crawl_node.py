"""
默认爬取节点实现。

职责：
  1. 从 factor 中取出基础设施上下文
  2. 构建请求 → 发送 → 解析 → 可选去重
  3. 组装并返回 CrawlNodeResultEntity
"""

from __future__ import annotations

import logging

from v1.DDD.domain.http_news_links_crawl.model.entity.layer_node_result_entity import (
    CrawlNodeResultEntity,
    DiscoveredNewsLinkUrl,
)
from v1.DDD.infrastructure.http.httpx_adapter import (
    HttpRequestError,
    HttpStatusError,
)
from v1.DDD.domain.http_news_links_crawl.service.single_news_link_crawl.crawl_layer.crawl_node.abstract_crawl_node import (
    AbstractCrawlNode,
)

logger = logging.getLogger(__name__)


class DefaultCrawlNode(AbstractCrawlNode):
    """默认爬取节点实现。"""

    async def fetch(self) -> CrawlNodeResultEntity:
        """仅请求和解析，不做数据库去重。"""
        urls_found = await self._fetch_and_parse()

        logger.debug(
            "爬取节点完成(仅获取): params=%s, found=%d",
            self._factor.params, len(urls_found),
        )

        return CrawlNodeResultEntity(
            urls_found=urls_found,
            urls_new=[],  # 待 Layer 层批量去重
        )

    async def execute(self) -> CrawlNodeResultEntity:
        """完整流程：请求 → 解析 → 去重 → 保存。"""
        urls_found = await self._fetch_and_parse()

        # 批量去重
        if urls_found:
            urls_new = await self._factor.context.news_crawl_repository.check_exists_batch(
                urls_found
            )
        else:
            urls_new = []

        logger.debug(
            "爬取节点完成(含去重): params=%s, found=%d, new=%d",
            self._factor.params, len(urls_found), len(urls_new),
        )

        # 批量保存
        if urls_new:
            from v1.DDD.domain.http_news_links_crawl.model.aggregate.news_link_batch_aggregate import NewsLinkBatchAggregate

            aggregate = NewsLinkBatchAggregate(
                metadata=self._factor.context.source_config.metadata,
                links=urls_new
            )
            save_result = await self._factor.context.news_crawl_repository.save_batch(aggregate)

            logger.debug(
                "批量保存完成: params=%s, saved=%d, skipped=%d",
                self._factor.params, save_result.saved_count, len(save_result.skipped_urls)
            )

        return CrawlNodeResultEntity(
            urls_found=urls_found,
            urls_new=urls_new,
        )

    async def _fetch_and_parse(self) -> list[DiscoveredNewsLinkUrl]:
        """执行请求和解析的公共逻辑。"""
        context = self._factor.context
        params = self._factor.params

        # 构建请求参数
        request_params = context.source_config.build_request(params)

        logger.info(f"发送请求: url={request_params.url}, params={params}")

        # 发送 HTTP 请求
        try:
            response = await context.http_adapter.send(request_params)
            logger.info(f"请求成功: url={request_params.url}, status={response.status_code}")
        except HttpRequestError as e:
            logger.error(
                "爬取节点网络错误: url=%s, params=%s, cause=%s",
                request_params.url, params, e.cause,
            )
            raise
        except HttpStatusError as e:
            logger.error(
                "爬取节点 HTTP 错误: url=%s, status=%d, params=%s",
                e.url, e.status_code, params,
            )
            raise

        # 解析响应
        parse_result = context.source_config.parse_response(response)

        # 提取 category（同一批链接的 category 相同）
        category = context.source_config.extract_category(params)

        urls_found = [
            DiscoveredNewsLinkUrl(
                url=url,
                crawl_params=dict(params),
                category=category
            )
            for url in parse_result.urls
        ]

        logger.debug(
            f"解析完成: url={request_params.url}, 提取链接数={len(urls_found)}, 类别={category}"
        )

        if parse_result.errors:
            logger.warning(
                "解析部分失败: url=%s, params=%s, errors=%s",
                request_params.url, params, parse_result.errors,
            )

        return urls_found
