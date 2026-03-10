"""
依赖层实现：根据父层参数值查映射表。

适用场景：
  - 二级分类依赖一级分类
  - 地区依赖省份
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from v1.DDD.domain.http_news_links_crawl.model.entity.layer_factor_entity import LayerFactorEntity
from v1.DDD.domain.http_news_links_crawl.model.entity.layer_node_result_entity import CrawlNodeResultEntity
from v1.DDD.domain.http_news_links_crawl.service.single_news_link_crawl.crawl_layer.abstract_layer import AbstractCrawlLayer
from v1.DDD.domain.http_news_links_crawl.service.single_news_link_crawl.crawl_layer.factory.layer_factory import (
    CrawlLayerFactory,
    LayerType,
)


@dataclass
class MappingLayerConfig:
    """MappingLayer 配置类。"""
    parent_key: str
    mapping: dict[str, list[str]]


@CrawlLayerFactory.register(LayerType.MAPPING)
class MappingLayer(AbstractCrawlLayer):
    """
    字典映射层：根据父层参数值查映射表。
    values: {
        "parent_key": "cat1",
        "mapping": {"tech": ["ai", "mobile"], ...}
    }
    """

    def __init__(
        self,
        key: str,
        values: MappingLayerConfig | dict[str, Any],
        next_layer: AbstractCrawlLayer | None = None,
    ) -> None:
        super().__init__(key, values, next_layer)

        if isinstance(values, dict):
            config = MappingLayerConfig(**values)
        else:
            config = values

        self.parent_key: str = config.parent_key
        self.mapping: dict[str, list[str]] = config.mapping

    async def execute(self, factor: LayerFactorEntity) -> CrawlNodeResultEntity:
        """根据父层值查映射，遍历对应的子值列表。"""
        parent_value = factor.params.get(self.parent_key)
        values = self.mapping.get(parent_value, [])

        children_results: list[CrawlNodeResultEntity] = []

        for value in values:
            new_factor = factor.with_param(self.key, value)
            child_result = await self.next_layer.execute(new_factor)
            children_results.append(child_result)

        return CrawlNodeResultEntity.merge_all(children_results)
