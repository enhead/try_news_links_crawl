"""
枚举层实现：遍历固定值列表。

适用场景：
  - 分类维度：["tech", "finance", "sports"]
  - 地区维度：["beijing", "shanghai", "guangzhou"]
"""

from __future__ import annotations

from v1.DDD.domain.http_news_links_crawl.model.entity.layer_factor_entity import LayerFactorEntity
from v1.DDD.domain.http_news_links_crawl.model.entity.layer_node_result_entity import CrawlNodeResultEntity
from v1.DDD.domain.http_news_links_crawl.service.crawl_layer.abstract_layer import AbstractCrawlLayer
from v1.DDD.domain.http_news_links_crawl.service.crawl_layer.factory.layer_factory import (
    CrawlLayerFactory,
    LayerType,
)


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
        children_results: list[CrawlNodeResultEntity] = []

        for value in self.values:
            new_factor = factor.with_param(self.key, value)
            child_result = await self.next_layer.execute(new_factor)
            children_results.append(child_result)

        return CrawlNodeResultEntity.merge_all(children_results)
