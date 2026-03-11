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
)
from v1.DDD.domain.http_news_links_crawl.model.valobj.stop_reason_vo import StopReasonVO
from v1.DDD.domain.http_news_links_crawl.service.single_news_link_crawl.crawl_layer.abstract_layer import AbstractCrawlLayer
from v1.DDD.domain.http_news_links_crawl.service.single_news_link_crawl.crawl_layer.crawl_node.abstract_crawl_node import (
    AbstractCrawlNode,
)
from v1.DDD.domain.http_news_links_crawl.service.single_news_link_crawl.crawl_layer.factory.layer_factory import (
    CrawlLayerFactory,
    LayerType,
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
    max_pages: int | None = None  # 最大页码限制,None 表示无限制


@CrawlLayerFactory.register(LayerType.SEQUENTIAL)
class SequentialLayer(AbstractCrawlLayer):
    """顺序翻页层，叶子层。"""

    def __init__(
        self,
        key: str,
        values: SequentialLayerConfig | dict[str, Any],
        next_layer: AbstractCrawlLayer | None = None,
    ) -> None:
        super().__init__(key, values, next_layer=None)

        if isinstance(values, dict):
            config = SequentialLayerConfig(**values)
        else:
            config = values

        self.start: int = config.start
        self.step: int = config.step
        self.max_consecutive_empty: int = config.max_consecutive_empty
        self.max_consecutive_duplicate: int = config.max_consecutive_duplicate
        self.max_pages: int | None = config.max_pages
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
        logger.info(
            f"开始顺序层翻页: key={self.key}, start={self.start}, step={self.step}, "
            f"max_pages={self.max_pages}, max_empty={self.max_consecutive_empty}, "
            f"max_duplicate={self.max_consecutive_duplicate}"
        )

        current_value = self.start
        all_results: list[CrawlNodeResultEntity] = []
        state = PruneState()
        pages_crawled = 0
        stop_reason = None  # 记录停止原因

        while True:
            # 检查是否达到最大页码限制
            if self.max_pages is not None and pages_crawled >= self.max_pages:
                logger.info(f"达到最大页码限制 {self.max_pages}，终止翻页: {self.key}={current_value}")
                stop_reason = StopReasonVO.PRUNED_BY_DEPTH
                break

            new_factor = factor.with_param(self.key, current_value)
            node = self.node_class(new_factor)
            result = await node.execute()

            all_results.append(result)
            self._update_prune_state(result, state)
            pages_crawled += 1

            logger.debug(
                f"页面完成 [{pages_crawled}]: {self.key}={current_value}, "
                f"发现={len(result.urls_found)}, 新增={len(result.urls_new)}, "
                f"重复率={result.exist_ratio:.2%}, 空页计数={state.consecutive_empty}, "
                f"重复页计数={state.consecutive_duplicate}"
            )

            should_stop, reason = self.should_prune(state)
            if should_stop:
                logger.info(f"剪枝终止: {reason}, 最后页码: {self.key}={current_value}")
                # 根据剪枝原因设置 stop_reason
                if state.consecutive_empty >= self.max_consecutive_empty:
                    stop_reason = StopReasonVO.NATURAL_END  # 空页自然结束
                elif state.consecutive_duplicate >= self.max_consecutive_duplicate:
                    stop_reason = StopReasonVO.PRUNED_BY_RATIO  # 重复率剪枝
                break

            current_value += self.step

        # 如果正常遍历完所有页（没有剪枝），设置为 COMPLETED
        if stop_reason is None:
            stop_reason = StopReasonVO.COMPLETED

        merged = CrawlNodeResultEntity.create_composite(
            layer_type=LayerType.SEQUENTIAL,
            children=all_results,
            stop_reason=stop_reason,
        )
        logger.info(
            f"顺序层完成: key={self.key}, 总页数={pages_crawled}, "
            f"总发现={len(merged.urls_found)}, 总新增={len(merged.urls_new)}"
        )
        return merged
