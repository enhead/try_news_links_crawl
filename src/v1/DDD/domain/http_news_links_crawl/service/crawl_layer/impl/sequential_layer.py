"""
顺序翻页层实现：从起始值开始递增，支持剪枝提前终止。

适用场景：
  - 分页爬取：page=1,2,3...
  - 时间序列：year=2024,2023,2022...
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from v1.DDD.domain.http_news_links_crawl.model.entity.layer_factor_entity import LayerFactorEntity
from v1.DDD.domain.http_news_links_crawl.model.entity.layer_node_result_entity import (
    CrawlNodeResultEntity,
    DiscoveredNewsLinkUrl,
)
from v1.DDD.domain.http_news_links_crawl.service.crawl_layer.abstract_layer import AbstractCrawlLayer
from v1.DDD.domain.http_news_links_crawl.service.crawl_layer.crawl_node.abstract_crawl_node import (
    AbstractCrawlNode,
)
from v1.DDD.domain.http_news_links_crawl.service.crawl_layer.factory.layer_factory import (
    CrawlLayerFactory,
    LayerTypeConstants,
)

logger = logging.getLogger(__name__)


@dataclass
class PruneState:
    """剪枝状态。"""
    consecutive_empty: int = 0
    consecutive_duplicate: int = 0


@dataclass
class SequentialLayerConfig:
    """SequentialLayer 配置类。"""
    node_class: type[AbstractCrawlNode]
    start: int = 1
    step: int = 1
    max_consecutive_empty: int = 2
    max_consecutive_duplicate: int = 2


@CrawlLayerFactory.register(LayerTypeConstants.SEQUENTIAL)
class SequentialLayer(AbstractCrawlLayer):
    """顺序翻页层，叶子层。"""

    def __init__(
        self,
        key: str,
        values: SequentialLayerConfig | dict[str, Any],
        next_layer: AbstractCrawlLayer | None = None,
    ) -> None:
        super().__init__(key, next_layer=None)

        if isinstance(values, dict):
            config = SequentialLayerConfig(**values)
        else:
            config = values

        self.start: int = config.start
        self.step: int = config.step
        self.max_consecutive_empty: int = config.max_consecutive_empty
        self.max_consecutive_duplicate: int = config.max_consecutive_duplicate
        self.node_class: type[AbstractCrawlNode] = config.node_class

    def _update_prune_state(self, result: CrawlNodeResultEntity, state: PruneState) -> None:
        """更新剪枝状态。"""
        if result.is_empty:
            state.consecutive_empty += 1
            state.consecutive_duplicate = 0
        elif result.exist_ratio >= 1.0:
            state.consecutive_duplicate += 1
            state.consecutive_empty = 0
        else:
            state.consecutive_empty = 0
            state.consecutive_duplicate = 0

    def should_prune(self, state: PruneState) -> tuple[bool, str]:
        """判断是否剪枝，返回(是否剪枝, 剪枝原因)。"""
        if state.consecutive_empty >= self.max_consecutive_empty:
            return True, f"连续{state.consecutive_empty}页为空"
        if state.consecutive_duplicate >= self.max_consecutive_duplicate:
            return True, f"连续{state.consecutive_duplicate}页全部重复"
        return False, ""

    # TODO：待探究：这里其实都还是顺序同步的跑，还没有上并发
    async def execute(self, factor: LayerFactorEntity) -> CrawlNodeResultEntity:
        """顺序翻页，每个节点单独去重，支持剪枝。"""
        current_value = self.start
        all_results: list[CrawlNodeResultEntity] = []
        state = PruneState()

        while True:
            new_factor = factor.with_param(self.key, current_value)
            node = self.node_class(new_factor)
            result = await node.execute()

            all_results.append(result)
            self._update_prune_state(result, state)

            should_stop, reason = self.should_prune(state)
            if should_stop:
                logger.debug(f"{reason}，终止: {self.key}={current_value}")
                break

            current_value += self.step

        return CrawlNodeResultEntity.merge_all(all_results)
