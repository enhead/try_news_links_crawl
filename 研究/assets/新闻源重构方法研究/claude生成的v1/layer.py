from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

from news_crawler.crawl_node import CrawlNode
from news_crawler.db_checker import DbChecker
from news_crawler.http_adapter import HttpAdapter
from news_crawler.models import LayerResult, NodeResult
from news_crawler.source_config import SourceConfig


class Layer(ABC):
    """
    Layer 抽象基类。
    每个 Layer 持有下一层引用，自驱动遍历，自己决定是否短路。
    参数通过 accumulated_params 逐层积累向下传递，不跳层。
    """

    def __init__(self, key: str, next_layer: Layer | None = None):
        self.key = key                  # 当前层写入 accumulated_params 的 key
        self.next_layer = next_layer    # 下一层引用，叶子层为 None

    @abstractmethod
    def execute(
        self,
        accumulated_params: dict[str, Any],
        source_config: SourceConfig,
        http_adapter: HttpAdapter,
        db_checker: DbChecker,
        checkpoint: dict[str, Any] | None = None,
    ) -> LayerResult:
        """
        主方法：获取当前层及以下所有新闻链接。
        负责遍历本层的值，调用 next_layer.execute()，汇总子结果。
        checkpoint 为上次中断时最后成功的 accumulated_params，用于断点恢复。
        """
        ...

    def _invoke_next(
        self,
        accumulated_params: dict[str, Any],
        source_config: SourceConfig,
        http_adapter: HttpAdapter,
        db_checker: DbChecker,
        checkpoint: dict[str, Any] | None,
    ) -> LayerResult:
        """调用下一层，或在叶子层直接执行 CrawlNode"""
        if self.next_layer is not None:
            return self.next_layer.execute(
                accumulated_params, source_config, http_adapter, db_checker, checkpoint
            )
        # 没有下一层时，当前层直接执行请求（理论上 SequentialLayer 才是叶子层）
        raise RuntimeError(f"{self.__class__.__name__} 没有 next_layer，无法执行请求")


# ---------------------------------------------------------------------------


class EnumerableLayer(Layer):
    """
    枚举层。值来自固定数组，不依赖父层。
    如：分类列表 ["tech", "finance", "sports"]
    """

    def __init__(self, key: str, values: list[Any], next_layer: Layer | None = None):
        super().__init__(key, next_layer)
        self.values = values

    def execute(
        self,
        accumulated_params: dict[str, Any],
        source_config: SourceConfig,
        http_adapter: HttpAdapter,
        db_checker: DbChecker,
        checkpoint: dict[str, Any] | None = None,
    ) -> LayerResult:
        result = LayerResult()

        # 断点恢复：找到上次中断的值，从此处开始，跳过之前的
        start_from = checkpoint.get(self.key) if checkpoint else None
        skip = start_from is not None

        for value in self.values:
            if skip:
                if value == start_from:
                    skip = False   # 找到断点位置，从这里继续（含本值）
                else:
                    continue       # 跳过断点之前的值

            params = {**accumulated_params, self.key: value}
            child_result = self._invoke_next(
                params, source_config, http_adapter, db_checker, checkpoint
            )
            result.merge(child_result)

        result.dedup_links()
        return result


# ---------------------------------------------------------------------------


class DependentLayer(Layer):
    """
    依赖层。当前层的值取决于父层传递的值（字典映射关系）。
    如：一级分类 "tech" → 二级分类 ["ai", "mobile"]
    """

    def __init__(
        self,
        key: str,
        parent_key: str,
        mapping: dict[Any, list[Any]],
        next_layer: Layer | None = None,
    ):
        super().__init__(key, next_layer)
        self.parent_key = parent_key
        self.mapping = mapping

    def execute(
        self,
        accumulated_params: dict[str, Any],
        source_config: SourceConfig,
        http_adapter: HttpAdapter,
        db_checker: DbChecker,
        checkpoint: dict[str, Any] | None = None,
    ) -> LayerResult:
        result = LayerResult()

        parent_value = accumulated_params.get(self.parent_key)
        values = self.mapping.get(parent_value, [])

        # 断点恢复：同 EnumerableLayer
        start_from = checkpoint.get(self.key) if checkpoint else None
        skip = start_from is not None

        for value in values:
            if skip:
                if value == start_from:
                    skip = False
                else:
                    continue

            params = {**accumulated_params, self.key: value}
            child_result = self._invoke_next(
                params, source_config, http_adapter, db_checker, checkpoint
            )
            result.merge(child_result)

        result.dedup_links()
        return result


# ---------------------------------------------------------------------------

# 短路策略阈值，可按需调整
DEFAULT_PRUNE_EXIST_RATIO = 0.8


class SequentialLayer(Layer):
    """
    顺序层。值从 start 开始递增，无限序列。
    自己负责：执行 CrawlNode、判断 should_prune、断点恢复。
    通常是叶子层（无 next_layer）。
    """

    def __init__(
        self,
        key: str,
        start: int = 1,
        step: int = 1,
        prune_exist_ratio: float = DEFAULT_PRUNE_EXIST_RATIO,
    ):
        super().__init__(key, next_layer=None)
        self.start = start
        self.step = step
        self.prune_exist_ratio = prune_exist_ratio

    def execute(
        self,
        accumulated_params: dict[str, Any],
        source_config: SourceConfig,
        http_adapter: HttpAdapter,
        db_checker: DbChecker,
        checkpoint: dict[str, Any] | None = None,
    ) -> LayerResult:
        result = LayerResult()

        # 断点恢复：从上次成功的页码开始，而不是 start
        resume_page = checkpoint.get(self.key) if checkpoint else None
        current = resume_page if resume_page is not None else self.start

        # 断点恢复时，checkpoint 只对第一个非 Sequential 层的首次迭代有意义
        # Sequential 层拿到 resume_page 后，checkpoint 使命完成，不再向下传
        effective_checkpoint = None if resume_page is not None else checkpoint

        while True:
            params = {**accumulated_params, self.key: current}

            node = CrawlNode(params, source_config, http_adapter, db_checker)
            node_result = node.execute()

            result.node_results.append(node_result)
            result.new_links.extend(node_result.links_new)
            result.total_requests += 1
            result.total_found += len(node_result.links_found)

            if self._should_prune(node_result):
                break

            current += self.step

        result.dedup_links()
        return result

    def _should_prune(self, node_result: NodeResult) -> bool:
        """
        短路判断：
        - 空页 → 停
        - 全部链接已存在于 DB → 停
        - 存在比例超过阈值 → 停
        """
        if node_result.is_empty:
            return True
        if not node_result.links_found:
            return True
        if node_result.exist_ratio >= self.prune_exist_ratio:
            return True
        return False
