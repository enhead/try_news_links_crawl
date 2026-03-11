"""
枚举层实现：遍历固定值列表。

适用场景：
  - 分类维度：["tech", "finance", "sports"]
  - 地区维度：["beijing", "shanghai", "guangzhou"]
"""

from __future__ import annotations

import logging

from v1.DDD.domain.http_news_links_crawl.model.entity.layer_factor_entity import LayerFactorEntity
from v1.DDD.domain.http_news_links_crawl.model.entity.layer_node_result_entity import CrawlNodeResultEntity
from v1.DDD.domain.http_news_links_crawl.service.single_news_link_crawl.crawl_layer.abstract_layer import AbstractCrawlLayer
from v1.DDD.domain.http_news_links_crawl.service.single_news_link_crawl.crawl_layer.factory.layer_factory import (
    CrawlLayerFactory,
    LayerType,
)

logger = logging.getLogger(__name__)


@CrawlLayerFactory.register(LayerType.ENUMERABLE)
class EnumerableLayer(AbstractCrawlLayer):
    """
    枚举层：遍历固定值列表。
    values: list[str]  e.g. ["tech", "finance"]
    """

    def __init__(
        self,
        key: str,
        values: list[str],
        next_layer: AbstractCrawlLayer | None = None,
    ) -> None:
        super().__init__(key, values, next_layer)
        self.values: list[str] = values

    async def execute(self, factor: LayerFactorEntity) -> CrawlNodeResultEntity:
        """
        遍历所有值，递归驱动下层，汇总结果。
        """
        logger.info(f"开始枚举层遍历: key={self.key}, 总数={len(self.values)}, values={self.values}")

        children_results: list[CrawlNodeResultEntity] = []

        for idx, value in enumerate(self.values, 1):
            logger.debug(f"处理枚举值 [{idx}/{len(self.values)}]: {self.key}={value}")

            new_factor = factor.with_param(self.key, value)
            child_result = await self.next_layer.execute(new_factor)
            children_results.append(child_result)

            logger.debug(
                f"枚举值完成 [{idx}/{len(self.values)}]: {self.key}={value}, "
                f"发现={len(child_result.urls_found)}, 新增={len(child_result.urls_new)}"
            )

        merged = CrawlNodeResultEntity.create_composite(
            layer_type=LayerType.ENUMERABLE,
            children=children_results,
        )
        logger.info(
            f"枚举层完成: key={self.key}, "
            f"总发现={len(merged.urls_found)}, 总新增={len(merged.urls_new)}"
        )
        return merged
